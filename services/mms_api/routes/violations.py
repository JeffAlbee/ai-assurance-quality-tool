from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from mms_api.db import get_db, Violation # move models to a shared db.py

router = APIRouter()

class ViolationPayload(BaseModel):
    model_id: str
    metric: str
    value: float
    baseline_low: float
    baseline_high: float
    violation_type: str
    source: str
    user: str

@router.post("/")
def log_violation(payload: ViolationPayload, db: Session = Depends(get_db)):
    violation = Violation(**payload.dict())
    db.add(violation)
    db.commit()
    return { "status": "logged", "id": violation.id }

@router.get("/")
def get_violations(model_id: str, db: Session = Depends(get_db)):
    violations = db.query(Violation).filter(Violation.model_id == model_id).order_by(Violation.timestamp.desc()).all()
    return [
        {
            "id": v.id,
            "metric": v.metric,
            "value": v.value,
            "baseline_low": v.baseline_low,
            "baseline_high": v.baseline_high,
            "violation_type": v.violation_type,
            "source": v.source,
            "user": v.user,
            "timestamp": v.timestamp
        }
        for v in violations
    ]
@router.get("/debug")
def debug_violation():
    return {"status": "violations router is active"}
