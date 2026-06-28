"""Validation runner."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

OUTPUT = Path("output")
INPUT = Path("input")
RESULTS = []
ERRORS = []

def check(name: str, condition: bool, detail: str = ""):
    RESULTS.append({"check": name, "passed": condition, "detail": detail})
    if not condition:
        ERRORS.append(f"{name}: {detail}")

def load_json(path: Path):
    if not path.exists():
        check(f"exists:{path.name}", False, str(path))
        return None
    check(f"exists:{path.name}", True)
    try:
        data = json.loads(path.read_text())
        check(f"valid_json:{path.name}", True)
        return data
    except Exception as e:
        check(f"valid_json:{path.name}", False, str(e))
        return None

def main():
    cases_raw = load_json(INPUT / "cases.json")
    cases = (cases_raw.get("cases", cases_raw) if isinstance(cases_raw, dict) else cases_raw) or []
    case_ids = {c["case_id"] for c in cases} if cases else set()

    rc = load_json(OUTPUT / "rule_checks.json") or []
    le = load_json(OUTPUT / "llm_evaluations.json") or []
    fs = load_json(OUTPUT / "final_scores.json") or []
    dg = load_json(OUTPUT / "disagreements.json") or []
    vl = load_json(OUTPUT / "validation_log.json")
    mf = load_json(OUTPUT / "manifest.json")

    report_path = OUTPUT / "report.md"
    calls_path = OUTPUT / "llm_calls.jsonl"
    check("exists:report.md", report_path.exists(), str(report_path))
    check("exists:llm_calls.jsonl", calls_path.exists(), str(calls_path))

    eval_ids = {e["case_id"] for e in le} if le else set()
    score_ids = {s["case_id"] for s in fs} if fs else set()
    check("one_llm_eval_per_case", eval_ids == case_ids, f"missing={sorted(case_ids - eval_ids)}")
    check("one_score_per_case", score_ids == case_ids, f"missing={sorted(case_ids - score_ids)}")

    for s in fs:
        check(f"score_range:{s['case_id']}", 0 <= s.get("score", 0) <= 100, str(s.get("score")))
        dims = s.get("dimension_scores", {})
        for key in ["relevance", "faithfulness", "clarity", "context_continuity", "safety_bias"]:
            check(f"dimension_present:{s['case_id']}:{key}", key in dims, str(dims))

    if calls_path.exists():
        lines = [json.loads(line) for line in calls_path.read_text().splitlines() if line.strip()]
        log_ids = {l["case_id"] for l in lines}
        check("llm_logs_cover_cases", log_ids == case_ids or len(lines) >= len(case_ids), f"logged={sorted(log_ids)}")

    if report_path.exists():
        content = report_path.read_text()
        check("report_mentions_summary", "Summary Table" in content)
        check("report_mentions_failure_patterns", "Top Failure Patterns" in content)
        check("report_mentions_llm_value", "Where LLM Judgment Adds Value" in content)

    out = {"timestamp": datetime.now(timezone.utc).isoformat(), "checks": RESULTS, "errors": ERRORS, "passed": len(ERRORS) == 0}
    (OUTPUT / "validation_log.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    sys.exit(0 if not ERRORS else 1)

if __name__ == "__main__":
    main()