from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from sqlalchemy import Column, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import requests
import os

# ─────────────────────────────────────────────────────────────
# ✅ FastAPI App Setup
# ─────────────────────────────────────────────────────────────
app = FastAPI()

# ─────────────────────────────────────────────────────────────
# ✅ Database Setup
# ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@localhost/assurance_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# ✅ SQLAlchemy Model
# ─────────────────────────────────────────────────────────────
class Baseline(Base):
    __tablename__ = "baselines"
    model_id = Column(String, primary_key=True, index=True)
    thresholds = Column(JSON, nullable=False)
    feature_stats = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# ✅ Dependency
# ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────
# ✅ License Check
# ─────────────────────────────────────────────────────────────
def license_is_active() -> bool:
    try:
        res = requests.get("http://assurance-service:8000/v1/license/status")
        return res.status_code == 200 and res.json().get("status") == "active"
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────
# ✅ Pydantic Schema
# ─────────────────────────────────────────────────────────────
class BaselinePayload(BaseModel):
    model_id: str
    thresholds: Dict[str, Dict[str, float]]
    feature_stats: Optional[Dict[str, Dict[str, float]]] = None

# ─────────────────────────────────────────────────────────────
# ✅ POST: Create New Baseline (License-Gated)
# ─────────────────────────────────────────────────────────────
@app.post("/v1/baselines")
def create_baseline(payload: BaselinePayload, db: Session = Depends(get_db)):
    if not license_is_active():
        raise HTTPException(status_code=403, detail="License inactive")

    existing = db.query(Baseline).filter(Baseline.model_id == payload.model_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Baseline already exists")

    baseline = Baseline(
        model_id=payload.model_id,
        thresholds=payload.thresholds,
        feature_stats=payload.feature_stats
    )
    db.add(baseline)
    db.commit()
    return { "status": "created", "model_id": payload.model_id }

# ─────────────────────────────────────────────────────────────
# ✅ GET: Retrieve Baseline by Model ID
# ─────────────────────────────────────────────────────────────
@app.get("/v1/baselines/{model_id}")
def get_baseline(model_id: str, db: Session = Depends(get_db)):
    baseline = db.query(Baseline).filter(Baseline.model_id == model_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return {
        "model_id": baseline.model_id,
        "thresholds": baseline.thresholds,
        "feature_stats": baseline.feature_stats,
        "created_at": baseline.created_at
    }

# ─────────────────────────────────────────────────────────────
# ✅ PUT: Update Existing Baseline (License-Gated)
# ─────────────────────────────────────────────────────────────
@app.put("/v1/baselines/{model_id}")
def update_baseline(model_id: str, payload: BaselinePayload, db: Session = Depends(get_db)):
    if not license_is_active():
        raise HTTPException(status_code=403, detail="License inactive")

    baseline = db.query(Baseline).filter(Baseline.model_id == model_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    baseline.thresholds = payload.thresholds
    baseline.feature_stats = payload.feature_stats
    db.commit()
    return { "status": "updated", "model_id": model_id }
