
from datetime import datetime, timedelta

from src.business_logic.percentage_change_calculator import (
    calculate_percentage_change,
)
from src.business_logic.stock_price_fetcher import fetch_stock_data
from src.models.stock_data import StockFetchResult
from src.utils.logger import get_logger

logger = get_logger(__name__)


def process_stock_price(
    stock_type: str,
    hour: datetime,
) -> StockFetchResult:
    current_result = fetch_stock_data(stock_type, hour)

    if not current_result.success or current_result.result is None:
        return current_result

    previous_hour = hour - timedelta(hours=1)
    previous_result = fetch_stock_data(stock_type, previous_hour)

    if not previous_result.success or previous_result.result is None:
        return StockFetchResult(
            hour=hour,
            stock_type=stock_type,
            success=False,
            error=(
                f"Failed to fetch previous price at {previous_hour}: "
                f"{previous_result.error}"
            ),
        )

    try:
        percentage_change = calculate_percentage_change(
            current_result.result.current_price,
            previous_result.result.current_price,
        )

        logger.info(
            "Calculated percentage change for %s at %s: %.2f%%",
            stock_type,
            hour,
            percentage_change,
        )

        return StockFetchResult(
            hour=hour,
            stock_type=stock_type,
            success=True,
            result=current_result.result,
            percentage_change=percentage_change,
        )

    except ValueError as error:
        logger.exception(
            "Failed to calculate percentage change for %s at %s",
            stock_type,
            hour,
        )

        return StockFetchResult(
            hour=hour,
            stock_type=stock_type,
            success=False,
            result=current_result.result,
            error=str(error),
        )
