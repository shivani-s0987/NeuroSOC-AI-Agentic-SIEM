FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts/docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x docker-entrypoint.sh
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
