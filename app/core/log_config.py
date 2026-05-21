import logging
import sys
import structlog
from app.core.settings import settings


def configure_logging() -> None:
    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.APP_ENV == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for name in ("uvicorn.access", "elasticsearch", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


'''
# Temp testing
if __name__ == "__main__":
    configure_logging()
    logger = get_logger(__name__)

    # Basic levels
    logger.debug("debug.test", env=settings.APP_ENV)
    logger.info("info.test", app=settings.APP_NAME, port=settings.APP_PORT)
    logger.warning("warning.test", message="this is a warning")
    logger.error("error.test", message="this is an error")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("exception.test", message="caught an exception")

    configure_logging()
    configure_logging()
    logger.info("duplicate.guard.test", message="It is working")

'''