from config.logger import configure_logging, get_logger
from config.settings import settings
from src.business_logic.convert_csv_to_percent_change import (
    convert_csv_to_percent_change,
)
from src.business_logic.write_to_csv_with_workers import (
    write_stock_prices_concurrently,
)
from src.data.timestamp_reader import get_timestamps_per_stock

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    logger.info("Starting stock price processing")

    stock_timestamps = get_timestamps_per_stock(settings.INPUT_DIRECTORY)

    logger.info(
        "Resolved stock types: %s",
        ", ".join(stock_timestamps.keys()),
    )
    

    logger.info("Fetching stock prices")
    write_stock_prices_concurrently(
        stock_timestamps,
        settings.TEMP_CSV_STOCK_PRICES_FILE,
    )
    logger.info(
        "Finished fetching stock prices. Results saved to %s",
        settings.TEMP_CSV_STOCK_PRICES_FILE,
    )

    destination_file = (
        settings.OUTPUT_DIRECTORY / settings.DESTINATION_FILE_NAME
    )

    logger.info("Calculating percentage changes and writing output CSV")
    convert_csv_to_percent_change(
        settings.TEMP_CSV_STOCK_PRICES_FILE,
        destination_file,
    )
    logger.info(
        "Finished writing percentage-change results to %s",
        destination_file,
    )

    logger.info("Stock price processing completed")


if __name__ == "__main__":
    main()