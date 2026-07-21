from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine
from app.routers.alerts import router as alerts_router
from app.routers.analytics import router as analytics_router
from app.routers.assistant import router as assistant_router
from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router
from app.routers.detections import router as detections_router
from app.routers.events import router as events_router
from app.routers.reports import router as reports_router
from app.routers.search import router as search_router
from app.routers.settings import router as settings_router

app = FastAPI(title="NeuroSOC", version="0.1.0", docs_url="/docs", openapi_url="/openapi.json")
app.add_middleware(SessionMiddleware, secret_key="dev-secret")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
