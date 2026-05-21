# app/consumer/stream_consumer.py
import asyncio

from typing import Callable, Awaitable

from app.core.log_config import get_logger
from app.core.redis import redis_manager
from app.core.settings import settings
from app.schemas.threat import ThreatEvent
from app.utils.geoip import geoip_service

logger = get_logger(__name__)


class StreamConsumer:

    def __init__(self) -> None:
        self._running = False
        # "$" new records after startup
        # "0" historical records from stream
        self._last_id = "$"

    async def start(self, callback: Callable[[ThreatEvent], Awaitable[None]]) -> None:
        self._running = True

        logger.info(
            "stream_consumer.started",
            stream=settings.REDIS_STREAM_KEY,
            from_id=self._last_id,
        )

        try:
            while self._running:
                try:
                    await self._read_batch(callback)

                except asyncio.CancelledError:
                    logger.info("stream_consumer.cancelled")
                    break

                except Exception as e:
                    logger.error("stream_consumer.read_error", error=str(e))
                    await asyncio.sleep(1)

        finally:
            logger.info("stream_consumer.stopped")

    async def _read_batch(self, callback: Callable[[ThreatEvent], Awaitable[None]]) -> None:
        results = await redis_manager.xread(
            stream_key=settings.REDIS_STREAM_KEY,
            last_id=self._last_id,
            block_ms=settings.STREAM_BLOCK_MS,
            count=settings.STREAM_BATCH_SIZE,
        )

        if not results:
            return  

        for _, records in results:
            for record_id, fields in records:
                self._last_id = record_id 

                event = self._parse_record(record_id, fields)
                if event is None:
                    continue 

                await callback(event)

    def _parse_record(self, record_id: str, fields: dict) -> ThreatEvent | None:
        try:
            event = ThreatEvent(
                stream_id=record_id,
                **fields,         
            )

            src_geo = geoip_service.lookup(event.src_ip, is_destination=False)
            dst_geo = geoip_service.lookup(event.dst_ip, is_destination=True)

            event.src_lat     = src_geo["lat"]
            event.src_lon     = src_geo["lon"]
            event.src_country = src_geo["country"]
            event.src_city    = src_geo["city"]

            event.dst_lat     = dst_geo["lat"]
            event.dst_lon     = dst_geo["lon"]
            event.dst_country = dst_geo["country"]
            event.dst_city    = dst_geo["city"]

            return event

        except Exception as e:
            logger.warning(
                "stream_consumer.parse_failed",
                record_id=record_id,
                error=str(e),
                fields=fields,
            )
            return None

    def stop(self) -> None:
        self._running = False
        logger.info("stream_consumer.stopped")

stream_consumer = StreamConsumer()