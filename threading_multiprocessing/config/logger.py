import logging

from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    yfinance_logger = logging.getLogger("yfinance")
    yfinance_logger.setLevel(
        getattr(logging, settings.YFINANCE_LOG_LEVEL.upper())
    )
    yfinance_logger.propagate = False