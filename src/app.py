from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.db.database import SessionLocal, init_db
from src.routes.queue_routes import router as queue_router
from src.services.aqis_service import aqis_service


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive Queue Intelligence System",
        version="1.0.0",
        description="AQIS backend with heap-based lazy updates and versioning",
    )
    app.include_router(queue_router)
    dashboard_path = Path(__file__).resolve().parent / "web" / "index.html"

    @app.on_event("startup")
    def startup_event() -> None:
        init_db()
        db = SessionLocal()
        try:
            aqis_service.bootstrap_from_db(db)
        finally:
            db.close()

    @app.get("/", tags=["UI"])
    def ui_dashboard() -> FileResponse:
        return FileResponse(dashboard_path)

    @app.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app
