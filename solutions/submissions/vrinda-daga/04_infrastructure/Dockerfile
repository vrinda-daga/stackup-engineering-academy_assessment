# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV DATA_DIR=/app/datasets
ENV OUTPUT_DIR=/app/outputs/results/vrinda-daga/04_infrastructure/docker_etl

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY datasets ./datasets
COPY solutions/submissions/vrinda-daga/02_sql_and_viz/etl_full.py ./etl_starter.py

ENTRYPOINT ["python", "/app/etl_starter.py"]
