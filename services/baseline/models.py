from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Baseline(Base):
    __tablename__ = "baselines"

    model_id = Column(String, primary_key=True, index=True)
    thresholds = Column(JSON, nullable=False)  # e.g. { "accuracy": { "low": 0.88, "high": 0.95 }, ... }
    created_at = Column(DateTime, default=datetime.utcnow)

