from fastapi import APIRouter
from app.api.v1.endpoints import health, events, stats, websocket, root, auth
from app.core.settings import settings

router = APIRouter()

# Routers
router.include_router(root.router, tags=["Main"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(websocket.router, prefix="/ws", tags=["Websocket"])
router.include_router(events.router)
router.include_router(stats.router)

    
