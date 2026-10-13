"""
FastAPI REST API Server for Modified Duke Endocarditis Criteria.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, create_model
from duke_endocarditis import FIELDS, calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Modified Duke Endocarditis Criteria API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "modified-duke-endocarditis-criteria", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

# This endpoint returns the criteria classification, not an automated diagnosis.
DukeCriteriaRequest = create_model(
    "DukeCriteriaRequest", __config__=ConfigDict(extra="forbid"),
    **{field: (bool, ...) for field in FIELDS}
)


@app.post("/api/classify")
def classify_criteria(payload: DukeCriteriaRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# Serve the same dependency-free browser classifier when running FastAPI locally.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "web"), html=True), name="web")
