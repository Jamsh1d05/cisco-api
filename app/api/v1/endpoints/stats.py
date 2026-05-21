# app/api/v1/endpoints/stats.py

from fastapi import APIRouter, Depends, Query
from app.core.security import get_current_user, TokenData
from app.services.threat_service import threat_service
from app.schemas.response import APIResponse

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/live",
    response_model=APIResponse,
    summary="Текущая статистика",
    description="""
Возвращает полный снимок статистики за текущее окно агрегации.

**Используется для:** первичной загрузки дашборда.

**Возвращает:**
- Общее количество событий
- События в секунду
- Разбивку по severity
- Топ атакующих IP
- Топ атакуемых IP
- Количество заблокированных / разрешённых

    """,
)
async def get_live_stats(
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_live_stats()
    return APIResponse(data=data)


@router.get(
    "/top-attackers",
    response_model=APIResponse,
    summary="Топ атакующих IP",
    description="""
Возвращает список наиболее активных атакующих IP-адресов,
отсортированных по количеству событий (по убыванию).

**Используется для:** панели "Топ атакующих" на дашборде.

**Параметры:**
- `limit` — количество IP в ответе (от 1 до 50, по умолчанию 10)

**Каждый объект содержит:**
- `ip` — IP-адрес атакующего
- `count` — количество зафиксированных событий
- `severity` — максимальный уровень угрозы от этого IP
- `country` — страна происхождения
- `city` — город
- `lat`, `lon` — координаты для отображения на карте
- `last_seen` — время последнего события

    """,
)
async def get_top_attackers(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Количество IP-адресов в ответе",
    ),
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_top_attackers(limit=limit)
    return APIResponse(data=data)


@router.get(
    "/attack-types",
    response_model=APIResponse,
    summary="Типы атак",
    description="""
Возвращает разбивку событий по типам атак с количеством и процентным соотношением.

**Каждый объект содержит:**
- `type` — тип события (например: Intrusion Event, Malware Event)
- `count` — количество событий данного типа
- `percentage` — процент от общего числа событий

    """,
)
async def get_attack_types(
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_attack_types()
    return APIResponse(data=data)


@router.get(
    "/severity",
    response_model=APIResponse,
    summary="Разбивка по уровням угрозы",
    description="""
Возвращает количество и процентное соотношение событий по уровням severity.

**Используется для:** графика распределения угроз на дашборде.

**Возвращает:**
- `total` — общее количество событий
- `breakdown` — список объектов:
  - `severity` — уровень угрозы: critical / high / medium / low / info
  - `count` — количество событий
  - `percentage` — процент от общего числа

    """,
)
async def get_severity_breakdown(
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_severity_breakdown()
    return APIResponse(data=data)


@router.get(
    "/geo",
    response_model=APIResponse,
    summary="Геолокация атак",
    description="""
Возвращает список атакующих IP-адресов с географическими координатами
и количеством событий.

**Используется для:** карты с отображением источников атак.

**Каждый объект содержит:**
- `ip` — IP-адрес атакующего
- `lat`, `lon` — координаты для точки на карте
- `country` — страна атакующего
- `city` — город атакующего
- `count` — количество событий с этого IP

**Примечание:** внутренние IP-адреса (10.x, 192.168.x) возвращают
координаты 0.0 / 0.0 и country = "Internal".

    """,
)
async def get_geo_data(
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_geo_data()
    return APIResponse(data=data)


@router.get(
    "/blocked-ratio",
    response_model=APIResponse,
    summary="Соотношение заблокированных и разрешённых",
    description="""
Возвращает соотношение заблокированных и разрешённых событий
в текущем окне агрегации.

**Используется для:** графика blocked vs allowed на дашборде.

**Возвращает:**
- `blocked` — количество заблокированных событий
- `allowed` — количество разрешённых событий
- `total` — общее количество событий
- `blocked_percent` — процент заблокированных
- `allowed_percent` — процент разрешённых

    """,
)
async def get_blocked_ratio(
    user: TokenData = Depends(get_current_user),
):
    data = await threat_service.get_blocked_ratio()
    return APIResponse(data=data)