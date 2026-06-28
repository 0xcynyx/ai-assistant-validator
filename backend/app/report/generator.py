"""Produces report.md and disagreements.json."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List
from collections import Counter

def _status_badge(status: str) -> str:
    return {"pass": "pass", "review": "review", "fail": "fail"}.get(status, status)

def _risk_badge(risk: str) -> str:
    return {"low": "low", "medium": "medium", "high": "high"}.get(risk, risk)

def _det_signal(rule_check: Dict) -> str:
    flags = rule_check.get("deterministic_flags", [])
    if "PII_REQUEST" in flags or "DISALLOWED_ACTION_HINT" in flags:
        return "high"
    if "ABSOLUTE_GUARANTEE" in flags or "MISSING_REQUIRED_POINTS" in flags:
        return "medium"
    return "low"

def generate_report(cases: List[Dict], rule_checks: List[Dict], llm_evals: List[Dict], final_scores: List[Dict], mock_mode: bool = False, run_id: str = "") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rc_m = {r["case_id"]: r for r in rule_checks}
    le_m = {e["case_id"]: e for e in llm_evals}
    fs_m = {s["case_id"]: s for s in final_scores}

    avg = lambda key: round(sum(le_m[c["case_id"]].get(key, 0) for c in cases) / max(len(cases), 1), 2)
    avg_score = round(sum(fs_m[c["case_id"]]["score"] for c in cases) / max(len(cases), 1), 2)
    unsupported = sum(len(le_m[c["case_id"]].get("unsupported_claims", [])) for c in cases)
    total_claims = sum(len(le_m[c["case_id"]].get("factual_claims", [])) for c in cases)
    hallucination_rate = round((unsupported / total_claims), 2) if total_claims else 0

    lines = [
        "# AI Response Evaluation Report",
        "",
        f"**Run ID**: `{run_id}`  ",
        f"**Generated**: {ts}  ",
        f"**Cases**: {len(cases)}  ",
        f"**Mock mode**: {mock_mode}",
        "",
        "## Summary Table",
        "",
        "| Case ID | Score | Status | Risk | Relevance | Faithfulness | Clarity | Context | Safety | Flags |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for case in cases:
        cid = case["case_id"]
        fs = fs_m[cid]
        le = le_m[cid]
        rc = rc_m[cid]
        lines.append(
            f"| `{cid}` | {fs['score']} | {_status_badge(fs['status'])} | {_risk_badge(le['risk_level'])} | {le.get('relevance', 0)} | {le.get('faithfulness', 0)} | {le.get('clarity', 0)} | {le.get('context_continuity', 0)} | {le.get('safety_bias', 0)} | `{', '.join(rc.get('deterministic_flags', [])) or '-'}' |"
        )

    flag_counts = Counter(flag for rc in rule_checks for flag in rc.get("deterministic_flags", []))
    lines += [
        "",
        "## Aggregate Metrics",
        "",
        f"- Average final score: {avg_score}",
        f"- Average relevance: {avg('relevance')}",
        f"- Average faithfulness: {avg('faithfulness')}",
        f"- Average clarity: {avg('clarity')}",
        f"- Average context & continuity: {avg('context_continuity')}",
        f"- Average safety / bias: {avg('safety_bias')}",
        f"- Hallucination rate: {hallucination_rate}",
        "",
        "## Top Failure Patterns",
        "",
    ]
    if flag_counts:
        lines.extend([f"- **{flag}**: {count} case(s)" for flag, count in flag_counts.most_common()])
    else:
        lines.append("- No deterministic failure patterns detected.")

    caught = [c for c in cases if rc_m[c["case_id"]].get("pii_request_detected") or rc_m[c["case_id"]].get("absolute_guarantee_detected")]
    lines += ["", "## Deterministic Checks That Caught Important Issues", ""]
    if caught:
        for c in caught[:2]:
            cid = c["case_id"]
            rc = rc_m[cid]
            lines.append(f"- `{cid}`: deterministic checks caught `{', '.join(rc.get('deterministic_flags', []))}` before any model judgment.")
    else:
        lines.append("- No major deterministic catches in this run.")

    llm_added = [c for c in cases if le_m[c["case_id"]].get("faithfulness", 0) <= 1 or le_m[c["case_id"]].get("clarity", 0) <= 1]
    lines += ["", "## Where LLM Judgment Adds Value", ""]
    if llm_added:
        c = llm_added[0]
        cid = c["case_id"]
        le = le_m[cid]
        lines.append(f"- `{cid}`: the LLM identified nuanced quality issues beyond keyword rules, especially around faithfulness/clarity. Reasoning: {le.get('reasoning', [])}")
    else:
        lines.append("- In this sample run, most issues were caught by deterministic checks. On larger datasets, LLM review should catch nuance and semantic failures.")

    lines += [
        "",
        "## Practical Evaluation Workflow",
        "",
        "1. Build a representative dataset of happy paths, edge cases, and adversarial cases.",
        "2. Run deterministic checks first for cheap, reproducible signals.",
        "3. Run one LLM judge call per case for language understanding and nuanced review.",
        "4. Route low-confidence/high-risk cases to human review.",
        "5. Add regression tests for each newly discovered failure mode.",
        "",
        "## Known Limitations",
        "",
        "- Keyword heuristics can miss paraphrases and implicit violations.",
        "- Faithfulness scoring is still assisted by LLM judgment, not full symbolic verification.",
        "- Mock mode is useful for CI but not a substitute for real evaluator-model calibration.",
        "- Context continuity is limited by the single-case schema; multi-turn conversation support is a next extension.",
    ]
    return "\n".join(lines)

def generate_disagreements(cases: List[Dict], rule_checks: List[Dict], llm_evals: List[Dict]) -> List[Dict]:
    rc_m = {r["case_id"]: r for r in rule_checks}
    le_m = {e["case_id"]: e for e in llm_evals}
    result = []
    for case in cases:
        cid = case["case_id"]
        det_signal = _det_signal(rc_m[cid])
        llm_risk = le_m[cid].get("risk_level", "low")
        if det_signal == "low" and llm_risk in ("medium", "high"):
            result.append({
                "case_id": cid,
                "deterministic_signal": det_signal,
                "llm_risk_level": llm_risk,
                "direction": "det_low_llm_high",
                "likely_cause": "Semantic quality/safety issue detected by LLM beyond regex heuristics.",
            })
        elif det_signal in ("medium", "high") and llm_risk == "low":
            result.append({
                "case_id": cid,
                "deterministic_signal": det_signal,
                "llm_risk_level": llm_risk,
                "direction": "det_high_llm_low",
                "likely_cause": "Regex may have over-triggered on wording without broader harmful meaning.",
            })
    return result