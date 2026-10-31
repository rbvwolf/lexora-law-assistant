"""Evaluation CLI for Lexora legal RAG and end-to-end pipeline.

Measures:
- Retrieval metrics: hit@k, all_hit@k, hit@1, MRR (Mean Reciprocal Rank)
- Latency metrics: min, avg, max, p95 retrieval latency
- Optional LLM metrics: intent classification accuracy, parameter extraction match
- Structured JSON reporting and domain-based breakdown.

Usage:
    python backend/scripts/run_eval.py
    python backend/scripts/run_eval.py --top-k 5 --output reports/eval_phase1.json
    python backend/scripts/run_eval.py --domain kira_hukuku
    python backend/scripts/run_eval.py --include-llm
"""

import argparse
import asyncio
import json
import logging
import math
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.schemas.chat import Citation
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ScenarioRetrievalResult:
    scenario_id: str
    domain: str
    query: str
    expected_articles: List[str]
    retrieved_articles: List[str]
    hit: bool
    all_hit: bool
    hit_at_1: bool
    reciprocal_rank: float
    latency_ms: float
    intent_match: Optional[bool] = None
    predicted_intent: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DomainSummary:
    total: int = 0
    hits: int = 0
    all_hits: int = 0
    hits_at_1: int = 0
    mrr_sum: float = 0.0

    @property
    def hit_rate(self) -> float:
        return (self.hits / self.total * 100.0) if self.total > 0 else 0.0

    @property
    def mrr(self) -> float:
        return (self.mrr_sum / self.total) if self.total > 0 else 0.0


@dataclass
class EvalReport:
    timestamp: str
    dataset_version: str
    total_scenarios: int
    evaluated_scenarios: int
    retrieval_applicable_count: int
    top_k: int
    hit_at_k: float
    all_hit_at_k: float
    hit_at_1: float
    mrr: float
    latency_avg_ms: float
    latency_p95_ms: float
    latency_max_ms: float
    domain_breakdown: Dict[str, Dict[str, Any]]
    intent_accuracy: Optional[float] = None
    results: List[Dict[str, Any]] = field(default_factory=list)


