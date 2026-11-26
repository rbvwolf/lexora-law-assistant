"""Unit tests for evaluation CLI script and metrics calculations."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.chat import Citation
from scripts import ingest_laws as ingest_laws_script
from scripts.run_eval import (
    DomainSummary,
    calculate_p95,
    evaluate_retrieval_scenario,
    evaluate_llm_judge,
    run_evaluation,
)


def test_calculate_p95():
    """Verify p95 calculation for edge cases and regular distributions."""
    assert calculate_p95([]) == 0.0
    assert calculate_p95([100.0]) == 100.0
    values = list(range(1, 101))  # 1 to 100
    p95 = calculate_p95([float(v) for v in values])
    assert 94.0 <= p95 <= 96.0


def test_domain_summary_properties():
    """Verify hit_rate and mrr property calculations in DomainSummary."""
    empty_summary = DomainSummary()
    assert empty_summary.hit_rate == 0.0
    assert empty_summary.mrr == 0.0

    summary = DomainSummary(total=4, hits=3, all_hits=2, hits_at_1=2, mrr_sum=2.5)
    assert summary.hit_rate == 75.0
    assert summary.mrr == 0.625


def test_evaluate_retrieval_scenario_out_of_scope():
    """Verify that scenarios with no expected articles (e.g. out_of_scope) pass cleanly."""
    scenario = {
        "id": "EVAL-015",
        "domain": "out_of_scope",
        "query": "Ceza davası sorusu",
        "expected_articles": [],
    }
    result = evaluate_retrieval_scenario(scenario)
    assert result.scenario_id == "EVAL-015"
    assert result.hit is True
    assert result.reciprocal_rank == 1.0
    assert result.retrieved_articles == []


def test_evaluate_retrieval_scenario_hit_and_mrr():
    """Verify reciprocal rank and hit detection when expected articles match retrieved citations."""
    scenario = {
        "id": "EVAL-TEST-1",
        "domain": "kira_hukuku",
        "query": "Kira artış oranı",
        "expected_articles": ["TBK-344"],
    }

    mock_citations = [
        Citation(article_id="TBK-343", law_name="TBK", text_snippet="Genel"),
        Citation(article_id="TBK-344", law_name="TBK", text_snippet="Kira artışı"),
        Citation(article_id="TBK-345", law_name="TBK", text_snippet="Dava"),
    ]

    with patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations):
        result = evaluate_retrieval_scenario(scenario, top_k=3)
        assert result.hit is True
        assert result.all_hit is True
        assert result.hit_at_1 is False
        assert result.reciprocal_rank == 0.5  # Rank 2 -> 1/2


def test_evaluate_retrieval_scenario_exception_handling():
    """Verify that unexpected retrieval exceptions are caught and reported without crashing."""
    scenario = {
        "id": "EVAL-ERR",
        "domain": "test",
        "query": "Error query",
        "expected_articles": ["TBK-100"],
    }

    with patch("scripts.run_eval.rag_service.retrieve_articles", side_effect=RuntimeError("ChromaDB down")):
        result = evaluate_retrieval_scenario(scenario, top_k=3)
        assert result.hit is False
        assert result.error == "ChromaDB down"
        assert result.retrieved_articles == []


@pytest.mark.asyncio
async def test_evaluate_llm_judge_mock_key_settings():
    """Verify the judge returns deterministic scores for mock API keys."""
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_mock_key_for_dev_mode"):
        result = await evaluate_llm_judge(
            query="Kira artış oranı nedir?",
            context_text="TBK Madde 344 kira artışı düzenler.",
            answer_text="Türk Borçlar Kanunu Madde 344 uygulanır.",
        )

    assert result["faithfulness"] == 0.95
    assert result["answer_relevancy"] == 0.95
    assert result["citation_accuracy"] is True
    assert "Mock evaluation" in result["reasoning"]


@pytest.mark.asyncio
async def test_evaluate_llm_judge_real_call_valid_json():
    """Verify valid Groq JSON is converted to judge metric fields."""
    judge_json = json.dumps({
        "faithfulness": 0.88,
        "answer_relevancy": 0.91,
        "citation_accuracy": True,
        "reasoning": "Yanıt bağlama dayalı ve soruyla ilgili.",
    })

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"):
        with patch("app.services.llm_service._call_groq", return_value=judge_json):
            result = await evaluate_llm_judge(
                query="Kira artış oranı nedir?",
                context_text="TBK Madde 344 kira artışı düzenler.",
                answer_text="Türk Borçlar Kanunu Madde 344 uygulanır.",
            )

    assert result["faithfulness"] == 0.88
    assert result["answer_relevancy"] == 0.91
    assert result["citation_accuracy"] is True
    assert result["reasoning"] == "Yanıt bağlama dayalı ve soruyla ilgili."


@pytest.mark.asyncio
async def test_evaluate_llm_judge_real_call_fallback():
    """Verify judge failures and malformed JSON return the documented fallback."""
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"):
        with patch("app.services.llm_service._call_groq", return_value="not-json"):
            result = await evaluate_llm_judge(
                query="Soru",
                context_text="Bağlam",
                answer_text="Yanıt",
            )

    assert result["faithfulness"] == 0.0
    assert result["answer_relevancy"] == 0.0
    assert result["citation_accuracy"] is False
    assert result["reasoning"].startswith("Judge error:")


@pytest.mark.asyncio
async def test_evaluate_llm_judge_real_call_exception():
    """Verify Groq exceptions return the judge fallback instead of raising."""
    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"):
        with patch(
            "app.services.llm_service._call_groq",
            side_effect=RuntimeError("Groq timeout"),
        ):
            result = await evaluate_llm_judge(
                query="Soru",
                context_text="Bağlam",
                answer_text="Yanıt",
            )

    assert result["faithfulness"] == 0.0
    assert result["answer_relevancy"] == 0.0
    assert result["citation_accuracy"] is False
    assert result["reasoning"] == "Judge error: Groq timeout"


@pytest.mark.asyncio
async def test_evaluate_llm_judge_rejects_invalid_semantic_values():
    """Verify malformed JSON and invalid judge field values fall back."""
    invalid_responses = [
        '{"faithfulness": 1.2, "answer_relevancy": 0.8, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        '{"faithfulness": 0.8, "answer_relevancy": 0.7, "citation_accuracy": "false", "reasoning": "Geçersiz"}',
        '{"faithfulness": 0.8, "answer_relevancy": 0.7}',
        '{"faithfulness": NaN, "answer_relevancy": 0.8, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        '{"faithfulness": 0.8, "answer_relevancy": Infinity, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        '{"faithfulness": 0.8, "answer_relevancy": -0.1, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        '{"faithfulness": true, "answer_relevancy": 0.8, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        '{"faithfulness": 0.8, "answer_relevancy": false, "citation_accuracy": true, "reasoning": "Geçersiz"}',
        "[]",
        '{"faithfulness": 0.8, "answer_relevancy": 0.7, "citation_accuracy": true, "reasoning": 42}',
    ]

    with patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"):
        for invalid_response in invalid_responses:
            with patch(
                "app.services.llm_service._call_groq",
                new_callable=AsyncMock,
                return_value=invalid_response,
            ):
                result = await evaluate_llm_judge(
                    "Soru",
                    "Bağlam",
                    "Cevap",
                )

            assert result["faithfulness"] == 0.0
            assert result["answer_relevancy"] == 0.0
            assert result["citation_accuracy"] is False
            assert result["reasoning"].startswith("Judge error:")

        with patch(
            "app.services.llm_service._call_groq",
            new_callable=AsyncMock,
            return_value=(
                '```json\n{"faithfulness": 0.9, "answer_relevancy": 0.85, '
                '"citation_accuracy": true, "reasoning": "Geçerli."}\n```'
            ),
        ):
            result = await evaluate_llm_judge("Soru", "Bağlam", "Yanıt")

    assert result["faithfulness"] == 0.9
    assert result["answer_relevancy"] == 0.85
    assert result["citation_accuracy"] is True
    assert result["reasoning"] == "Geçerli."


def test_run_evaluation_with_judge_flag_aggregate_details(tmp_path):
    """Verify eval_judge populates per-scenario and aggregate judge metrics."""
    scenarios_data = {
        "dataset_version": "test-v1",
        "scenarios": [
            {
                "id": "EVAL-001",
                "domain": "kira_hukuku",
                "query": "Kiracı kirayı ödemiyor",
                "expected_intent": "question_answering",
                "expected_articles": ["TBK-315"],
            },
            {
                "id": "EVAL-015",
                "domain": "out_of_scope",
                "query": "Ceza sorusu",
                "expected_articles": [],
            },
        ],
    }
    eval_file = tmp_path / "test_scenarios.json"
    eval_file.write_text(json.dumps(scenarios_data), encoding="utf-8")

    mock_citations = [
        Citation(article_id="TBK-315", law_name="TBK", text_snippet="Temerrüt"),
    ]
    judge_result = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.9,
        "citation_accuracy": True,
        "reasoning": "Bağlama uygun ve ilgili.",
    }

    with patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations):
        with patch(
            "app.services.llm_service.llm_service.process_chat_message",
            new_callable=AsyncMock,
            return_value=("question_answering", "Test answer", {}, [], None),
        ):
            with patch(
                "scripts.run_eval.evaluate_llm_judge",
                new_callable=AsyncMock,
                return_value=judge_result,
            ):
                report = run_evaluation(
                    eval_file_path=eval_file,
                    top_k=5,
                    eval_judge=True,
                    judge_model="test-judge-model",
                    quiet=True,
                )

    assert report.avg_faithfulness == 0.8
    assert report.avg_answer_relevancy == 0.9
    assert report.citation_accuracy_pct == 100.0
    assert report.results[0]["faithfulness"] == 0.8
    assert report.results[0]["answer_relevancy"] == 0.9
    assert report.results[0]["citation_accuracy"] is True
    assert report.results[0]["judge_reasoning"] == "Bağlama uygun ve ilgili."
    assert report.results[1]["faithfulness"] is None


def test_run_evaluation_integration_uses_one_loop_and_routes_judge_by_intent(tmp_path):
    """Exercise intent, chat, and judge through the real service using a fake Groq client."""
    from app.services import llm_service as llm_service_module

    eval_file = tmp_path / "integration_scenarios.json"
    eval_file.write_text(
        json.dumps(
            {
                "scenarios": [
                    {
                        "id": "INTENT-ERROR",
                        "query": "integration intent error",
                        "expected_intent": "question_answering",
                        "expected_articles": [],
                    },
                    {
                        "id": "INTENT-QA",
                        "query": "integration qa success",
                        "expected_intent": "question_answering",
                        "expected_articles": [],
                    },
                    {
                        "id": "INTENT-DOC",
                        "query": "integration document request",
                        "expected_intent": "document_generation",
                        "expected_articles": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    loop_instances = []
    requests = []
    query_call_counts = {}

    async def fake_create(**kwargs):
        loop_instances.append(asyncio.get_running_loop())
        requests.append(kwargs)
        messages = kwargs["messages"]
        system_prompt = messages[0]["content"]
        user_content = messages[-1]["content"]

        if system_prompt == llm_service_module._INTENT_SYSTEM:
            query_call_counts[user_content] = query_call_counts.get(user_content, 0) + 1
            if user_content == "integration intent error" and query_call_counts[user_content] == 1:
                raise RuntimeError("intent classification failed")
            intent = (
                "document_generation"
                if user_content == "integration document request"
                else "question_answering"
            )
            content = json.dumps({"intent": intent})
        elif "LLM-as-a-Judge" in system_prompt:
            content = json.dumps(
                {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.8,
                    "citation_accuracy": True,
                    "reasoning": "Integration judge response.",
                }
            )
        else:
            raise AssertionError(f"Unexpected Groq prompt: {system_prompt[:80]}")

        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_integration_test_key"),
        patch("app.services.llm_service._get_groq_client", return_value=fake_client),
    ):
        report = run_evaluation(
            eval_file_path=eval_file,
            include_llm=True,
            eval_judge=True,
            judge_model="integration-judge-model",
            delay=0.0,
            quiet=True,
        )

    assert loop_instances
    assert all(loop is loop_instances[0] for loop in loop_instances)
    assert report.intent_accuracy == pytest.approx(66.67)
    assert report.results[0]["intent_match"] is False
    assert report.results[0]["predicted_intent"] == "ERROR: intent classification failed"
    assert report.results[1]["intent_match"] is True
    assert report.results[2]["intent_match"] is True

    judge_requests = [
        request
        for request in requests
        if "LLM-as-a-Judge" in request["messages"][0]["content"]
    ]
    assert len(judge_requests) == 2
    assert all(request["model"] == "integration-judge-model" for request in judge_requests)
    assert query_call_counts["integration document request"] == 1


def test_ingest_laws_skips_orphan_pruning_when_expected_file_is_missing(tmp_path):
    """Keep existing collection entries when only part of the law corpus is available."""
    data_dir = tmp_path / "laws"
    data_dir.mkdir()
    (data_dir / ingest_laws_script.EXPECTED_LAW_FILES[0]).write_text(
        json.dumps(
            [
                {
                    "article_id": "TBK-299",
                    "law": "TBK",
                    "article_no": 299,
                    "title": "Kira sözleşmesi",
                    "text": "Kiraya veren bir şeyin kullanılmasını bırakır.",
                    "domain": "kira_hukuku",
                }
            ]
        ),
        encoding="utf-8",
    )

    class FakeCollection:
        def __init__(self):
            self.get_calls = []
            self.deleted_ids = []

        def upsert(self, **kwargs):
            self.upserted_ids = kwargs["ids"]

        def get(self, **kwargs):
            self.get_calls.append(kwargs)
            return {"ids": ["obsolete-id"]}

        def delete(self, ids):
            self.deleted_ids.extend(ids)

        def count(self):
            return 1

    class FakeModel:
        def encode(self, *args, **kwargs):
            return SimpleNamespace(tolist=lambda: [[0.1]])

    collection = FakeCollection()
    client = SimpleNamespace(get_or_create_collection=lambda **kwargs: collection)
    with (
        patch.object(ingest_laws_script.chromadb, "PersistentClient", return_value=client),
        patch.object(ingest_laws_script, "SentenceTransformer", return_value=FakeModel()),
        patch.object(ingest_laws_script, "format_passage", side_effect=lambda text, **kwargs: text),
    ):
        total = ingest_laws_script.ingest_laws(
            data_dir=data_dir,
            persist_dir=tmp_path / "chroma",
            model_name="test-embedding-model",
        )

    assert total == 1
    assert collection.upserted_ids == ["TBK-299"]
    assert collection.get_calls == []
    assert collection.deleted_ids == []


def test_run_evaluation_missing_file_raises():
    """Verify FileNotFoundError when evaluation JSON file does not exist."""
    non_existent = Path("data/eval/does_not_exist.json")
    with pytest.raises(FileNotFoundError):
        run_evaluation(non_existent)


def test_run_evaluation_domain_filter_not_found_raises(tmp_path):
    """Verify ValueError when domain filter matches zero scenarios."""
    dummy_data = {
        "dataset_version": "1.0",
        "scenarios": [
            {"id": "1", "domain": "kira_hukuku", "query": "q", "expected_articles": ["TBK-315"]}
        ],
    }
    dummy_file = tmp_path / "scenarios.json"
    dummy_file.write_text(json.dumps(dummy_data), encoding="utf-8")

    with pytest.raises(ValueError, match="No scenarios found matching domain filter"):
        run_evaluation(dummy_file, domain="non_existent_domain")


def test_run_evaluation_end_to_end_with_json_output(tmp_path):
    """Verify run_evaluation execution and output file generation with mock citations."""
    scenarios_data = {
        "dataset_version": "test-v1",
        "scenarios": [
            {
                "id": "EVAL-001",
                "domain": "kira_hukuku",
                "query": "Kiracı kirayı ödemiyor",
                "expected_articles": ["TBK-315"],
            },
            {
                "id": "EVAL-015",
                "domain": "out_of_scope",
                "query": "Ceza sorusu",
                "expected_articles": [],
            },
        ],
    }
    eval_file = tmp_path / "test_scenarios.json"
    eval_file.write_text(json.dumps(scenarios_data), encoding="utf-8")
    output_file = tmp_path / "reports" / "eval_out.json"

    mock_citations = [
        Citation(article_id="TBK-315", law_name="TBK", text_snippet="Temerrüt"),
    ]

    with patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations):
        report = run_evaluation(
            eval_file_path=eval_file,
            top_k=5,
            output_path=output_file,
            quiet=True,
        )

        assert report.dataset_version == "test-v1"
        assert report.total_scenarios == 2
        assert report.retrieval_applicable_count == 1
        assert report.hit_at_k == 100.0
        assert report.hit_at_1 == 100.0
        assert report.mrr == 1.0
        assert "kira_hukuku" in report.domain_breakdown
        assert output_file.exists()

        saved_data = json.loads(output_file.read_text(encoding="utf-8"))
        assert saved_data["hit_at_k"] == 100.0


@pytest.mark.asyncio
async def test_evaluate_llm_judge_passes_custom_model_name():
    """Verify evaluate_llm_judge forwards model_name to _call_groq."""
    valid_json = (
        '{"faithfulness": 0.9, "answer_relevancy": 0.85, '
        '"citation_accuracy": true, "reasoning": "Uygun."}'
    )
    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"),
        patch(
            "app.services.llm_service._call_groq",
            new_callable=AsyncMock,
            return_value=valid_json,
        ) as mock_call,
    ):
        res = await evaluate_llm_judge(
            "Soru",
            "Bağlam",
            "Cevap",
            model_name="custom-judge-model-70b",
        )
        assert res["faithfulness"] == 0.9
        mock_call.assert_awaited_once()
        _, kwargs = mock_call.call_args
        assert kwargs.get("model_name") == "custom-judge-model-70b"


@pytest.mark.asyncio
async def test_evaluate_llm_judge_default_model_name_is_none():
    """Verify evaluate_llm_judge defaults model_name to None when not specified."""
    valid_json = (
        '{"faithfulness": 0.9, "answer_relevancy": 0.85, '
        '"citation_accuracy": true, "reasoning": "Uygun."}'
    )
    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"),
        patch(
            "app.services.llm_service._call_groq",
            new_callable=AsyncMock,
            return_value=valid_json,
        ) as mock_call,
    ):
        await evaluate_llm_judge("Soru", "Bağlam", "Cevap")
        mock_call.assert_awaited_once()
        _, kwargs = mock_call.call_args
        assert kwargs.get("model_name") is None


def test_run_evaluation_delay_pacing_between_live_calls(tmp_path):
    """Verify run_evaluation sleeps `delay` seconds between consecutive live Groq calls."""
    eval_file = tmp_path / "pacing_scenarios.json"
    eval_file.write_text(
        json.dumps(
            {
                "dataset_version": "test-pacing",
                "scenarios": [
                    {
                        "id": "EVAL-001",
                        "domain": "kira_hukuku",
                        "query": "Kira artış oranı nedir?",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-344"],
                    },
                    {
                        "id": "EVAL-002",
                        "domain": "out_of_scope",
                        "query": "Boşanma davası nasıl açılır?",
                        "expected_intent": "out_of_scope",
                        "expected_articles": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    mock_citations = [
        Citation(article_id="TBK-344", law_name="TBK", text_snippet="TÜFE sınırı."),
    ]
    judge_result = {
        "faithfulness": 0.95,
        "answer_relevancy": 0.90,
        "citation_accuracy": True,
        "reasoning": "Doğru.",
    }
    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_pacing_key"),
        patch("app.core.config.settings.GROQ_MODEL_NAME", "qwen/qwen3.8-27b"),
        patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations),
        patch(
            "scripts.run_eval.evaluate_llm_intent",
            new_callable=AsyncMock,
            side_effect=[(True, "question_answering"), (True, "out_of_scope")],
        ),
        patch(
            "app.services.llm_service.llm_service.process_chat_message",
            new_callable=AsyncMock,
            return_value=("question_answering", "TBK-344 uygulanır.", {}, [], None),
        ),
        patch(
            "scripts.run_eval.evaluate_llm_judge",
            new_callable=AsyncMock,
            return_value=judge_result,
        ) as mock_judge,
        patch("scripts.run_eval.asyncio.sleep", side_effect=fake_sleep),
    ):
        run_evaluation(
            eval_file_path=eval_file,
            include_llm=True,
            eval_judge=True,
            delay=15.0,
            quiet=True,
        )

    # Live calls: intent(1) -> process_chat(1) -> judge(1) -> intent(2) = 4 calls -> 3 sleeps
    assert sleep_calls == [15.0, 15.0, 15.0]
    mock_judge.assert_awaited_once()
    assert mock_judge.call_args.kwargs.get("model_name") == "qwen/qwen3.8-27b"


@pytest.mark.asyncio
async def test_evaluate_llm_judge_recovers_after_rate_limit_error():
    """Verify evaluate_llm_judge retries on HTTP 429 / RateLimitError with 30s cooldown."""
    class RateLimitError(Exception):
        status_code = 429

    valid_json = json.dumps(
        {
            "faithfulness": 0.92,
            "answer_relevancy": 0.94,
            "citation_accuracy": True,
            "reasoning": "429 sonrası kurtarıldı.",
        }
    )
    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"),
        patch(
            "app.services.llm_service._call_groq",
            new_callable=AsyncMock,
            side_effect=[
                RateLimitError("Error code: 429 - Rate limit reached"),
                RateLimitError("Error code: 429 - Rate limit reached"),
                valid_json,
            ],
        ) as mock_call,
        patch("scripts.run_eval.asyncio.sleep", side_effect=fake_sleep),
    ):
        res = await evaluate_llm_judge("Soru", "Bağlam", "Yanıt")

    assert mock_call.await_count == 3
    assert sleep_calls == [30.0, 30.0]
    assert res["faithfulness"] == 0.92
    assert res["citation_accuracy"] is True


def test_run_evaluation_recovers_from_429_in_intent_and_chat(tmp_path):
    """Verify run_evaluation retries 429 errors in intent and chat without failing scenarios."""
    class RateLimitError(Exception):
        status_code = 429

    eval_file = tmp_path / "retry_scenarios.json"
    eval_file.write_text(
        json.dumps(
            {
                "dataset_version": "test-retry",
                "scenarios": [
                    {
                        "id": "EVAL-001",
                        "domain": "kira_hukuku",
                        "query": "Kira artış oranı nedir?",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-344"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    mock_citations = [
        Citation(article_id="TBK-344", law_name="TBK", text_snippet="TÜFE sınırı."),
    ]
    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_retry_key"),
        patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations),
        patch(
            "scripts.run_eval.evaluate_llm_intent",
            new_callable=AsyncMock,
            side_effect=[RateLimitError("429 TPM"), (True, "question_answering")],
        ),
        patch(
            "app.services.llm_service.llm_service.process_chat_message",
            new_callable=AsyncMock,
            side_effect=[
                RateLimitError("429 TPM"),
                ("question_answering", "TBK-344 uygulanır.", {}, [], None),
            ],
        ),
        patch(
            "scripts.run_eval.evaluate_llm_judge",
            new_callable=AsyncMock,
            return_value={
                "faithfulness": 0.9,
                "answer_relevancy": 0.9,
                "citation_accuracy": True,
                "reasoning": "Başarılı.",
            },
        ),
        patch("scripts.run_eval.asyncio.sleep", side_effect=fake_sleep),
    ):
        report = run_evaluation(
            eval_file_path=eval_file,
            include_llm=True,
            eval_judge=True,
            delay=0.0,
            quiet=True,
        )

    assert sleep_calls == [30.0, 30.0]
    assert report.intent_accuracy == 100.0
    assert report.results[0]["intent_match"] is True
    assert report.results[0]["faithfulness"] == 0.9


def test_run_evaluation_md_output_with_llm_and_without_llm(tmp_path):
    """Verify --md-output generates all 4 sections cleanly with populated or None metrics."""
    eval_file = tmp_path / "md_scenarios.json"
    eval_file.write_text(
        json.dumps(
            {
                "dataset_version": "2.0.0-phase2",
                "scenarios": [
                    {
                        "id": "EVAL-001",
                        "domain": "kira_hukuku",
                        "query": "Kiracım kirayı ödemiyor | ne yapmalıyım?",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-315"],
                        "ground_truth_summary": "TBK Madde 315 uyarınca en az 30 gün süre verilmelidir.",
                        "mentor_verified": True,
                    },
                    {
                        "id": "EVAL-027",
                        "domain": "kira_hukuku",
                        "query": "Fahiş kira artışına itiraz ihtarnamesi hazırla.",
                        "expected_intent": "document_generation",
                        "expected_articles": ["TBK-344"],
                        "ground_truth_summary": "Sistem document_generation niyetini seçmelidir.",
                        "mentor_verified": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    mock_citations = [
        Citation(article_id="TBK-315", law_name="TBK", text_snippet="Temerrüt."),
        Citation(article_id="TBK-344", law_name="TBK", text_snippet="Kira artışı."),
    ]

    # 1. Retrieval-only (None LLM/judge metrics -> "N/A")
    md_retrieval_only = tmp_path / "reports" / "eval_retrieval_only.md"
    with patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations):
        run_evaluation(
            eval_file_path=eval_file,
            md_output_path=md_retrieval_only,
            quiet=True,
        )

    assert md_retrieval_only.exists()
    content_no_llm = md_retrieval_only.read_text(encoding="utf-8")
    assert "## 1. Genel Benchmark Özeti" in content_no_llm
    assert "## 2. Alan Bazlı Performans Dağılımı" in content_no_llm
    assert "## 3. 30 Senaryo Detay ve Karşılaştırma Tablosu" in content_no_llm
    assert "## 4. Rapor Ekibi İçin Ana Rapor Düzeltme Rehberi" in content_no_llm
    assert "| **Intent Accuracy** | **N/A** |" in content_no_llm
    assert "| **Avg Faithfulness** | **N/A** |" in content_no_llm
    assert "EVAL-001" in content_no_llm
    assert "EVAL-027" in content_no_llm
    assert "TBK Madde 315 uyarınca en az 30 gün süre verilmelidir." in content_no_llm
    assert "Kiracım kirayı ödemiyor \\| ne yapmalıyım?" in content_no_llm

    # 2. Populated LLM + Judge metrics
    md_with_llm = tmp_path / "reports" / "eval_full.md"
    with (
        patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations),
        patch(
            "scripts.run_eval.evaluate_llm_intent",
            new_callable=AsyncMock,
            side_effect=[(True, "question_answering"), (True, "document_generation")],
        ),
        patch(
            "app.services.llm_service.llm_service.process_chat_message",
            new_callable=AsyncMock,
            return_value=("question_answering", "TBK-315 uygulanır.", {}, [], None),
        ),
        patch(
            "scripts.run_eval.evaluate_llm_judge",
            new_callable=AsyncMock,
            return_value={
                "faithfulness": 0.91,
                "answer_relevancy": 0.87,
                "citation_accuracy": True,
                "reasoning": "Geçerli.",
            },
        ),
    ):
        run_evaluation(
            eval_file_path=eval_file,
            include_llm=True,
            eval_judge=True,
            judge_model="qwen/qwen3.8-27b",
            delay=0.0,
            md_output_path=md_with_llm,
            quiet=True,
        )

    assert md_with_llm.exists()
    content_full = md_with_llm.read_text(encoding="utf-8")
    assert "`qwen/qwen3.8-27b`" in content_full
    assert "| **Intent Accuracy** | **%100.00** |" in content_full
    assert "| **Avg Faithfulness** | **0.910 / 1.000** |" in content_full
    assert "| **Avg Answer Relevancy** | **0.870 / 1.000** |" in content_full
    assert "| **Citation Accuracy** | **%100.0** |" in content_full
    assert "cold-start" in content_full
    assert "all_hit_at_k" in content_full
    assert "All-Hit@5" in content_full
    assert "All-Hit@{report.top_k}" not in content_full
    assert "8.6 saniye" not in content_full
    assert "EVAL-027" in content_full


@pytest.mark.asyncio
async def test_evaluate_llm_judge_recovers_after_connection_error():
    """Verify evaluate_llm_judge retries transient APIConnectionError / ConnectionError."""
    class APIConnectionError(Exception):
        pass

    valid_json = json.dumps(
        {
            "faithfulness": 0.95,
            "answer_relevancy": 0.90,
            "citation_accuracy": True,
            "reasoning": "Bağlantı hatası sonrası kurtarıldı.",
        }
    )
    sleep_calls = []

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)

    with (
        patch("app.core.config.settings.GROQ_API_KEY", "gsk_real_test_key"),
        patch(
            "app.services.llm_service._call_groq",
            new_callable=AsyncMock,
            side_effect=[
                APIConnectionError("Connection error."),
                ConnectionError("Reset by peer"),
                valid_json,
            ],
        ) as mock_call,
        patch("scripts.run_eval.asyncio.sleep", side_effect=fake_sleep),
    ):
        res = await evaluate_llm_judge("Soru", "Bağlam", "Yanıt")

    assert mock_call.await_count == 3
    assert sleep_calls == [30.0, 30.0]
    assert res["faithfulness"] == 0.95
    assert res["citation_accuracy"] is True


def test_run_evaluation_retry_errors_from_preserves_successes_and_retries_only_errors(tmp_path):
    """Verify --retry-errors-from only re-runs ERROR / Judge error scenarios and preserves latencies."""
    eval_file = tmp_path / "scenarios.json"
    eval_file.write_text(
        json.dumps(
            {
                "dataset_version": "2.0.0-phase2",
                "scenarios": [
                    {
                        "id": "EVAL-001",
                        "domain": "kira_hukuku",
                        "query": "Soru 1",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-315"],
                        "ground_truth_summary": "Özet 1",
                        "mentor_verified": True,
                    },
                    {
                        "id": "EVAL-002",
                        "domain": "kira_hukuku",
                        "query": "Soru 2",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-344"],
                        "ground_truth_summary": "Özet 2",
                        "mentor_verified": True,
                    },
                    {
                        "id": "EVAL-003",
                        "domain": "borclar_genel",
                        "query": "Soru 3",
                        "expected_intent": "question_answering",
                        "expected_articles": ["TBK-117"],
                        "ground_truth_summary": "Özet 3",
                        "mentor_verified": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    prev_report = {
        "dataset_version": "2.0.0-phase2",
        "results": [
            {
                "scenario_id": "EVAL-001",
                "domain": "kira_hukuku",
                "query": "Soru 1",
                "expected_articles": ["TBK-315"],
                "retrieved_articles": ["TBK-315"],
                "hit": True,
                "all_hit": True,
                "hit_at_1": True,
                "reciprocal_rank": 1.0,
                "latency_ms": 72.4,
                "intent_match": True,
                "predicted_intent": "question_answering",
                "error": None,
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "citation_accuracy": False,
                "judge_reasoning": "Judge error: Connection error.",
            },
            {
                "scenario_id": "EVAL-002",
                "domain": "kira_hukuku",
                "query": "Soru 2",
                "expected_articles": ["TBK-344"],
                "retrieved_articles": ["TBK-344"],
                "hit": True,
                "all_hit": True,
                "hit_at_1": True,
                "reciprocal_rank": 1.0,
                "latency_ms": 88.0,
                "intent_match": True,
                "predicted_intent": "question_answering",
                "error": None,
                "faithfulness": 1.0,
                "answer_relevancy": 1.0,
                "citation_accuracy": True,
                "judge_reasoning": "Tamamen doğru.",
            },
            {
                "scenario_id": "EVAL-003",
                "domain": "borclar_genel",
                "query": "Soru 3",
                "expected_articles": ["TBK-117"],
                "retrieved_articles": ["TBK-117"],
                "hit": True,
                "all_hit": True,
                "hit_at_1": True,
                "reciprocal_rank": 1.0,
                "latency_ms": 81.0,
                "intent_match": False,
                "predicted_intent": "ERROR: Connection error.",
                "error": None,
                "faithfulness": 1.0,
                "answer_relevancy": 0.8,
                "citation_accuracy": True,
                "judge_reasoning": "Önceki judge geçerli.",
            },
        ],
    }
    prev_file = tmp_path / "prev_report.json"
    prev_file.write_text(json.dumps(prev_report), encoding="utf-8")

    out_json = tmp_path / "updated.json"
    out_md = tmp_path / "updated.md"
    mock_citations = [
        Citation(article_id="TBK-315", law_name="TBK", text_snippet="Temerrüt."),
    ]

    with (
        patch("scripts.run_eval.rag_service.retrieve_articles", return_value=mock_citations),
        patch(
            "scripts.run_eval.evaluate_llm_intent",
            new_callable=AsyncMock,
            return_value=(True, "question_answering"),
        ) as mock_intent,
        patch(
            "app.services.llm_service.llm_service.process_chat_message",
            new_callable=AsyncMock,
            return_value=("question_answering", "TBK-315 uygulanır.", {}, [], None),
        ) as mock_chat,
        patch(
            "scripts.run_eval.evaluate_llm_judge",
            new_callable=AsyncMock,
            return_value={
                "faithfulness": 0.9,
                "answer_relevancy": 0.9,
                "citation_accuracy": True,
                "reasoning": "Yeniden değerlendirildi.",
            },
        ) as mock_judge,
    ):
        report = run_evaluation(
            eval_file_path=eval_file,
            include_llm=True,
            eval_judge=True,
            delay=0.0,
            retry_errors_from=prev_file,
            output_path=out_json,
            md_output_path=out_md,
            quiet=True,
        )

    # Only EVAL-003 needed intent retry; only EVAL-001 needed judge retry
    assert mock_intent.await_count == 1
    assert mock_chat.await_count == 1
    assert mock_judge.await_count == 1

    # Preserved latencies
    assert report.results[0]["latency_ms"] == 72.4
    assert report.results[1]["latency_ms"] == 88.0
    assert report.results[2]["latency_ms"] == 81.0

    # Updated aggregate metrics across all 3 scenarios
    assert report.intent_accuracy == 100.0
    assert report.avg_faithfulness == pytest.approx(0.967, abs=0.001)
    assert report.citation_accuracy_pct == 100.0
    assert out_json.exists()
    assert out_md.exists()
