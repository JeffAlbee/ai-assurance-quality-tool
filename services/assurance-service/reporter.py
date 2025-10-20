from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
import time
import os

# ✅ FastAPI app setup
app = FastAPI()
LOG_FILE = "assurance_labels.log"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@localhost/assurance_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ✅ SQLAlchemy model
class Violation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String)
    metric = Column(String)
    value = Column(Float)
    baseline_low = Column(Float)
    baseline_high = Column(Float)
    violation_type = Column(String)
    source = Column(String)
    user = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Pydantic schema
class ViolationPayload(BaseModel):
    model_id: str
    metric: str
    value: float
    baseline_low: float
    baseline_high: float
    violation_type: str
    source: str
    user: str

# ✅ POST: Log assurance label to file
@app.post("/v1/labels")
async def receive_label(request: Request):
    try:
        payload = await request.json()
        payload["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(payload) + "\n")
        return JSONResponse(content={"status": "label logged"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ POST: Log violation to database
@app.post("/v1/violations")
def log_violation(payload: ViolationPayload, db: Session = Depends(get_db)):
    violation = Violation(**payload.dict())
    db.add(violation)
    db.commit()
    return { "status": "logged", "id": violation.id }

# ✅ GET: Retrieve violations by model_id
@app.get("/v1/violations")
def get_violations(model_id: str, db: Session = Depends(get_db)):
    violations = db.query(Violation).filter(Violation.model_id == model_id).order_by(Violation.timestamp.desc()).all()
    return [ {
        "id": v.id,
        "metric": v.metric,
        "value": v.value,
        "baseline_low": v.baseline_low,
        "baseline_high": v.baseline_high,
        "violation_type": v.violation_type,
        "source": v.source,
        "user": v.user,
        "timestamp": v.timestamp
    } for v in violations ]
