# syntax=docker/dockerfile:1

# ---- builder: install deps into an isolated venv ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- runtime: copy venv + app code only, run as non-root ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY alembic.ini .
COPY app ./app
COPY scripts/docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# STORAGE_ROOT (./storage, relative to this WORKDIR) is where uploads land,
# and compose mounts a named volume over it. Create it owned by the runtime
# user *before* dropping privileges: Docker copies an image directory's
# owner and mode onto a fresh empty volume, so without this the mount point
# is created root-owned and every upload fails with EACCES.
RUN mkdir -p /app/storage && chown app:app /app/storage

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request as u,sys; sys.exit(0 if u.urlopen('http://localhost:8000/api/v1/health').status==200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
