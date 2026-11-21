from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.core.openapi import ERROR_RESPONSES

api_router = APIRouter(responses=ERROR_RESPONSES)
api_router.include_router(health_router, tags=["Health"])
