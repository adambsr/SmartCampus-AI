from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Check backend health",
    description="A lightweight endpoint that confirms the API is responding.",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "smartcampus-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
