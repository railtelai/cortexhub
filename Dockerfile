# Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install common build/system deps (add more if required by your requirements.txt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Copy application code (this will include cortexthub/others/firebaseCred.json
# if you placed it in that path before building)
COPY . /app

# Expose the port your main.py uses
EXPOSE 8001

# Optional healthcheck (uncomment / adjust if you have a health endpoint)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD curl -f http://localhost:8001/ || exit 1

# Run your app using the python entry (which runs uvicorn inside main.py)
CMD ["python", "main.py"]
