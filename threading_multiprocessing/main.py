from config.logger import configure_logging, get_logger
from config.settings import settings
from src.business_logic.convert_csv_to_percent_change import (
    convert_csv_to_percent_change,
)
from src.business_logic.write_to_csv_with_workers import (
    write_stock_prices_concurrently,
)
from src.data.input_reader import get_timestamps_per_stock_per_day


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)

    logger.info("Starting stock price processing")

    stock_timestamps = get_timestamps_per_stock_per_day(settings.INPUT_DIRECTORY)

    logger.info(f"Resolved stock types: {', '.join(stock_timestamps.keys())}")

    logger.info("Fetching stock prices")
    write_stock_prices_concurrently(
        stock_timestamps,
        settings.TEMP_CSV_STOCK_PRICES_FILE,
    )
    logger.info(
        f"Finished fetching stock prices. Results saved to "
        f"{settings.TEMP_CSV_STOCK_PRICES_FILE}"
    )

    destination_file = settings.OUTPUT_DIRECTORY / settings.DESTINATION_FILE_NAME

    logger.info("Calculating percentage changes and writing output CSV")
    convert_csv_to_percent_change(
        settings.TEMP_CSV_STOCK_PRICES_FILE,
        destination_file,
    )
    logger.info(f"Finished writing percentage-change results to {destination_file}")

    logger.info("Stock price processing completed")


if __name__ == "__main__":
    main()
