"""measure_latency.py helpers (no network, no Groq)."""

import json
import math

import pytest

from scripts.measure_latency import load_queries, percentile


def test_percentile_nearest_rank():
    values = [float(v) for v in range(1, 21)]  # 1..20
    assert percentile(values, 95) == 19.0
    assert percentile(values, 50) == 10.0
    assert percentile(values, 100) == 20.0
    assert percentile([7.0], 95) == 7.0


def test_percentile_ignores_input_order():
    assert percentile([900.0, 100.0, 500.0], 50) == 500.0


def test_percentile_empty_is_nan():
    assert math.isnan(percentile([], 95))


def test_load_queries_reads_eval_scenarios(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(
        json.dumps({"scenarios": [{"id": "EVAL-001", "query": "Soru?", "expected_intent": "question_answering"}]}),
        encoding="utf-8",
    )
    assert load_queries(path) == [{"id": "EVAL-001", "query": "Soru?", "expected_intent": "question_answering"}]


def test_in_process_mode_refuses_mock_key(monkeypatch):
    from app.core.config import settings
    from scripts import measure_latency

    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_mock_key_for_dev_mode")
    with pytest.raises(SystemExit):
        measure_latency.build_client(None)
