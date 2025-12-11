# Org Management Service API Dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app

# build-stage system deps for wheel builds
RUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# copy source into builder to allow tests to run here if desired
COPY . /app

FROM python:3.11-slim AS runtime
WORKDIR /app

# minimal runtime deps (keep gcc for some wheels if necessary)
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# copy only the application code and docs into the final image (exclude tests and scripts)
COPY app /app/app
COPY docs /app/docs

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
