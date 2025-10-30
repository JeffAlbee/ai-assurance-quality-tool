FROM python:3.10-slim

WORKDIR /app

COPY assurance-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mms_api/ ./mms_api/

# 👇 Add this line to fix import resolution
ENV PYTHONPATH=/app

CMD ["uvicorn", "mms_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
