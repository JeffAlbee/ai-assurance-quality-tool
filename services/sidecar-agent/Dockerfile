# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/sidecar-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy the sidecar agent script
COPY services/sidecar-agent/evaluate_model.py .

# Copy model config and orchestration logic
COPY services/mms_api/model_config.json ./mms_api/model_config.json
COPY services/orchestration /app/orchestration

# Set PYTHONPATH so orchestration and mms_api modules are resolvable
ENV PYTHONPATH=/app

# Run the Sidecar agent
CMD ["python", "evaluate_model.py"]
