import asyncio
import uuid
import json
import orjson

from typing import Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.log_config import get_logger
from app.core.settings import settings
from app.schemas.response import WSHeartbeatMessage

logger = get_logger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        # client_id → WebSocket
        self._connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        #self._heartbeat_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        '''
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(),
            name="ws_manager.heartbeat",
        )
        '''

        logger.info("ws_manager.started")

    async def stop(self) -> None:
        async with self._lock:
            for ws in self._connections.values():
                try:
                    await ws.close()
                except Exception:
                    pass
            self._connections.clear()

        logger.info("ws_manager.stopped")


    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()

        async with self._lock:
            if len(self._connections) >= settings.WS_MAX_CONNECTIONS:
                await ws.close(code=1008, reason="Server at capacity")
                return ""

            client_id = str(uuid.uuid4())
            self._connections[client_id] = ws

        logger.info(
            "ws_manager.client_connected",
            client_id=client_id,
            total=len(self._connections),
        )

        return client_id

    async def disconnect(self, client_id: str) -> None:
                async with self._lock:
                    self._connections.pop(client_id, None)

                logger.info(
                    "ws_manager.client_disconnected",
                    client_id=client_id,
                    total=len(self._connections),
            )


    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return

        async with self._lock:
            snapshot = dict(self._connections)

        for client_id, ws in snapshot.items():
            try:
                if ws.application_state == WebSocketState.CONNECTED:
                    clean_message = json.loads(json.dumps(message, default=str))
                    await ws.send_json(clean_message)
            except Exception:
                await self.disconnect(client_id)
    '''
    # Heartbeat 

    async def _heartbeat_loop(self) -> None:
        heartbeat = orjson.dumps(
            WSHeartbeatMessage().model_dump(mode="json")
        )

        while True:
            try:
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
                await self.broadcast(heartbeat)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("ws_manager.heartbeat_error", error=str(e))
    '''

    @property
    def connection_count(self) -> int:
        return len(self._connections)

ws_manager = WebSocketManager()