def calculate_p95(values: List[float]) -> float:
    """Calculate the 95th percentile of a list of floats."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * 0.95
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[int(f)] * (c - k)
    d1 = sorted_vals[int(c)] * (k - f)
    return d0 + d1


def evaluate_retrieval_scenario(
    scenario: Dict[str, Any],
    top_k: int = 5,
    domain_filter: Optional[str] = None,
) -> ScenarioRetrievalResult:
    """Evaluate a single scenario for statutory retrieval metrics."""
    scenario_id = scenario.get("id", "UNKNOWN")
    domain = scenario.get("domain", "unknown")
    query = scenario.get("query", "")
    expected_articles = scenario.get("expected_articles", [])

    if not expected_articles:
        return ScenarioRetrievalResult(
            scenario_id=scenario_id,
            domain=domain,
            query=query,
            expected_articles=[],
            retrieved_articles=[],
            hit=True,
            all_hit=True,
            hit_at_1=True,
            reciprocal_rank=1.0,
            latency_ms=0.0,
        )

    t0 = time.perf_counter()
    try:
        citations = rag_service.retrieve_articles(query, top_k=top_k, domain_filter=domain_filter)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        retrieved_ids = [c.article_id for c in citations]
        error = None
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        retrieved_ids = []
        error = str(exc)

    hit = any(exp in retrieved_ids for exp in expected_articles)
    all_hit = all(exp in retrieved_ids for exp in expected_articles)
    hit_at_1 = bool(retrieved_ids and retrieved_ids[0] in expected_articles)

    # Reciprocal Rank: 1 / rank of first relevant article
    reciprocal_rank = 0.0
    for rank_idx, art_id in enumerate(retrieved_ids, 1):
        if art_id in expected_articles:
            reciprocal_rank = 1.0 / rank_idx
            break

    return ScenarioRetrievalResult(
        scenario_id=scenario_id,
        domain=domain,
        query=query,
        expected_articles=expected_articles,
        retrieved_articles=retrieved_ids,
        hit=hit,
        all_hit=all_hit,
        hit_at_1=hit_at_1,
        reciprocal_rank=reciprocal_rank,
        latency_ms=latency_ms,
        error=error,
    )


async def evaluate_llm_intent(scenario: Dict[str, Any]) -> Tuple[bool, str]:
    """Evaluate intent classification using llm_service.

    Note: Uses the internal _classify_intent method directly because it returns
    a plain intent string (Literal), which is exactly what the eval harness needs.
    The public process_chat_message entry point runs the full pipeline
    (RAG + answer generation) which is not needed here.
    """
    from app.services.llm_service import llm_service

    query = scenario.get("query", "")
    expected_intent = scenario.get("expected_intent")

    # _classify_intent returns a plain str (Literal), not a Pydantic model.
    predicted_intent: str = await llm_service._classify_intent(query)  # noqa: SLF001
    match = predicted_intent == expected_intent
    return match, predicted_intent


def run_evaluation(
    eval_file_path: Path,
    top_k: int = 5,
    domain: Optional[str] = None,
    include_llm: bool = False,
    output_path: Optional[Path] = None,
    quiet: bool = False,
) -> EvalReport:
    """Run full evaluation suite over scenarios JSON and generate EvalReport."""
    if not eval_file_path.exists():
        raise FileNotFoundError(f"Evaluation dataset file not found: {eval_file_path}")

    with open(eval_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset_version = data.get("dataset_version", "unknown")
    raw_scenarios = data.get("scenarios", [])

    # Filter by domain if specified
    if domain:
        scenarios = [s for s in raw_scenarios if s.get("domain") == domain]
    else:
        scenarios = raw_scenarios

    if not scenarios:
        raise ValueError(f"No scenarios found matching domain filter: '{domain}'")

    results: List[ScenarioRetrievalResult] = []
    latencies: List[float] = []
    domain_map: Dict[str, DomainSummary] = {}

    total_scenarios = len(scenarios)
    retrieval_applicable_count = 0
    total_hits = 0
    total_all_hits = 0
    total_hits_at_1 = 0
    total_mrr_sum = 0.0

    intent_matches = 0
    intent_total = 0

    if not quiet:
        print(f"\n=======================================================")
        print(f" LEXORA RAG & PIPELINE EVALUATION CLI")
        print(f" Dataset: {eval_file_path.name} (v{dataset_version})")
        print(f" Target Scenarios: {total_scenarios} | Top-K: {top_k}")
        if domain:
            print(f" Domain Filter: {domain}")
        print(f"=======================================================\n")

    for sc in scenarios:
        sc_res = evaluate_retrieval_scenario(sc, top_k=top_k)

        # LLM intent evaluation if requested
        if include_llm:
            try:
                matched, pred_intent = asyncio.run(evaluate_llm_intent(sc))
                sc_res.intent_match = matched
                sc_res.predicted_intent = pred_intent
                intent_total += 1
                if matched:
                    intent_matches += 1
            except Exception as e:
                sc_res.predicted_intent = f"ERROR: {e}"
                sc_res.intent_match = False

        results.append(sc_res)

        # Update domain summary
        dom_sum = domain_map.setdefault(sc_res.domain, DomainSummary())

        if sc_res.expected_articles:
            retrieval_applicable_count += 1
            dom_sum.total += 1
            latencies.append(sc_res.latency_ms)

            if sc_res.hit:
                total_hits += 1
                dom_sum.hits += 1
            if sc_res.all_hit:
                total_all_hits += 1
                dom_sum.all_hits += 1
            if sc_res.hit_at_1:
                total_hits_at_1 += 1
                dom_sum.hits_at_1 += 1
            total_mrr_sum += sc_res.reciprocal_rank
            dom_sum.mrr_sum += sc_res.reciprocal_rank

        if not quiet:
            status_tag = "PASS" if sc_res.hit else "FAIL"
            color = "\033[92m" if sc_res.hit else "\033[91m"
            reset = "\033[0m"
            exp_str = ",".join(sc_res.expected_articles) if sc_res.expected_articles else "(none/out_of_scope)"
            ret_str = ",".join(sc_res.retrieved_articles[:3])
            if len(sc_res.retrieved_articles) > 3:
                ret_str += "..."

            intent_info = f" | intent={sc_res.predicted_intent}" if sc_res.predicted_intent else ""
            print(
                f"[{color}{status_tag}{reset}] {sc_res.scenario_id:<8} ({sc_res.domain:<16}) "
                f"exp=[{exp_str}] -> ret=[{ret_str}] "
                f"({sc_res.latency_ms:.1f}ms){intent_info}"
            )

    hit_rate = (total_hits / retrieval_applicable_count * 100.0) if retrieval_applicable_count > 0 else 0.0
    all_hit_rate = (total_all_hits / retrieval_applicable_count * 100.0) if retrieval_applicable_count > 0 else 0.0
    hit_1_rate = (total_hits_at_1 / retrieval_applicable_count * 100.0) if retrieval_applicable_count > 0 else 0.0
    overall_mrr = (total_mrr_sum / retrieval_applicable_count) if retrieval_applicable_count > 0 else 0.0

    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    p95_lat = calculate_p95(latencies)
    max_lat = max(latencies) if latencies else 0.0

    intent_acc = (intent_matches / intent_total * 100.0) if intent_total > 0 else None

    # Format domain breakdown
    domain_dict: Dict[str, Dict[str, Any]] = {}
    for d_name, d_stat in domain_map.items():
        domain_dict[d_name] = {
            "total": d_stat.total,
            "hits": d_stat.hits,
            "hit_rate_pct": round(d_stat.hit_rate, 1),
            "mrr": round(d_stat.mrr, 3),
        }

    report = EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        dataset_version=dataset_version,
        total_scenarios=len(raw_scenarios),
        evaluated_scenarios=total_scenarios,
        retrieval_applicable_count=retrieval_applicable_count,
        top_k=top_k,
        hit_at_k=round(hit_rate, 2),
        all_hit_at_k=round(all_hit_rate, 2),
        hit_at_1=round(hit_1_rate, 2),
        mrr=round(overall_mrr, 3),
        latency_avg_ms=round(avg_lat, 2),
        latency_p95_ms=round(p95_lat, 2),
        latency_max_ms=round(max_lat, 2),
        domain_breakdown=domain_dict,
        intent_accuracy=round(intent_acc, 2) if intent_acc is not None else None,
        results=[asdict(r) for r in results],
    )

    if not quiet:
        print("\n" + "=" * 55)
        print(" SUMMARY METRICS")
        print("=" * 55)
        print(f" Hit@{top_k} (At least 1 article) : {report.hit_at_k}% ({total_hits}/{retrieval_applicable_count})")
        print(f" All-Hit@{top_k} (All articles)  : {report.all_hit_at_k}% ({total_all_hits}/{retrieval_applicable_count})")
        print(f" Hit@1 (First rank accuracy)     : {report.hit_at_1}% ({total_hits_at_1}/{retrieval_applicable_count})")
        print(f" Mean Reciprocal Rank (MRR)      : {report.mrr}")
        print(f" Retrieval Latency (avg / p95)   : {report.latency_avg_ms:.1f}ms / {report.latency_p95_ms:.1f}ms")
        if report.intent_accuracy is not None:
            print(f" Intent Classification Accuracy  : {report.intent_accuracy}%")
        print("\nDomain Breakdown:")
        for dom, stats in domain_dict.items():
            print(f"  - {dom:<18}: {stats['hit_rate_pct']}% hit@{top_k} (n={stats['total']}, MRR={stats['mrr']})")
        print("=" * 55 + "\n")

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        if not quiet:
            print(f"Report saved successfully to: {out_p.resolve()}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Lexora Evaluation CLI")
    parser.add_argument(
        "--eval-file",
        type=str,
        default=str(backend_root.parent / "data" / "eval" / "eval_scenarios.json"),
        help="Path to evaluation scenarios JSON file.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-K articles to retrieve from ChromaDB (default: 5).",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Filter evaluation to a specific domain (e.g., kira_hukuku, tuketici_hukuku, is_hukuku).",
    )
    parser.add_argument(
        "--include-llm",
        action="store_true",
        help="Include LLM intent classification evaluation (requires valid GROQ_API_KEY).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to output evaluation JSON report.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed scenario output and only print final summary.",
    )

    args = parser.parse_args()
    eval_file = Path(args.eval_file)

    try:
        run_evaluation(
            eval_file_path=eval_file,
            top_k=args.top_k,
            domain=args.domain,
            include_llm=args.include_llm,
            output_path=Path(args.output) if args.output else None,
            quiet=args.quiet,
        )
    except Exception as exc:
        print(f"Error during evaluation: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
