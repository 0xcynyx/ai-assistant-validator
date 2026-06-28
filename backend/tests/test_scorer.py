import json
from pathlib import Path

from app.pipeline.scorer import score_case


def _load_cases():
    cases_path = Path(__file__).resolve().parents[1] / "input" / "cases.json"
    return json.loads(cases_path.read_text(encoding="utf-8"))


def test_score_case_applies_deductions_and_force_fail():
    case = _load_cases()[0]
    rule_check = {
        "deterministic_flags": ["PII_REQUEST", "MISSING_REQUIRED_POINTS"],
        "required_points_coverage_ratio": 0.5,
        "disallowed_action_hints": ["ask for password"],
    }
    llm_eval = {
        "policy_adherence": "fail",
        "customer_helpfulness": "pass",
        "risk_level": "high",
        "relevance": 1,
        "faithfulness": 1,
        "clarity": 2,
        "context_continuity": 2,
        "safety_bias": 1,
        "faithfulness_ratio": 0.4,
        "factual_claims": ["claim"],
        "unsupported_claims": ["claim"],
    }

    result = score_case(case, rule_check, llm_eval)

    assert result["status"] == "fail"
    assert result["score"] <= 100
    assert result["rule_contributions"]["PII_REQUEST"] == -50
    assert result["llm_contributions"]["policy_adherence_fail"] == -20
    assert result["aggregate_metrics"]["unsupported_claim_count"] == 1
