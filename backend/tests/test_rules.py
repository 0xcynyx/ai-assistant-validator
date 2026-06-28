import json
from pathlib import Path

from app.rules.checker import check_case


def _load_cases():
    cases_path = Path(__file__).resolve().parents[1] / "input" / "cases.json"
    return json.loads(cases_path.read_text(encoding="utf-8"))


def test_check_case_detects_pii_and_missing_required_points():
    case = _load_cases()[0]

    result = check_case(case)

    assert result["pii_request_detected"] is True
    assert result["absolute_guarantee_detected"] is True
    assert result["required_points_coverage_ratio"] < 1.0
    assert "PII_REQUEST" in result["deterministic_flags"]
    assert "ABSOLUTE_GUARANTEE" in result["deterministic_flags"]


def test_check_case_marks_grounding_when_response_mentions_policy_source():
    case = _load_cases()[1]

    result = check_case(case)

    assert result["citation_or_grounding_present"] is True
    assert result["claim_count_estimate"] >= 1
