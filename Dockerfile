# syntax=docker/dockerfile:1
# Wan Gateway Studio — Gradio UI + CLI for Alibaba Cloud AIGC (video / image / speech)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    WAN_DATA_DIR=/app/data

WORKDIR /app

# oss2 depends on crcmod, which ships as a source distribution and needs a C
# toolchain to build.  Install it only for the pip step, then drop it again.
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && pip install --upgrade pip \
 && pip install -r requirements.txt \
 && apt-get purge -y --auto-remove build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY src/ ./src/
COPY main.py cli.py ./

RUN mkdir -p /app/data \
 && groupadd -r appuser && useradd -r -g appuser appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/ > /dev/null || exit 1

# --host 0.0.0.0 is required inside a container; main.py skips the API-key
# check when WAN_DRY_RUN=1 so the image also boots in CI without secrets.
CMD ["sh", "-c", "python main.py --host 0.0.0.0 --port ${PORT}"]
