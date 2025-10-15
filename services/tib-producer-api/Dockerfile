FROM python:3.11-slim
WORKDIR /app

COPY ingest.py .

RUN pip install fastapi uvicorn kafka-python pydantic

CMD ["uvicorn", "ingest:app", "--host", "0.0.0.0", "--port", "8002"]