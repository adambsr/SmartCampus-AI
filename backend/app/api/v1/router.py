from fastapi import APIRouter

from app.api.v1.endpoints.admission import router as admission_router
from app.api.v1.endpoints.admin_users import router as admin_users_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.candidates import router as candidates_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.guest_link import router as guest_link_router
from app.api.v1.endpoints.programs import router as programs_router
from app.api.v1.endpoints.visitor_sessions import router as visitor_sessions_router
from app.core.openapi import ERROR_RESPONSES

api_router = APIRouter(responses=ERROR_RESPONSES)
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, tags=["Account authentication"])
api_router.include_router(candidates_router, tags=["Candidates"])
api_router.include_router(admin_users_router, tags=["User administration"])
api_router.include_router(programs_router, tags=["Programs"])
api_router.include_router(admission_router, tags=["Admission & fees"])
api_router.include_router(conversations_router, tags=["Conversations"])
api_router.include_router(guest_link_router, tags=["Guest conversation transfer"])
api_router.include_router(visitor_sessions_router, tags=["Visitor sessions"])
