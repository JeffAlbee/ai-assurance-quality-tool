from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from sqlalchemy import Column, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import requests
import os
import logging
import json
import uuid

# ─────────────────────────────────────────────────────────────
# ✅ Logging Setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
EVENT_LOG_PATH = "baseline_events.log"

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
# ✅ SQLAlchemy Models
# ─────────────────────────────────────────────────────────────
class Baseline(Base):
    __tablename__ = "baselines"
    model_id = Column(String, primary_key=True, index=True)
    thresholds = Column(JSON, nullable=False)
    feature_stats = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class BaselineLog(Base):
    __tablename__ = "baseline_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    event = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    thresholds = Column(JSON, nullable=True)
    feature_stats = Column(JSON, nullable=True)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────────────────────
# ✅ Pydantic Schema
# ─────────────────────────────────────────────────────────────
class BaselinePayload(BaseModel):
    model_id: str
    thresholds: Dict[str, Dict[str, float]]
    feature_stats: Optional[Dict[str, Dict[str, float]]] = None

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
    except Exception as e:
        logging.warning(f"[Baseline] License check failed: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# ✅ Event Logger (File + PostgreSQL)
# ─────────────────────────────────────────────────────────────
def log_baseline_event(event_type: str, model_id: str, payload: Optional[BaselinePayload], db: Session):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event_type,
        "model_id": model_id,
        "thresholds": payload.thresholds if payload else None,
        "feature_stats": payload.feature_stats if payload else None
    }

    # Write to file
    try:
        with open(EVENT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logging.error(f"[Baseline] Failed to write event log: {e}")

    # Write to PostgreSQL
    try:
        db_log = BaselineLog(
            event=event_type,
            model_id=model_id,
            thresholds=payload.thresholds if payload else None,
            feature_stats=payload.feature_stats if payload else None
        )
        db.add(db_log)
        db.commit()
    except Exception as e:
        logging.error(f"[Baseline] Failed to insert log into DB: {e}")

# ─────────────────────────────────────────────────────────────
# ✅ Health Check Endpoint
# ─────────────────────────────────────────────────────────────
@app.get("/v1/health")
def health_check():
    return {"status": "healthy", "service": "baseline-service"}

# ─────────────────────────────────────────────────────────────
# ✅ POST: Create New Baseline (License-Gated)
# ─────────────────────────────────────────────────────────────
@app.post("/v1/baselines")
def create_baseline(payload: BaselinePayload, db: Session = Depends(get_db)):
    # 🔒 License check temporarily disabled for local testing
    # 🔒 Undo this comment to reactivate licensing
    # if not license_is_active():
    #     raise HTTPException(status_code=403, detail="License inactive")

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
    logging.info(f"[Baseline] Created baseline for model: {payload.model_id}")
    log_baseline_event("created", payload.model_id, payload, db)
    return {"status": "created", "model_id": payload.model_id}

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
    # 🔒 License check temporarily disabled for local testing
    # 🔒 Undo this comment to reactivate licensing
    # if not license_is_active():
    #     raise HTTPException(status_code=403, detail="License inactive")

    baseline = db.query(Baseline).filter(Baseline.model_id == model_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")

    baseline.thresholds = payload.thresholds
    baseline.feature_stats = payload.feature_stats
    db.commit()
    logging.info(f"[Baseline] Updated baseline for model: {model_id}")
    log_baseline_event("updated", model_id, payload, db)
    return {"status": "updated", "model_id": model_id}

# ─────────────────────────────────────────────────────────────
# ✅ GET: List All Baselines
# ─────────────────────────────────────────────────────────────
@app.get("/v1/baselines")
def list_baselines(db: Session = Depends(get_db)):
    baselines = db.query(Baseline).order_by(Baseline.created_at.desc()).all()
    return [
        {
            "model_id": b.model_id,
            "thresholds": b.thresholds,
            "feature_stats": b.feature_stats,
            "created_at": b.created_at
        }
        for b in baselines
    ]

# ─────────────────────────────────────────────────────────────
# ✅ GET: Retrieve Baseline Logs (Filterable)
# ─────────────────────────────────────────────────────────────
@app.get("/v1/logs")
def get_baseline_logs(
    model_id: Optional[str] = None,
    event: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict]:
    try:
        query = db.query(BaselineLog)
        if model_id:
            query = query.filter(BaselineLog.model_id == model_id)
        if event:
            query = query.filter(BaselineLog.event == event)
        logs = query.order_by(BaselineLog.timestamp.desc()).limit(100).all()
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "event": log.event,
                "model_id": log.model_id,
                "thresholds": log.thresholds,
                "feature_stats": log.feature_stats
            }
            for log in logs
        ]
    except Exception as e:
        logging.error(f"[Baseline] Failed to read logs from DB: {e}")
        raise HTTPException(status_code=500, detail="Could not read baseline logs")
