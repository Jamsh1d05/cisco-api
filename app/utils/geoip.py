import geoip2.database
import geoip2.errors
from pathlib import Path
from typing import Optional
from functools import lru_cache

from app.core.log_config import get_logger

logger = get_logger(__name__)

GEOIP_DB_PATH = Path(__file__).resolve().parent.parent.parent /"GeoLite2-City_20260417"/"GeoLite2-City.mmdb"

ORG_LAT     = 51.16812421697976
ORG_LON     = 71.4215152246305
ORG_COUNTRY = "Kazakhstan"
ORG_CITY    = "Astana"

_PRIVATE_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.", "192.168.", "127.", "0.",
)

class GeoIPService:

    def __init__(self) -> None:
        self._reader: Optional[geoip2.database.Reader] = None
        self._cache:  dict[str, dict] = {}   
    def open(self) -> None:
        if not GEOIP_DB_PATH.exists():
            logger.warning(
                "geoip.database_not_found",
                path=str(GEOIP_DB_PATH),
                note="Download GeoLite2-City.mmdb from maxmind.com",
            )
            return
        self._reader = geoip2.database.Reader(str(GEOIP_DB_PATH))
        logger.info("geoip.database_opened", path=str(GEOIP_DB_PATH))

    def close(self) -> None:
        if self._reader:
            self._reader.close()
            logger.info("geoip.database_closed")

    def lookup(self, ip: str, is_destination: bool = False) -> dict:
            cache_key = f"{ip}:{is_destination}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            result = self._resolve(ip, is_destination)
            self._cache[cache_key] = result
            return result

    def _resolve(self, ip: str, is_destination: bool) -> dict:
        if self._is_private(ip):
            if is_destination:
                return {
                    "lat":     ORG_LAT,
                    "lon":     ORG_LON,
                    "country": ORG_COUNTRY,
                    "city":    ORG_CITY,
                }
            
            return {
                "lat":     0.0,
                "lon":     0.0,
                "country": "Internal",
                "city":    "Unknown",
            }

        if not self._reader:
            return {"lat": 0.0, "lon": 0.0, "country": "Unknown", "city": "Unknown"}

        try:
            response = self._reader.city(ip)
            return {
                "lat":     float(response.location.latitude  or 0.0),
                "lon":     float(response.location.longitude or 0.0),
                "country": str(response.country.name         or "Unknown"),
                "city":    str(response.city.name            or "Unknown"),
            }
        except geoip2.errors.AddressNotFoundError:
            return {"lat": 0.0, "lon": 0.0, "country": "Unknown", "city": "Unknown"}
        except Exception as e:
            logger.warning("geoip.lookup_failed", ip=ip, error=str(e))
            return {"lat": 0.0, "lon": 0.0, "country": "Unknown", "city": "Unknown"}

    def _is_private(self, ip: str) -> bool:
        return any(ip.startswith(prefix) for prefix in _PRIVATE_PREFIXES)


geoip_service = GeoIPService()