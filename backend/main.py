from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.requests import Request

from backend.api.health import router as health_router
from backend.api.v1 import api_router
from backend.core.config import get_settings
from backend.core.database import engine
from backend.core.exceptions import AppError, app_error_handler
from backend.core.logger import setup_logging
from backend.db.migrate import run_migrations
from backend.db.seed import run_seed
from backend.models.base import Base


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging()
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    if settings.seed_on_startup:
        run_seed()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                }
            },
        )

    app.include_router(health_router)
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/api/docs")

    @app.get("/docs", include_in_schema=False)
    def docs_redirect() -> RedirectResponse:
        return RedirectResponse(url="/api/docs")

    @app.get("/redoc", include_in_schema=False)
    def redoc_redirect() -> RedirectResponse:
        return RedirectResponse(url="/api/redoc")

    return app


app = create_app()
