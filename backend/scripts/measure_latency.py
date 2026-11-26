"""End-to-end response time of POST /api/v1/chat/message over the eval scenarios (AGENTS.md: p95 < 10 s).

Unlike run_eval.py (retrieval latency only), every sample here is the full pipeline the user waits
for: sanitize + PII mask + RAG retrieval + Groq intent classification + Groq answer/extraction.

Modes:
    In-process (default): the FastAPI app runs inside this process via httpx.ASGITransport, so no
    server is needed. The LLM response cache is cleared before every request, so no sample is a
    cache hit. Refuses to run with a mock GROQ_API_KEY (mock answers would make the numbers meaningless).
    Remote (--base-url): sends real HTTP requests to a running server, e.g. the staging deploy.
    The server keeps an in-memory LLM response cache, so restart it before measuring: a second
    pass over the same scenarios is answered from the cache and measures nothing (~100 ms).

The first request also loads the embedding model; it is reported separately as the cold start and
left out of the percentiles. Requests are spaced out (--delay) to stay inside Groq free-tier limits.

Usage (from backend/):
    python scripts/measure_latency.py
    python scripts/measure_latency.py --base-url https://lexora-backend.onrender.com --delay 5
    python scripts/measure_latency.py --base-url http://localhost:8001 --delay 4 --client-retry
"""

import argparse
import asyncio
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

PROJECT_ROOT = backend_root.parent
CHAT_PATH = "/api/v1/chat/message"
TARGET_P95_MS = 10_000
WARMUP_QUERY = "Kira artış oranı en fazla ne kadar olabilir?"
# frontend/src/lib/retry.js AUTO_RETRY_MAX_WAIT_SECONDS
CLIENT_AUTO_RETRY_MAX_WAIT_S = 30


