import logging

from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class InfoOnlyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.INFO


def create_formatter() -> logging.Formatter:
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def create_console_handler(formatter: logging.Formatter) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.addFilter(InfoOnlyFilter())
    handler.setFormatter(formatter)

    return handler


def create_file_handler(formatter: logging.Formatter) -> logging.Handler:
    settings.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

    log_file = settings.LOG_DIRECTORY / settings.LOG_FILE_NAME
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    return handler


def configure_yfinance_logging() -> None:
    yfinance_logger = logging.getLogger("yfinance")
    yfinance_logger.setLevel(getattr(logging, settings.YFINANCE_LOG_LEVEL.upper()))
    yfinance_logger.propagate = True


def configure_logging() -> None:
    formatter = create_formatter()

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            create_console_handler(formatter),
            create_file_handler(formatter),
        ],
        force=True,
    )

    configure_yfinance_logging()
