from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from app.core.security import get_current_user, TokenData
from app.services.threat_service import threat_service
from app.schemas.response import APIResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", 
        response_model=APIResponse,
        summary="Список последних событий",
        description="""
Возвращает список последних событий и
из текущего окна агрегации.

**Фильтры :**
- `severity` — уровень угрозы: critical / high / medium / low / info
  (можно передать несколько: ?severity=high&severity=critical)
- `type` — тип события (например: Intrusion Event)
- `src_ip` — точный IP-адрес источника атаки
- `dst_ip` — точный IP-адрес цели атаки
- `blocked` — статус блокировки: Yes / No

**Пагинация:**
- `page` — номер страницы (по умолчанию 1)
- `page_size` — количество записей на странице (по умолчанию 20, максимум 100)

**Каждое событие содержит:**
- `timestamp` — время события
- `type` — тип события
- `title` — название сигнатуры / правила
- `severity` — уровень угрозы
- `protocol` — протокол (TCP / UDP / ICMP)
- `blocked` — заблокировано ли событие (Yes / No)
- `src_ip`, `dst_ip` — IP-адреса источника и назначения
- `src_lat`, `src_lon`, `src_country`, `src_city` — гео атакуещего
- `dst_lat`, `dst_lon`, `dst_country`, `dst_city` — гео цели

    """,
   )


async def get_events(
    severity:  Optional[List[str]] = Query(default=None),
    type:      Optional[str]       = Query(default=None),
    src_ip:    Optional[str]       = Query(default=None),
    dst_ip:    Optional[str]       = Query(default=None),
    blocked:   Optional[str]       = Query(default=None),
    page:      int                 = Query(default=1, ge=1),
    page_size: int                 = Query(default=20, ge=1, le=100),
    user:      TokenData           = Depends(get_current_user),
):
    data = await threat_service.get_events(
        severity=severity,
        type=type,
        src_ip=src_ip,
        dst_ip=dst_ip,
        blocked=blocked,
        page=page,
        page_size=page_size,
    )
    return APIResponse(data=data)