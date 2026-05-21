import asyncio
import orjson

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.settings import settings
from app.core.redis import redis_manager
from app.core.log_config import configure_logging, get_logger
from app.api.v1.router import router as v1_router
from app.consumer.stream_consumer import stream_consumer
from app.workers.aggregator import threat_aggregator
from app.utils.geoip import geoip_service
from app.bot.notifier import notifier

configure_logging()
logger = get_logger(__name__)

consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("app.startup.begin")
    await redis_manager.connect()
    geoip_service.open()

    async def start_pipeline(event):
        await threat_aggregator.ingest(event)
  
    app.state.stream_task = asyncio.create_task(stream_consumer.start(start_pipeline))
    await notifier.setup()
    logger.info("app.startup.complete")

    yield

    logger.info("app.shutdown.begin")
    app.state.stream_task.cancel()
    
    try:
        await app.state.stream_task
    except Exception as e:
        logger.warning("stream_task_cancel_error", error=str(e))
    
    await notifier.close()  
    geoip_service.close() 
    await redis_manager.disconnect()

    logger.info("app.shutdown.complete")


def create_validation_error_response(exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": errors,
        },
    )


def create_general_exception_response(exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc) if settings.APP_DEBUG else "An unexpected error occurred",
        },
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Threat monitoring and analysis API for network security events",
        version="1.0.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", settings.APP_HOST] + settings.ALLOWED_ORIGINS,
    )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    

    app.add_exception_handler(
        RequestValidationError,
        lambda request, exc: create_validation_error_response(exc),
    )
    
    app.add_exception_handler(
        Exception,
        lambda request, exc: create_general_exception_response(exc),
    )
    

    app.include_router(v1_router,prefix=settings.API_V1_PREFIX,)


    logger.info(
        "app.created",
        title=app.title,
        debug=app.debug,
        routes_count=len(app.routes),
    )
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "uvicorn.start",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_config=None, 
    )
