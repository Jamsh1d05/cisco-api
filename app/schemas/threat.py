from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatEvent(BaseModel):
    timestamp: Optional[datetime] = None
    type: str = "unknown"
    title: str = "no-title"
    severity: SeverityLevel = SeverityLevel.LOW
    protocol: str = "N/A"
    blocked: str = "false"

    # Network
    src_ip: str = "0.0.0.0"
    dst_ip: str = "0.0.0.0"

    # Geo
    src_lat:     float = 0.0
    src_lon:     float = 0.0
    src_country: str   = "Unknown"
    src_city:    str   = "Unknown"

    dst_lat:     float = 0.0
    dst_lon:     float = 0.0
    dst_country: str   = "Unknown"
    dst_city:    str   = "Unknown"
   
    # Redis metadata
    stream_id: Optional[str] = None

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v):
        if not v:
            return SeverityLevel.LOW
        return str(v).lower().strip()

    @field_validator("blocked", mode="before")
    @classmethod
    def normalize_blocked(cls, v):
        if not v:
            return "false"
        return str(v).lower().strip()

    @field_validator("timestamp", mode="before")
    @classmethod
    def fix_timestamp(cls, v):
        if not v:
            return None
        return v

    @property
    def is_blocked(self) -> bool:
        return self.blocked.lower() in ("yes", "true", "1", "blocked")

    @property
    def threat_score(self) -> int:
        return {
            SeverityLevel.CRITICAL: 95,
            SeverityLevel.HIGH: 75,
            SeverityLevel.MEDIUM: 55,
            SeverityLevel.LOW: 35,
            SeverityLevel.INFO: 15,
        }.get(self.severity, 10)