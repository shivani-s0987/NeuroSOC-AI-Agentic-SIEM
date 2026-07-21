# NeuroSOC

NeuroSOC is an AI-assisted Security Operations Center (SOC) and SIEM platform designed for authorized blue-team workflows, education, and research.

## Features

- Log ingestion for common formats including JSON, CSV, syslog, Windows, Apache, and Nginx-style content
- Event normalization and storage in SQLite
- Full-text search and saved searches
- Detection execution and rule management
- Alert workflow and case management
- AI-assisted investigation summaries and assistant prompts
- Modern React dashboard and REST API

## Quick start

### Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### CLI

```bash
python -m app.cli --help
```
