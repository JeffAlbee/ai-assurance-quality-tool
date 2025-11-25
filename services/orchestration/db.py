import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# ✅ Database Configuration
# ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@localhost:5432/assurance_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# ✅ Session Generator
# ─────────────────────────────────────────────────────────────
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────
# ✅ Violation Model
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# ✅ Metric Model
# ─────────────────────────────────────────────────────────────
class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String)
    metric = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────────────────────
# ✅ Create Tables
# ─────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)
