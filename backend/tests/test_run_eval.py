"""Unit tests for evaluation CLI script and metrics calculations."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.chat import Citation
from scripts.run_eval import (
    DomainSummary,
    calculate_p95,
    evaluate_retrieval_scenario,
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
