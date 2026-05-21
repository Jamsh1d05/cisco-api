import asyncio

from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from app.core.log_config import get_logger
from app.services.ws_manager import ws_manager
from app.core.settings import settings
from app.schemas.threat import ThreatEvent, SeverityLevel
from app.schemas.response import ThreatStats,SeverityBreakdown,AttackerSummary,TargetSummary
from app.bot.notifier import notifier

logger = get_logger(__name__)


class ThreatAggregator:
    def __init__(self) -> None:
        self._total_events = 0
        self._blocked_count = 0
        self._allowed_count = 0

        self._severity_counts = defaultdict(int)
        self._attacker_counts = defaultdict(int)
        self._target_counts = defaultdict(int)
        self._type_counts = defaultdict(int)

        self._recent_events: list[dict] = []
        self._window_start = datetime.now(timezone.utc)

        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None


    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="aggregator.loop")
        logger.info("aggregator.started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("aggregator.stopped")


    async def ingest(self, event: ThreatEvent) -> None:
        async with self._lock:
            self._update(event)
            self._recent(event)

        await self._broadcast_event(event)
        await notifier.send_event(event) 
        
    def _update(self, event: ThreatEvent) -> None:
        self._total_events += 1
        self._severity_counts[event.severity] += 1
        self._attacker_counts[event.src_ip] += 1
        self._target_counts[event.dst_ip] += 1
        self._type_counts[event.type] += 1

        if event.is_blocked:
            self._blocked_count += 1
        else:
            self._allowed_count += 1

    def _recent(self, event: ThreatEvent) -> None:
        self._recent_events.append(event.model_dump(mode="json"))
        if len(self._recent_events) > settings.MAX_RECENT_EVENTS:
            self._recent_events.pop(0)


    async def get_recent_events(
        self,
        severity:  Optional[list[str]] = None,
        type:      Optional[str] = None,
        src_ip:    Optional[str] = None,
        dst_ip:    Optional[str] = None,
        blocked:   Optional[str] = None,
        page:      int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:

        async with self._lock:
            events = list(reversed(self._recent_events))

        if severity:
            sevs = {s.lower() for s in severity}
            events = [e for e in events if e["severity"] in sevs]

        if type:
            events = [e for e in events if e["type"] == type]

        if src_ip:
            events = [e for e in events if e["src_ip"] == src_ip]

        if dst_ip:
            events = [e for e in events if e["dst_ip"] == dst_ip]

        if blocked:
            events = [e for e in events if e["blocked"].lower() == blocked.lower()]

        total = len(events)
        start = (page - 1) * page_size
        end   = start + page_size

        return events[start:end], total
    

    async def get_recent_events_raw(self) -> list[dict]:
        """
        Returns raw recent events list as dicts.
        """
        async with self._lock:
            return list(reversed(self._recent_events))


    async def get_live_stats(self) -> ThreatStats:
        async with self._lock:
            return self._build_stats()


    async def _broadcast_event(self, event: ThreatEvent) -> None:
        payload = {
            "event": "threat_event",
            "data": event.model_dump(mode="json"),
        }
        await ws_manager.broadcast(payload)

    async def _broadcast_stats(self, stats: ThreatStats) -> None:
        payload = {
            "event": "stats_update",
            "data": stats.model_dump(mode="json"),
        }
        await ws_manager.broadcast(payload)


    def _build_stats(self) -> ThreatStats:
        now = datetime.now(timezone.utc)
        elapsed = max((now - self._window_start).total_seconds(), 1)

        return ThreatStats(
            window_start=self._window_start,
            window_end=now,
            total_events=self._total_events,
            events_per_second=round(self._total_events / elapsed, 2),

            severity_breakdown=SeverityBreakdown(
                critical=self._severity_counts.get(SeverityLevel.CRITICAL, 0),
                high=self._severity_counts.get(SeverityLevel.HIGH, 0),
                medium=self._severity_counts.get(SeverityLevel.MEDIUM, 0),
                low=self._severity_counts.get(SeverityLevel.LOW, 0),
                info=self._severity_counts.get(SeverityLevel.INFO, 0),
            ),

            top_attackers=self._top(self._attacker_counts, settings.TOP_N_ATTACKERS, AttackerSummary),
            top_targets=self._top(self._target_counts, settings.TOP_N_TARGETS, TargetSummary),

            blocked_count=self._blocked_count,
            allowed_count=self._allowed_count,
            unique_src_ips=len(self._attacker_counts),
            unique_dst_ips=len(self._target_counts),
        )

    def _top(self, data: dict, n: int, model: type):
        return [
            model(ip=k, count=v)
            for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)[:n]
        ]


    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(settings.AGGREGATION_WINDOW_SECONDS)

                async with self._lock:
                    stats = self._build_stats()
                    self._reset()

                await self._broadcast_stats(stats)
                await notifier.send_stats(stats.model_dump(mode="json"))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("aggregator.loop_error", error=str(e))

    def _reset(self) -> None:
        self._total_events = 0
        self._blocked_count = 0
        self._allowed_count = 0
        self._severity_counts.clear()
        self._attacker_counts.clear()
        self._target_counts.clear()
        self._type_counts.clear()
        self._recent_events.clear()
        self._window_start = datetime.now(timezone.utc)


threat_aggregator = ThreatAggregator()