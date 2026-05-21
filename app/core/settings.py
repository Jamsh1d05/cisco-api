from pathlib import Path
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "CFM API"
    APP_ENV: str = "production"
    APP_DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    API_USERNAME: str = "admin"
    API_PASSWORD: str 

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECRET_KEY: str = "default"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_MAX_CONNECTIONS: int = 20

    REDIS_STREAM_KEY: str = "alerts_stream"      
    REDIS_PUBSUB_EVENTS: str = "tm:events"    
    REDIS_PUBSUB_STATS: str = "tm:stats"     
    REDIS_CACHE_STATS_KEY: str = "tm:stats:latest" 
    REDIS_CACHE_TTL: int = 120                

    STREAM_BLOCK_MS: int = 5000    
    STREAM_BATCH_SIZE: int = 100  

    AGGREGATION_WINDOW_SECONDS: int = 60   
    TOP_N_ATTACKERS: int = 10
    TOP_N_TARGETS: int = 10
    MAX_RECENT_EVENTS: int = 500          

    TELEGRAM_BOT_TOKEN:        str  = ""
    TELEGRAM_CHAT_ID:          str  = ""
    ENABLE_NOTIFICATIONS:      bool = False
    NOTIFICATION_MIN_SEVERITY: str  = "high"
    NOTIFICATION_IP_COOLDOWN_SECONDS:    int  = 300   # 5 min per IP
    #NOTIFICATION_TITLE_COOLDOWN_SECONDS: int  = 600   # 10 min per title
    
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()