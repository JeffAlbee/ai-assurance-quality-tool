# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional but helpful)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

# Ensure core packages are installed
RUN pip install --no-cache-dir \
    requests \
    kafka-python \
    pydantic

# Copy application code
COPY . .

# Run the Sidecar agent
CMD ["python", "agent.py"]
