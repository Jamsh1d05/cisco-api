import asyncio
from typing import Optional

import httpx

from app.core.settings import settings
from app.core.log_config import get_logger
from app.schemas.threat import ThreatEvent
from app.bot.filters import notification_filter
from app.bot.templates import format_threat_event, format_stats_summary

logger = get_logger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    def __init__(self) -> None:
        self._client:  Optional[httpx.AsyncClient] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._url = TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)

    async def setup(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(),
            name="bot.cleanup",
        )
        logger.info(
            "bot.notifier.started",
            enabled=settings.ENABLE_NOTIFICATIONS,
            min_severity=settings.NOTIFICATION_MIN_SEVERITY,
        )

        if settings.ENABLE_NOTIFICATIONS:
            await self._send_message(
                "<b>Notifier started</b>\n"
                "Bot is ready to send threat notifications."
            )

    async def close(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if settings.ENABLE_NOTIFICATIONS:
            await self._send_message("<b>Notifier stopped</b>")

        if self._client:
            await self._client.aclose()

        logger.info("bot.notifier.stopped")

    async def send_event(self, event: ThreatEvent) -> None:
        if not await notification_filter.should_notify(event):
            return

        message = format_threat_event(event)

        asyncio.create_task(
            self._send_message(message),
            name="bot.send_event",
        )

    async def send_stats(self, stats: dict) -> None:
        if not settings.ENABLE_NOTIFICATIONS:
            return

        if stats.get("total_events", 0) == 0:
            return

        message = format_stats_summary(stats)

        asyncio.create_task(
            self._send_message(message),
            name="bot.send_stats",
        )

    async def _send_message(self, text: str) -> None:
        if not self._client:
            return

        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return

        payload = {
            "chat_id":    settings.TELEGRAM_CHAT_ID,
            "text":       text,
            "parse_mode": "HTML",
        }

        for attempt in range(2):  # try twice
            try:
                resp = await self._client.post(
                    self._url,
                    json=payload,
                )
                if resp.status_code == 200:
                    logger.info("bot.message_sent")
                    return
                else:
                    logger.warning(
                        "bot.send_failed",
                        status=resp.status_code,
                        response=resp.text[:200],
                    )
            except Exception as e:
                logger.error(
                    "bot.send_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                await asyncio.sleep(2)

    async def _cleanup_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(300)  # every 5 minutes
                await notification_filter.cleanup_expired()
                logger.info("bot.cooldowns_cleaned")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("bot.cleanup_error", error=str(e))


notifier = TelegramNotifier()