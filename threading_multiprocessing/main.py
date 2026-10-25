from config.logger import configure_logging, get_logger
from config.settings import settings
from src.business_logic.convert_df_to_percent_change import (
    convert_stock_prices_to_percent_change,
)
from src.business_logic.stock_price_fetcher_with_threads import (
    fetch_stock_prices_concurrently,
)
from src.data.csv_writer import write_dataframe_to_csv
from src.data.input_reader import get_timestamps_per_stock_per_day


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)

    logger.info("Starting stock price processing")

    stock_timestamps = get_timestamps_per_stock_per_day(settings.INPUT_DIRECTORY)

    logger.info(f"Resolved stock types: {', '.join(stock_timestamps.keys())}")

    logger.info("Fetching stock prices")
    stock_prices = fetch_stock_prices_concurrently(stock_timestamps)
    logger.info(f"Fetched {len(stock_prices)} stock price records")

    logger.info("Calculating percentage changes")
    percentage_changes = convert_stock_prices_to_percent_change(stock_prices)

    destination_file = settings.OUTPUT_DIRECTORY / settings.DESTINATION_FILE_NAME

    write_dataframe_to_csv(percentage_changes, destination_file)
    logger.info(f"Finished writing percentage-change results to {destination_file}")

    logger.info("Stock price processing completed")


if __name__ == "__main__":
    main()