from src.business_logic.convert_df_to_percent_change import (
    convert_stock_prices_to_percent_change,
)
from src.business_logic.fetch_orchestration import (
    fetch_stock_prices_concurrently,
)
from src.business_logic.fetch_orchestration import create_stock_price_tasks
from src.config.logger import configure_logging, get_logger
from src.config.settings import settings
from src.data.csv_writer import write_dataframe_to_csv
from src.data.input_reader import get_stock_data


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)

    logger.info("Starting stock price processing")

    stock_data = get_stock_data(settings.INPUT_DIRECTORY)

    logger.info(
        f"Resolved stock IDs: {', '.join(stock_data['stock_id'].unique())}"
    )

    tasks = create_stock_price_tasks(
        stock_data,
        settings.DEFAULT_SPLIT_TIME,
    )

    logger.info(f"Created {len(tasks)} stock price tasks")

    stock_prices = fetch_stock_prices_concurrently(tasks)

    logger.info(f"Fetched {len(stock_prices)} stock price records")

    percentage_changes = convert_stock_prices_to_percent_change(stock_prices)

    destination_file = (
        settings.OUTPUT_DIRECTORY / settings.DESTINATION_FILE_NAME
    )

    write_dataframe_to_csv(percentage_changes, destination_file)

    logger.info("Stock price processing completed")


if __name__ == "__main__":
    main()