def percentile(values: List[float], pct: float) -> float:
    """Nearest-rank percentile (the same definition for every report row)."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


def load_queries(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [{"id": s["id"], "query": s["query"], "expected_intent": s.get("expected_intent", "")} for s in data["scenarios"]]


def build_client(base_url: Optional[str]) -> httpx.AsyncClient:
    timeout = httpx.Timeout(60.0)
    if base_url:
        return httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    from app.core.config import settings
    from app.services.llm_service import _is_mock_key

    if _is_mock_key(settings.GROQ_API_KEY):
        sys.exit("GROQ_API_KEY is a mock/placeholder key: in-process numbers would measure mock answers. Set a real key.")
    from app.main import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://measure", timeout=timeout)


def clear_llm_cache(in_process: bool) -> None:
    if in_process:
        from app.services import llm_service

        llm_service._response_cache.clear()


async def timed_request(client: httpx.AsyncClient, session_id: str, message: str) -> Dict[str, Any]:
    start = time.perf_counter()
    try:
        response = await client.post(CHAT_PATH, json={"session_id": session_id, "message": message})
        elapsed_ms = (time.perf_counter() - start) * 1000
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        return {
            "status_code": response.status_code,
            "latency_ms": round(elapsed_ms, 1),
            "intent": body.get("intent"),
            "error_code": body.get("error_code"),
            "retry_after_seconds": body.get("retry_after_seconds"),
        }
    except httpx.HTTPError as exc:
        return {
            "status_code": None,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "intent": None,
            "error_code": type(exc).__name__,
        }


async def run(args: argparse.Namespace) -> Dict[str, Any]:
    queries = load_queries(args.scenarios)
    in_process = not args.base_url
    samples: List[Dict[str, Any]] = []

    async with build_client(args.base_url) as client:
        clear_llm_cache(in_process)
        cold = await timed_request(client, "latency-warmup", WARMUP_QUERY)
        print(f"cold start: {cold['latency_ms']:.0f} ms (status {cold['status_code']})")

        for run_no in range(1, args.runs + 1):
            for q in queries:
                await asyncio.sleep(args.delay)
                clear_llm_cache(in_process)
                session_id = f"latency-{run_no}-{q['id']}"
                result = await timed_request(client, session_id, q["query"])
                retry_after = result.get("retry_after_seconds")
                if (
                    args.client_retry
                    and result["error_code"] == "LLM_RATE_LIMITED"
                    and retry_after
                    and retry_after <= CLIENT_AUTO_RETRY_MAX_WAIT_S
                ):
                    # Same as the chat screen (frontend/src/lib/retry.js): wait once, resend, count the whole wait
                    await asyncio.sleep(retry_after)
                    second = await timed_request(client, session_id, q["query"])
                    second["latency_ms"] = round(result["latency_ms"] + retry_after * 1000 + second["latency_ms"], 1)
                    second["client_retried"] = True
                    result = second
                result.update({"id": q["id"], "run": run_no, "expected_intent": q["expected_intent"]})
                samples.append(result)
                print(f"[{run_no}] {q['id']}: {result['latency_ms']:.0f} ms  status={result['status_code']}  intent={result['intent']}")

    ok = [s["latency_ms"] for s in samples if s["status_code"] == 200]
    failed = [s for s in samples if s["status_code"] != 200]
    # Time until the user saw any answer, including a fast 503 "busy, retry in N s"
    answered = [s["latency_ms"] for s in samples if s["status_code"] is not None]
    rate_limited = sum(1 for s in samples if s["error_code"] == "LLM_RATE_LIMITED")
    by_intent: Dict[str, List[float]] = {}
    for s in samples:
        if s["status_code"] == 200 and s["intent"]:
            by_intent.setdefault(s["intent"], []).append(s["latency_ms"])

    p95 = percentile(ok, 95)
    from app.core.config import settings

    return {
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "remote" if args.base_url else "in-process",
        "target": args.base_url or "ASGITransport (local)",
        "model": None if args.base_url else settings.GROQ_MODEL_NAME,
        "embedding_model": None if args.base_url else settings.EMBEDDING_MODEL_NAME,
        "scenarios": len(queries),
        "runs": args.runs,
        "delay_s": args.delay,
        "client_retry": args.client_retry,
        "client_retried": sum(1 for s in samples if s.get("client_retried")),
        "cold_start_ms": cold["latency_ms"],
        "requests": len(samples),
        "succeeded": len(ok),
        "failed": len(failed),
        "failures": [{k: s[k] for k in ("id", "run", "status_code", "error_code")} for s in failed],
        "latency_ms": {
            "min": min(ok) if ok else None,
            "p50": percentile(ok, 50) if ok else None,
            "mean": round(statistics.fmean(ok), 1) if ok else None,
            "p95": p95 if ok else None,
            "max": max(ok) if ok else None,
        },
        "p95_by_intent_ms": {k: percentile(v, 95) for k, v in sorted(by_intent.items())},
        "rate_limited": rate_limited,
        "all_responses_p95_ms": percentile(answered, 95) if answered else None,
        "target_p95_ms": TARGET_P95_MS,
        "passed": bool(ok) and not failed and p95 < TARGET_P95_MS,
        "samples": samples,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default=None, help="Measure a running server instead of the in-process app")
    parser.add_argument(
        "--scenarios", type=Path, default=PROJECT_ROOT / "data" / "eval" / "eval_scenarios.json", help="Eval scenario file"
    )
    parser.add_argument("--runs", type=int, default=1, help="Passes over the scenario set (default: 1)")
    parser.add_argument("--delay", type=float, default=4.0, help="Seconds between requests (Groq free-tier rate limit)")
    parser.add_argument(
        "--client-retry",
        action="store_true",
        help="Behave like the chat screen: after 503 LLM_RATE_LIMITED wait retry_after_seconds once and resend "
        "(latency then includes the wait)",
    )
    parser.add_argument(
        "--out", type=Path, default=PROJECT_ROOT / "reports" / "latency_e2e.json", help="JSON report path"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = asyncio.run(run(args))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lat = report["latency_ms"]
    print()
    print(f"requests: {report['requests']}  succeeded: {report['succeeded']}  failed: {report['failed']}")
    if lat["p95"] is not None:
        print(f"p50: {lat['p50']:.0f} ms  p95: {lat['p95']:.0f} ms  max: {lat['max']:.0f} ms  (target p95 < {TARGET_P95_MS} ms)")
    if report["rate_limited"]:
        print(f"rate limited (503): {report['rate_limited']}  p95 of all responses incl. 503: {report['all_responses_p95_ms']:.0f} ms")
    print(f"result: {'PASS' if report['passed'] else 'FAIL'}  -> {args.out}")
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
