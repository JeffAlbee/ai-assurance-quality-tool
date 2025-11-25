from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yourpassword@localhost:5432/assurance_db")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String)
    input_data = Column(String)
    predicted_label = Column(String)
    confidence_score = Column(Float)
    ground_truth = Column(String)
    source = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
print("✅ predictions table created successfully")
