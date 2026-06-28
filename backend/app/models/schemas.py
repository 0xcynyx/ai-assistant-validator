"""Pydantic models / JSON schemas for the evaluation pipeline."""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PolicyContext(BaseModel):
    allowed_actions: List[str] = []
    disallowed_actions: List[str] = []
    required_points: List[str] = []

class Case(BaseModel):
    case_id: str
    user_message: str
    assistant_response: str
    policy_context: PolicyContext = Field(default_factory=PolicyContext)

class CasesFile(BaseModel):
    cases: List[Case]

class LengthInfo(BaseModel):
    char_count: int
    flag: str

class RequiredPointDetail(BaseModel):
    point: str
    covered: bool
    matched: List[str]
    keywords: List[str]

class RuleCheckResult(BaseModel):
    case_id: str
    pii_request_detected: bool
    pii_match_text: Optional[str]
    absolute_guarantee_detected: bool
    guarantee_match_text: Optional[str]
    required_points_coverage_ratio: float
    required_points_detail: List[RequiredPointDetail]
    disallowed_action_hints: List[str]
    response_length: LengthInfo
    prompt_injection_detected: bool
    injection_match_text: Optional[str]
    citation_or_grounding_present: bool = False
    claim_count_estimate: int = 0
    deterministic_flags: List[str]

class Verdict(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LLMEvalResult(BaseModel):
    case_id: str
    policy_adherence: Verdict
    customer_helpfulness: Verdict
    risk_level: RiskLevel
    reasoning: List[str]
    policy_violations: List[str]
    recommended_fix: str
    relevance: int = Field(ge=0, le=3)
    faithfulness: int = Field(ge=0, le=3)
    clarity: int = Field(ge=0, le=3)
    context_continuity: int = Field(ge=0, le=3)
    safety_bias: int = Field(ge=0, le=3)
    factual_claims: List[str] = []
    supported_claims: List[str] = []
    unsupported_claims: List[str] = []
    faithfulness_ratio: float = Field(ge=0, le=1, default=0)
    mock: bool = False

class FinalStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"

class FinalScore(BaseModel):
    case_id: str
    score: int = Field(ge=0, le=100)
    status: FinalStatus
    explanation: str
    rule_contributions: Dict[str, Any]
    llm_contributions: Dict[str, Any]
    dimension_scores: Dict[str, int] = {}
    aggregate_metrics: Dict[str, Any] = {}

class LLMCallLog(BaseModel):
    stage: str
    case_id: str
    timestamp: str
    provider: str
    model: str
    prompt_hash: str
    input_artifacts: List[str]
    output_artifact: str

class Disagreement(BaseModel):
    case_id: str
    deterministic_signal: str
    llm_risk_level: str
    direction: str
    likely_cause: str

class Stage(str, Enum):
    INIT = "INIT"
    CASES_LOADED = "CASES_LOADED"
    RULE_CHECKS_COMPLETE = "RULE_CHECKS_COMPLETE"
    LLM_EVAL_COMPLETE = "LLM_EVAL_COMPLETE"
    SCORES_AGGREGATED = "SCORES_AGGREGATED"
    REPORT_GENERATED = "REPORT_GENERATED"
    VALIDATION_COMPLETE = "VALIDATION_COMPLETE"
    RESULTS_FINALISED = "RESULTS_FINALISED"

STAGE_ORDER = list(Stage)

class PipelineManifest(BaseModel):
    run_id: str
    stage: Stage
    mock_mode: bool = False
    case_count: int = 0
    artifacts: Dict[str, str] = {}
    errors: List[str] = []
    started_at: str = ""
    finished_at: str = ""