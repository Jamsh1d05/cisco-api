import asyncio
from datetime import datetime, timezone
from app.core.settings import settings
from app.core.log_config import get_logger
from app.schemas.threat import ThreatEvent, SeverityLevel

logger = get_logger(__name__)

SEVERITY_ORDER = {
    SeverityLevel.CRITICAL: 4,
    SeverityLevel.HIGH:     3,
    SeverityLevel.MEDIUM:   2,
    SeverityLevel.LOW:      1,
    SeverityLevel.INFO:     0,
}

MIN_SEVERITY_ORDER = SEVERITY_ORDER.get(
    SeverityLevel(settings.NOTIFICATION_MIN_SEVERITY),
    3,  # default to HIGH
)


class NotificationFilter:
    def __init__(self) -> None:
        self._ip_cooldowns:    dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def should_notify(self, event: ThreatEvent) -> bool:
        if not settings.ENABLE_NOTIFICATIONS:
            return False

        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return False

        event_severity_order = SEVERITY_ORDER.get(
            SeverityLevel(event.severity), 0
        )
        if event_severity_order < MIN_SEVERITY_ORDER:
            return False

        async with self._lock:
            now = datetime.now(timezone.utc)

            if event.src_ip in self._ip_cooldowns:
                elapsed = (now - self._ip_cooldowns[event.src_ip]).total_seconds()
                if elapsed < settings.NOTIFICATION_IP_COOLDOWN_SECONDS:
                    logger.debug(
                        "bot.filter.ip_cooldown",
                        ip=event.src_ip,
                        remaining=settings.NOTIFICATION_IP_COOLDOWN_SECONDS - elapsed,
                    )
                    return False

            self._ip_cooldowns[event.src_ip] = now

        logger.info(
            "bot.filter.passed",
            ip=event.src_ip,
            severity=event.severity,
            title=event.title,
        )
        return True

    async def cleanup_expired(self) -> None:
        async with self._lock:
            now = datetime.now(timezone.utc)
            self._ip_cooldowns = {
                ip: ts
                for ip, ts in self._ip_cooldowns.items()
                if (now - ts).total_seconds() < settings.NOTIFICATION_IP_COOLDOWN_SECONDS
            }
        logger.info(
            "bot.cooldowns_cleaned",
            remaining=len(self._ip_cooldowns),
        )

notification_filter = NotificationFilter()