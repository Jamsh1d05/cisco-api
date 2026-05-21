import asyncio
import json

from datetime import timezone, datetime
from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect, HTTPException

from app.core.log_config import get_logger
from app.core.settings import settings
from app.services.ws_manager import ws_manager
from app.core.security import get_ws_user

logger = get_logger(__name__)

router = APIRouter()

@router.websocket("/connect")
async def websocket_connect(websocket: WebSocket, token: str = Query(..., description="JWT token")):
    client_id = None

    try:
        user = get_ws_user(token) 
    except HTTPException:
        await websocket.close(code=1008, reason="Unauthorized")
        logger.warning("websocket.rejected_invalid_token")
        return

    try:
        client_id = await ws_manager.connect(websocket) 

        logger.info("websocket.connected", client_id=client_id)

        await websocket.send_json({
            "event": "Success", 
            "message": "Connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("websocket.disconnected", client_id=client_id)

    finally:
        if client_id is not None:
            await ws_manager.disconnect(client_id)  


@router.websocket("/stats")
async def ws_stats(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        while True:
            stats = {
                "active_connections": ws_manager.connection_count,
                "max_connections": settings.WS_MAX_CONNECTIONS
            }

            await websocket.send_json(stats)
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
