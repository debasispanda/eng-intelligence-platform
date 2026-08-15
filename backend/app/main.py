from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        docs_url="/docs" if app_settings.docs_enabled else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[app_settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.include_router(api_router)

    return app


app = create_app()
