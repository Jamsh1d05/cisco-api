from fastapi import APIRouter, Depends
from app.core.settings import settings
from app.core.security import get_current_user, TokenData

router = APIRouter()

@router.get("/", summary="API Root", description="Get basic information about the API")
async def root(user: TokenData = Depends(get_current_user)):
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "env": settings.APP_ENV,
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }