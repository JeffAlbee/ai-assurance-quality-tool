import os
import json
import logging
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from redis_utils import get_old_redis_entries

# ─────────────────────────────────────────────────────────────
# ✅ Database Setup
# ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@postgres:5432/your_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─────────────────────────────────────────────────────────────
# ✅ ORM Model: ArchivedViolation
# ─────────────────────────────────────────────────────────────
class ArchivedViolation(Base):
    __tablename__ = "archived_violations"

    id = Column(String, primary_key=True)
    model_name = Column(String)
    timestamp = Column(DateTime)
    metric = Column(String)
    value = Column(Float)

# ─────────────────────────────────────────────────────────────
# ✅ Insert Function
# ─────────────────────────────────────────────────────────────
def insert_archived_violation(db, model_name, timestamp, violation):
    db_violation = ArchivedViolation(
        id=violation.get("id"),  # optional: UUID or hash
        model_name=model_name,
        timestamp=timestamp,
        metric=violation["metric"],
        value=violation["value"],
    )
    db.add(db_violation)

# ─────────────────────────────────────────────────────────────
# ✅ Archive Redis → PostgreSQL (30+ days)
# ─────────────────────────────────────────────────────────────
def archive_old_violations(model_id: str, cutoff_days: int = 30) -> int:
    """
    Archives Redis entries older than `cutoff_days` for the given model_id
    into PostgreSQL. Returns the number of entries archived.
    """
    session = SessionLocal()
    archived = 0

    try:
        old_entries = get_old_redis_entries(model_id, cutoff_days)
        for key, ts, entry in old_entries:
            for v in entry.get("violations", []):
                insert_archived_violation(session, model_id, ts, v)
            archived += 1

        session.commit()
        logging.info(f"🗃️ Archived {archived} entries for {model_id} to PostgreSQL")
    except Exception as e:
        logging.error(f"❌ Archival failed for {model_id}: {e}")
    finally:
        session.close()

    return archived

def init_db():
    Base.metadata.create_all(bind=engine)
