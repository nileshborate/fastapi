# Video 63 - ONE image for the api AND the migrate job - and it knows its commit
ARG BASE=python:3.13-slim

# ---- stage 1: install the dependencies into a virtual environment ----
FROM ${BASE} AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt .
# no .pyc files: smaller image (homework 57)
RUN /opt/venv/bin/pip install --no-compile -r requirements.txt \
 && find /opt/venv -name __pycache__ -prune -exec rm -rf {} +

# ---- stage 2: only what we need to RUN the app ----
FROM ${BASE}
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
USER app
# the commit this image was built from - /health/ready shows it (Video 63)
ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA}
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-m", "app.healthcheck"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
