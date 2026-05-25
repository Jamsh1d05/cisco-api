from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class LoginRequest(BaseModel):
    username: str
    password: str


class APIResponse(BaseModel, Generic[T]):
    success:   bool = True
    data:      Optional[T] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    success:   bool = False
    error:     str
    detail:    Optional[Any] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaginatedResponse(BaseModel, Generic[T]):
    items:     List[T]
    total:     int
    page:      int
    page_size: int
    has_next:  bool


class WSEventMessage(BaseModel):
    event:     str = "threat_event"
    data:      dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WSStatsMessage(BaseModel):
    event:     str = "stats_update"
    data:      dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WSHeartbeatMessage(BaseModel):
    event:     str = "heartbeat"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AttackerSummary(BaseModel):
    ip:    str
    count: int


class TargetSummary(BaseModel):
    ip:    str
    count: int


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high:     int = 0
    medium:   int = 0
    low:      int = 0
    info:     int = 0


class ThreatStats(BaseModel):
    window_start:       datetime
    window_end:         datetime
    total_events:       int
    events_per_second:  float
    severity_breakdown: SeverityBreakdown
    top_attackers:      List[AttackerSummary]
    top_targets:        List[TargetSummary]
    blocked_count:      int
    allowed_count:      int
    unique_src_ips:     int
    unique_dst_ips:     int


class EventFilterParams(BaseModel):
    severity:   Optional[List[str]] = None
    type:       Optional[str] = None
    src_ip:     Optional[str] = None
    dst_ip:     Optional[str] = None
    blocked:    Optional[str] = None 
    page:       int = 1
    page_size:  int = 50