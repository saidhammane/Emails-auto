from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.database import init_db
from app.services.scheduler_service import scheduler_service

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    scheduler_service.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    scheduler_service.shutdown()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Email Dashboard & Automation Tool backend is running."}
