import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.pipeline.graph import run_pipeline

router = APIRouter()

ROOT = Path(__file__).resolve().parents[2]


def _load_cases_from_payload(payload: Optional[bytes]) -> List[Dict[str, Any]]:
    if not payload:
        return []
    raw = json.loads(payload.decode("utf-8"))
    if isinstance(raw, dict) and "cases" in raw:
        return raw["cases"]
    if isinstance(raw, list):
        return raw
    raise HTTPException(status_code=400, detail="JSON payload must be a list of cases or an object with a cases array")


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/evaluate")
async def evaluate(file: Optional[UploadFile] = File(None)) -> Dict[str, Any]:
    payload = None
    if file is not None:
        payload = await file.read()
    cases = _load_cases_from_payload(payload) if payload else []
    if not cases:
        default_cases_path = ROOT / "input" / "cases.json"
        cases = json.loads(default_cases_path.read_text(encoding="utf-8"))
    result = run_pipeline(cases, output_dir=str(ROOT / "output"))
    return result


@router.get("/report", response_class=PlainTextResponse)
async def report() -> str:
    report_path = ROOT / "output" / "report.md"
    if not report_path.exists():
        return "No report generated yet."
    return report_path.read_text(encoding="utf-8")
