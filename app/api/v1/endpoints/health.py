"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends

from app.core.redis import redis_manager
from app.core.log_config import get_logger
from app.schemas.response import APIResponse
from app.core.settings import settings
from app.core.security import get_current_user, TokenData

logger = get_logger(__name__)

router = APIRouter()

@router.get("", response_model=APIResponse[dict], summary="Health Check", description="Returns detailed health status of the API and other servies")
async def check_health_detailed() -> APIResponse[dict]:
    try:
        ping_time = await redis_manager.client.ping()
        redis_version = (await redis_manager.client.info())["redis_version"]
        redis_data = {
            "status": "OK",
            "version": redis_version,
            "ping_response": str(ping_time),
        }
    except Exception as e:
        logger.warning("health.check.detailed.redis_failed", error=str(e))
        redis_data = {
            "status": "Error",
            "error": str(e),
        }
    
    health_data = {
        "status": "OK" if redis_data.get("status") == "OK" else "Error",
        "redis": redis_data,
        "api": {
            "status": "OK",
        },
    }
    
    return APIResponse(success=True, data=health_data)
