FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY assurance-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy the ASGI app
COPY mms_api/mms_api /app/mms_api

# ✅ Copy historian.py directly into /app
COPY mms-consumer/historian.py /app/historian.py

# ✅ Ensure Python can resolve mms_api and historian
ENV PYTHONPATH=/app

# ✅ Launch the ASGI app
CMD ["uvicorn", "mms_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
