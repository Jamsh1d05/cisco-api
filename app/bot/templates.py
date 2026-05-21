from datetime import datetime, timezone
from app.schemas.threat import ThreatEvent, SeverityLevel


SEVERITY_EMOJI = {
    SeverityLevel.CRITICAL: "🔴",
    SeverityLevel.HIGH:     "🟠",
    SeverityLevel.MEDIUM:   "🟡",
    SeverityLevel.LOW:      "🟢",
    SeverityLevel.INFO:     "⚪",
}

BLOCKED_EMOJI = {
    "yes": "🛡️ Заблокировано",
    "no":  "⚠️ Пропущено",
}


def format_threat_event(event: ThreatEvent) -> str:
    severity    = SeverityLevel(event.severity)
    emoji       = SEVERITY_EMOJI.get(severity, "⚪")
    blocked_str = BLOCKED_EMOJI.get(event.blocked.lower(), "⚠️ Пропущено")

    severity_label = {
        SeverityLevel.CRITICAL: "КРИТИЧЕСКАЯ УГРОЗА",
        SeverityLevel.HIGH:     "ВЫСОКАЯ УГРОЗА",
        SeverityLevel.MEDIUM:   "СРЕДНЯЯ УГРОЗА",
        SeverityLevel.LOW:      "НИЗКАЯ УГРОЗА",
        SeverityLevel.INFO:     "ИНФОРМАЦИЯ",
    }.get(severity, "УГРОЗА")

    # Source location
    src_location = event.src_country
    if event.src_city and event.src_city != "Unknown":
        src_location = f"{event.src_country} / {event.src_city}"

    # Destination location
    dst_location = event.dst_country
    if event.dst_city and event.dst_city != "Unknown":
        dst_location = f"{event.dst_country} / {event.dst_city}"

    # Timestamp
    timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    message = (
        f"{emoji} <b>{severity_label}</b>\n\n"
        f"🎯 <b>{event.title}</b>\n"
        f"🌍 <b>Источник:</b>\n"
        f"  IP: <code>{event.src_ip}</code>\n"
        f"  Локация: {src_location}\n\n"
        f"🏠 <b>Цель:</b>\n"
        f"  IP: <code>{event.dst_ip}</code>\n"
        f"  Локация: {dst_location}\n\n"
        f"🔧 <b>Детали:</b>\n"
        f"  Протокол: {event.protocol}\n"
        f"  Тип: {event.type}\n"
        f"  Статус: {blocked_str}\n\n"
        f"🕐 {timestamp}"
    )

    return message


def format_stats_summary(stats: dict) -> str:
    severity = stats.get("severity_breakdown", {})
    message = (
        f"📊 <b>Сводка угроз</b>\n\n"
        f"📈 Всего событий: <b>{stats.get('total_events', 0)}</b>\n"
        f"⚡ События/сек: <b>{stats.get('events_per_second', 0)}</b>\n\n"
        f"🔴 Критических: <b>{severity.get('critical', 0)}</b>\n"
        f"🟠 Высоких: <b>{severity.get('high', 0)}</b>\n"
        f"🟡 Средних: <b>{severity.get('medium', 0)}</b>\n\n"
        f"🛡️ Заблокировано: <b>{stats.get('blocked_count', 0)}</b>\n"
        f"⚠️ Пропущено: <b>{stats.get('allowed_count', 0)}</b>\n\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return message