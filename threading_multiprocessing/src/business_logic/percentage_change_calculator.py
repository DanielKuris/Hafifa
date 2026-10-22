def calculate_percentage_change(
    current_price: float,
    previous_price: float,
) -> float:
    if previous_price == 0:
        raise ValueError("Previous price cannot be zero")

    return (
        (current_price - previous_price)
        / previous_price
        * 100
    )
