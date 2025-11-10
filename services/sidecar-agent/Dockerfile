# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional but helpful)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy dependency list and install Python packages
COPY services/sidecar-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true


# Copy only the relevant sidecar-agent code
COPY services/sidecar-agent/evaluate_model.py /app/evaluate_model.py
COPY services/mms_api/mms_api /app/mms_api

# Run the Sidecar agent
CMD ["python", "evaluate_model.py"]
