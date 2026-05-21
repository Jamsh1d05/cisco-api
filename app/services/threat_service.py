from typing import Optional
from app.core.log_config import get_logger
from app.workers.aggregator import threat_aggregator
from app.schemas.response import PaginatedResponse

logger = get_logger(__name__)


class ThreatService:
    async def get_top_attackers(self, limit: int = 10) -> list[dict]:
        events = await threat_aggregator.get_recent_events_raw()

        attackers: dict[str, dict] = {}

        for event in events:
            ip = event["src_ip"]
            if ip not in attackers:
                attackers[ip] = {
                    "ip":        ip,
                    "count":     0,
                    "severity":  event["severity"],
                    "last_seen": event["timestamp"],
                }

            attackers[ip]["count"] += 1

            attackers[ip]["severity"] = self._highest_severity(
                attackers[ip]["severity"],
                event["severity"],
            )

            if event["timestamp"] > attackers[ip]["last_seen"]:
                attackers[ip]["last_seen"] = event["timestamp"]

        sorted_attackers = sorted(
            attackers.values(),
            key=lambda x: x["count"],
            reverse=True,
        )

        return sorted_attackers[:limit]


    async def get_attack_types(self) -> list[dict]:
        events = await threat_aggregator.get_recent_events_raw()

        type_counts: dict[str, int] = {}
        for event in events:
            t = event["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        total = sum(type_counts.values()) or 1  

        result = [
            {
                "type":       t,
                "count":      count,
                "percentage": round((count / total) * 100, 1),
            }
            for t, count in sorted(
                type_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        return result

    # Severity Breakdown 

    async def get_severity_breakdown(self) -> dict:
        events = await threat_aggregator.get_recent_events_raw()

        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for event in events:
            sev = event["severity"].lower()
            if sev in counts:
                counts[sev] += 1

        total = sum(counts.values()) or 1  

        breakdown = [
            {
                "severity":   sev,
                "count":      count,
                "percentage": round((count / total) * 100, 1),
            }
            for sev, count in counts.items()
            if count > 0 
        ]

        return {
            "total":     sum(counts.values()),
            "breakdown": breakdown,
        }

    #  Geo Map 

    async def get_geo_data(self) -> list[dict]:
        events = await threat_aggregator.get_recent_events_raw()

        geo_map: dict[str, dict] = {}

        for event in events:
            ip = event["src_ip"]

            if ip not in geo_map:
                geo_map[ip] = {
                    "ip":      ip,
                    "lat":     float(event.get("src_lat", 0.0)),
                    "lon":     float(event.get("src_lon", 0.0)),
                    "country": event.get("src_country", "Unknown"),  
                    "city":    event.get("src_city", "Unknown"),     
                    "count":   0,
                }

            geo_map[ip]["count"] += 1

        return sorted(
            geo_map.values(),
            key=lambda x: x["count"],
            reverse=True,
        )


    async def get_events(
        self,
        severity:  Optional[list[str]] = None,
        type:      Optional[str] = None,
        src_ip:    Optional[str] = None,
        dst_ip:    Optional[str] = None,
        blocked:   Optional[str] = None,
        page:      int = 1,
        page_size: int = 20,
    ) -> dict:

        items, total = await threat_aggregator.get_recent_events(
            severity=severity,
            type=type,
            src_ip=src_ip,
            dst_ip=dst_ip,
            blocked=blocked,
            page=page,
            page_size=page_size,
        )

        return {
            "items":     items,
            "total":     total,
            "page":      page,
            "page_size": page_size,
            "has_next":  (page * page_size) < total,
        }


    async def get_blocked_ratio(self) -> dict:
        stats = await threat_aggregator.get_live_stats()

        total   = (stats.blocked_count + stats.allowed_count) or 1
        blocked = stats.blocked_count
        allowed = stats.allowed_count

        return {
            "blocked":         blocked,
            "allowed":         allowed,
            "total":           total,
            "blocked_percent": round((blocked / total) * 100, 1),
            "allowed_percent": round((allowed / total) * 100, 1),
        }


    async def get_live_stats(self) -> dict:
        stats = await threat_aggregator.get_live_stats()
        return stats.model_dump(mode="json")


    def _highest_severity(self, current: str, new: str) -> str:
        """Return the higher severity of two."""
        order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        return current if order.get(current, 0) >= order.get(new, 0) else new
    

    def _get_country(self, lat: float, lon: float) -> str:

        if lat == 0.0 and lon == 0.0:
            return "Unknown"
        return "Unknown"  


threat_service = ThreatService()