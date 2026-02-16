"""FastAPI application factory."""

from fastapi import FastAPI

from football_engine.api.dependencies.container import build_container
from football_engine.api.http.v1.router import api_v1_router
from football_engine.api.ws.v2.routes import ws_v2_router


def create_app() -> FastAPI:
    container = build_container()

    app = FastAPI(
        title=container.settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.state.container = container
    app.include_router(api_v1_router, prefix=container.settings.api_prefix)
    app.include_router(ws_v2_router)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"service": container.settings.app_name, "status": "ok"}

    return app
