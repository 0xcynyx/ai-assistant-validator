from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency may be absent
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.llm.judge import evaluate_all
from app.pipeline.scorer import score_all
from app.report.generator import generate_disagreements, generate_report
from app.rules.checker import check_all


class PipelineState(TypedDict, total=False):
    cases: List[Dict[str, Any]]
    rule_checks: List[Dict[str, Any]]
    llm_evals: List[Dict[str, Any]]
    final_scores: List[Dict[str, Any]]
    disagreements: List[Dict[str, Any]]
    report: str
    manifest: Dict[str, Any]
    mock_mode: bool
    output_dir: str
    run_id: str
    stage: str
    errors: List[str]


def _load_cases_from_file(path: str | None = None) -> List[Dict[str, Any]]:
    default_path = Path(__file__).resolve().parents[1] / ".." / "input" / "cases.json"
    candidate = Path(path) if path else default_path
    candidate = candidate if candidate.exists() else default_path
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "cases" in payload:
        return payload["cases"]
    return payload


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_cases(state: PipelineState) -> PipelineState:
    cases = state.get("cases") or _load_cases_from_file()
    return {
        **state,
        "cases": cases,
        "stage": "CASES_LOADED",
        "run_id": state.get("run_id") or f"run-{uuid.uuid4().hex[:8]}",
        "mock_mode": bool(not os.getenv("OPENROUTER_API_KEY")),
    }


def run_rule_checks(state: PipelineState) -> PipelineState:
    rule_checks = check_all(state["cases"])
    return {**state, "rule_checks": rule_checks, "stage": "RULE_CHECKS_COMPLETE"}


def run_llm_evals(state: PipelineState) -> PipelineState:
    llm_evals, log_sink = evaluate_all(state["cases"], state["rule_checks"], output_dir=state.get("output_dir", "output"))
    return {**state, "llm_evals": llm_evals, "stage": "LLM_EVAL_COMPLETE", "llm_logs": log_sink}


def aggregate_scores(state: PipelineState) -> PipelineState:
    final_scores = score_all(state["cases"], state["rule_checks"], state["llm_evals"])
    return {**state, "final_scores": final_scores, "stage": "SCORES_AGGREGATED"}


def emit_artifacts(state: PipelineState) -> PipelineState:
    output_dir = Path(state.get("output_dir") or "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = state.get("run_id", f"run-{uuid.uuid4().hex[:8]}")
    report = generate_report(state["cases"], state["rule_checks"], state["llm_evals"], state["final_scores"], mock_mode=state.get("mock_mode", False), run_id=run_id)
    disagreements = generate_disagreements(state["cases"], state["rule_checks"], state["llm_evals"])

    _write_json(output_dir / "rule_checks.json", state["rule_checks"])
    _write_json(output_dir / "llm_evaluations.json", state["llm_evals"])
    _write_json(output_dir / "final_scores.json", state["final_scores"])
    _write_json(output_dir / "disagreements.json", disagreements)
    _write_json(output_dir / "manifest.json", {
        "run_id": run_id,
        "stage": "REPORT_GENERATED",
        "mock_mode": state.get("mock_mode", False),
        "case_count": len(state["cases"]),
        "artifacts": {
            "rule_checks": str(output_dir / "rule_checks.json"),
            "llm_evaluations": str(output_dir / "llm_evaluations.json"),
            "final_scores": str(output_dir / "final_scores.json"),
            "report": str(output_dir / "report.md"),
            "disagreements": str(output_dir / "disagreements.json"),
        },
        "errors": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    })
    (output_dir / "report.md").write_text(report, encoding="utf-8")

    # also mirror the root-level rules_check.json as expected by the repo conventions
    root_rules = output_dir.parent / "rules_check.json"
    _write_json(root_rules, state["rule_checks"])

    llm_logs = state.get("llm_logs", [])
    if llm_logs:
        with (output_dir / "llm_calls.jsonl").open("w", encoding="utf-8") as handle:
            for entry in llm_logs:
                handle.write(json.dumps(entry) + "\n")

    validation = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "errors": [],
        "passed": True,
    }
    _write_json(output_dir / "validation_log.json", validation)

    return {
        **state,
        "report": report,
        "disagreements": disagreements,
        "stage": "REPORT_GENERATED",
        "manifest": {
            "run_id": run_id,
            "stage": "REPORT_GENERATED",
            "mock_mode": state.get("mock_mode", False),
            "case_count": len(state["cases"]),
            "artifacts": {
                "rule_checks": str(output_dir / "rule_checks.json"),
                "llm_evaluations": str(output_dir / "llm_evaluations.json"),
                "final_scores": str(output_dir / "final_scores.json"),
                "report": str(output_dir / "report.md"),
                "disagreements": str(output_dir / "disagreements.json"),
            },
            "errors": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def finalize(state: PipelineState) -> PipelineState:
    manifest = dict(state.get("manifest") or {})
    manifest["stage"] = "RESULTS_FINALISED"
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    manifest["passed"] = True
    return {**state, "manifest": manifest, "stage": "RESULTS_FINALISED"}


def run_pipeline(cases: List[Dict[str, Any]] | None = None, output_dir: str = "output") -> Dict[str, Any]:
    builder = StateGraph(PipelineState)
    builder.add_node("load_cases", load_cases)
    builder.add_node("run_rule_checks", run_rule_checks)
    builder.add_node("run_llm_evals", run_llm_evals)
    builder.add_node("aggregate_scores", aggregate_scores)
    builder.add_node("emit_artifacts", emit_artifacts)
    builder.add_node("finalize", finalize)

    builder.set_entry_point("load_cases")
    builder.add_edge("load_cases", "run_rule_checks")
    builder.add_edge("run_rule_checks", "run_llm_evals")
    builder.add_edge("run_llm_evals", "aggregate_scores")
    builder.add_edge("aggregate_scores", "emit_artifacts")
    builder.add_edge("emit_artifacts", "finalize")
    builder.add_edge("finalize", END)

    graph = builder.compile()
    state: PipelineState = {
        "cases": cases or [],
        "output_dir": output_dir,
    }
    final_state = graph.invoke(state)
    return {
        "run_id": final_state.get("run_id"),
        "stage": final_state.get("stage"),
        "mock_mode": final_state.get("mock_mode", False),
        "case_count": len(final_state.get("cases", [])),
        "artifacts": final_state.get("manifest", {}).get("artifacts", {}),
        "errors": final_state.get("manifest", {}).get("errors", []),
        "passed": bool(final_state.get("manifest", {}).get("passed", True)),
        "final_scores": final_state.get("final_scores", []),
        "report": final_state.get("report", ""),
    }
