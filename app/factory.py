"""Create isolated FastAPI applications with explicit dependencies and lifecycle."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from config.settings import Settings
from infrastructure.container import Container, use_container


def create_app(settings: Settings | None = None, *, container: Container | None = None) -> FastAPI:
    dependencies = container or Container(settings)

    @asynccontextmanager
    async def lifespan(_app):
        dependencies.settings  # Validate once at startup; errors remain visible.
        await dependencies.proactive.start()
        try:
            yield
        finally:
            await dependencies.proactive.stop()

    app = FastAPI(title="Bina Core API", version="1.0.0", lifespan=lifespan)
    app.state.container = dependencies

    @app.middleware("http")
    async def scope(request: Request, call_next):
        with use_container(dependencies):
            return await call_next(request)

    @app.exception_handler(HTTPException)
    async def domain_error(_request: Request, exc: HTTPException):
        # Stable machine codes; the existing detail text remains compatible.
        codes = {
            400: "invalid_request",
            404: "not_found",
            409: "turn_conflict",
            410: "archived",
            422: "invalid_option",
            499: "disconnected",
            502: "model_failed",
            503: "service_unavailable",
        }
        return JSONResponse(
            {"code": codes.get(exc.status_code, "internal_error"), "detail": exc.detail},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    from modules.chat_api.routes import router
    from modules.personas.routes import router as personas

    app.include_router(router)
    app.include_router(personas)
    return app
