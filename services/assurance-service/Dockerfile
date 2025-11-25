FROM python:3.10-slim

WORKDIR /app

# ✅ Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# ✅ Install Python dependencies
COPY services/assurance-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy ASGI app and config logic
COPY services/mms_api/app.py /app/mms_api/app.py
COPY services/mms_api/__init__.py /app/mms_api/__init__.py
COPY services/mms_api/export_historian.py /app/mms_api/export_historian.py
COPY services/mms_api/model_config.json /app/mms_api/model_config.json

# ✅ Copy historian logic
COPY services/mms-consumer/historian.py /app/historian.py

# ✅ Copy orchestration layer (for shared db, routes, utils)
COPY services/orchestration /app/orchestration

# ✅ Set PYTHONPATH so all modules are resolvable
ENV PYTHONPATH=/app

# ✅ Launch the ASGI app
CMD ["uvicorn", "mms_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
