from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.openapi import ERROR_RESPONSES
from app.core.request_id import RequestIdMiddleware
from app.db.session import close_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="SmartCampus backend foundation for SA-7.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/", tags=["Root"], responses=ERROR_RESPONSES)
    async def root() -> dict[str, str]:
        return {"message": "Hello World"}

    return application


app = create_app()
