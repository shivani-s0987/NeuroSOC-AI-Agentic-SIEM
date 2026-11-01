<div align="center">

# 🧠 NeuroSOC

### AI-Assisted Security Operations Center (SOC) & Next-Generation SIEM

*An intelligent, AI-powered Security Information and Event Management (SIEM) platform built for **Security Analysts, Blue Teams, Threat Hunters, and Cybersecurity Research**.*

<p align="center">
<img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black"/>
<img src="https://img.shields.io/badge/SQLite-Local_DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
<img src="https://img.shields.io/badge/AI-Assisted-Analysis-8A2BE2?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-success?style=for-the-badge"/>
</p>

**Analyze • Detect • Investigate • Correlate • Respond**

## Threat intelligence and MITRE ATT&CK

NeuroSOC includes normalized IOC management, provenance-preserving lifecycle state, JSON/CSV imports, event-to-IOC matching, URLhaus provider lookups, and an imported MITRE ATT&CK technique workspace. See [Threat intelligence documentation](docs/threat-intel/THREAT_INTELLIGENCE.md).

</div>

---

## 🚀 Overview

**NeuroSOC** is a modern **AI-assisted Security Operations Center (SOC) & SIEM platform** that helps security teams collect, normalize, correlate, investigate, and visualize security events through an intuitive dashboard and intelligent analyst assistance.

Designed for **defensive security, threat hunting, security research, and SOC training**, NeuroSOC combines modern software engineering with AI-powered investigation workflows.

---

## Implemented in this revision

- Argon2id password hashing with legacy SHA-256 verification and rehashing on login
- Short-lived access JWTs and separate refresh JWTs
- SQLite and PostgreSQL configuration, plus Bearer-token authentication
- Bounded JSONL/log/CSV uploads and normalized UTC timestamps
- Threshold-based failed-login, SSH brute-force, and repeated denied-access detections
- Rule and detection deduplication
- API-backed React overview, event, alert, detection, and case views
- SQLite/PostgreSQL CLI backup and confirmed restore workflows
- Docker Compose for frontend, API, and PostgreSQL

## Current limitations

- The remaining frontend menu routes are shells until their backend contracts are completed.
- Alembic migrations exist for the current schema, but production rollout and multi-version migration history require operational review.
- Redis/Celery, WebSockets, playbooks, and autonomous response may require external platform operations.
- The AI endpoint is a provider boundary with deterministic fallback, not an autonomous provider guarantee.
- Real-time ingestion and a complete browser login flow require additional integration.

---

## 🏗️ Architecture

```text
Security Logs
      │
      ▼
 Log Ingestion
      │
      ▼
 Event Normalization
      │
      ▼
 Detection Engine
      │
      ▼
 Alert Correlation
      │
      ▼
 AI Investigation Assistant
      │
      ▼
 Dashboard • Cases • Reports
```

---

## ⚙️ Tech Stack

| Backend | Frontend | Database | AI |
|---------|----------|----------|----|
| Python • FastAPI | React • TypeScript • Tailwind CSS | SQLite | AI-Assisted SOC Workflows |

---

## 🚀 Quick Start

### Backend

```bash
cp .env.example .env
python -m pip install -r backend/requirements.txt
alembic upgrade head
uvicorn app.main:app --app-dir backend --reload
```

API routes are available both at the compatibility root paths and under `/api/v1`. Core list endpoints accept `page`, `page_size`, `sort_by`, and `sort_order=asc|desc`, and return `items` plus pagination metadata.

Run tests with `pytest backend/tests -v`; run backend lint with `ruff check backend`.

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

### Production-like deployment

Create a separate PostgreSQL password, JWT secret, refresh secret, and explicit frontend origin. Never reuse local `.env` values.

```bash
export POSTGRES_PASSWORD="$(openssl rand -hex 32)"
export JWT_SECRET="$(openssl rand -hex 32)"
export JWT_REFRESH_SECRET="$(openssl rand -hex 32)"
export CORS_ORIGINS="https://soc.example.com"
docker compose up -d --build
curl -fsS http://localhost:8000/health/live
curl -fsS http://localhost:8000/health/ready
```

Production containers require PostgreSQL; SQLite is only supported in development and isolated automated testing. See [production configuration](docs/production/ENVIRONMENT_CONFIGURATION.md), [deployment](docs/production/DEPLOYMENT_RUNBOOK.md), [backup and restore](docs/production/BACKUP_AND_RESTORE.md), and [release operations](docs/production/RELEASE_PROCESS.md).

---

## 📂 Project Structure

```text
backend/
frontend/
docs/
tests/
docker/
scripts/
```

---

## 📜 Disclaimer

> **NeuroSOC is intended exclusively for authorized security operations, defensive security, education, and cybersecurity research. Users are responsible for complying with all applicable laws, organizational policies, and ethical guidelines.**

---

<div align="center">

### ⭐ If you find NeuroSOC useful, consider giving it a Star!

**Built with ❤️ for the Blue Team & Cybersecurity Community**

</div>
