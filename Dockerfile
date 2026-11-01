FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 neurosoc \
    && useradd --uid 10001 --gid neurosoc --home-dir /app --shell /usr/sbin/nologin neurosoc

WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --require-hashes --no-cache-dir -r /tmp/requirements.txt || pip install --no-cache-dir -r /tmp/requirements.txt
COPY --chown=neurosoc:neurosoc backend ./backend
COPY --chown=neurosoc:neurosoc alembic ./alembic
COPY --chown=neurosoc:neurosoc alembic.ini pyproject.toml ./
COPY --chown=neurosoc:neurosoc scripts/docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod 0555 ./docker-entrypoint.sh && mkdir -p /app/uploads /app/backups && chown neurosoc:neurosoc /app/uploads /app/backups

USER neurosoc
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
