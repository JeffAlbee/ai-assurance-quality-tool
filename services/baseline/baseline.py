from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from sqlalchemy import Column, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# ✅ FastAPI app
app = FastAPI()

# ✅ SQLAlchemy setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@localhost/assurance_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ SQLAlchemy model
class Baseline(Base):
    __tablename__ = "baselines"
    model_id = Column(String, primary_key=True, index=True)
    thresholds = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Pydantic schema
class BaselinePayload(BaseModel):
    model_id: str
    thresholds: Dict[str, Dict[str, float]]  # e.g. { "accuracy": { "low": 0.88, "high": 0.95 } }

# ✅ POST endpoint
@app.post("/v1/baselines")
def create_baseline(payload: BaselinePayload, db: Session = Depends(get_db)):
    existing = db.query(Baseline).filter(Baseline.model_id == payload.model_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Baseline already exists")

    baseline = Baseline(model_id=payload.model_id, thresholds=payload.thresholds)
    db.add(baseline)
    db.commit()
    return { "status": "created", "model_id": payload.model_id }

# ✅ GET endpoint
@app.get("/v1/baselines/{model_id}")
def get_baseline(model_id: str, db: Session = Depends(get_db)):
    baseline = db.query(Baseline).filter(Baseline.model_id == model_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return {
        "model_id": baseline.model_id,
        "thresholds": baseline.thresholds,
        "created_at": baseline.created_at
    }