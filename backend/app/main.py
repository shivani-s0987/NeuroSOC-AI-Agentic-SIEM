import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, log_request
from app.routers.alerts import router as alerts_router
from app.routers.analytics import router as analytics_router
from app.routers.assistant import router as assistant_router
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router
from app.routers.detections import router as detections_router
from app.routers.events import router as events_router
from app.routers.reports import router as reports_router
from app.routers.search import router as search_router
from app.routers.settings import router as settings_router
from app.routers.realtime import router as realtime_router
from app.routers.threat_intelligence import router as threat_intelligence_router, mitre_router

app = FastAPI(title="NeuroSOC", version="0.1.0", docs_url="/docs", openapi_url="/openapi.json")
configure_logging(settings.log_level)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
    return response


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    log_request(request.method, request.url.path, response.status_code, duration_ms, request_id)
    return response


app.include_router(auth_router)
app.include_router(events_router)
app.include_router(alerts_router)
app.include_router(detections_router)
app.include_router(search_router)
app.include_router(cases_router)
app.include_router(reports_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(assistant_router)
app.include_router(admin_router)
app.include_router(realtime_router)
app.include_router(threat_intelligence_router)
app.include_router(mitre_router)

for router in (
    auth_router,
    events_router,
    alerts_router,
    detections_router,
    search_router,
    cases_router,
    reports_router,
    analytics_router,
    settings_router,
    assistant_router,
    admin_router,
    realtime_router,
    threat_intelligence_router,
    mitre_router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok", "check": "live"}


@app.get("/health/ready")
def health_ready() -> dict[str, str]:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db.commit()
        return {"status": "ok", "check": "ready", "database": "ready"}
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
