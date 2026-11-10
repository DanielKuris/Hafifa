import numpy as np
import pandas as pd


PM25_BREAKPOINTS = (
    (0, 12, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
)

NO2_BREAKPOINTS = (
    (0, 53, 0, 50),
    (54, 100, 51, 100),
    (101, 360, 101, 150),
    (361, 649, 151, 200),
    (650, 1249, 201, 300),
    (1250, 2049, 301, 500),
)

CO2_BREAKPOINTS = (
    (0, 5, 0, 50),
    (5.1, 15, 51, 100),
    (15.1, 30, 101, 150),
    (30.1, 60, 151, 200),
    (60.1, 100, 201, 300),
    (100.1, 200, 301, 500),
)

AQI_THRESHOLDS = (
    (50, "Good"),
    (100, "Moderate"),
    (150, "Unhealthy for Sensitive Groups"),
    (200, "Unhealthy"),
    (300, "Very Unhealthy"),
    (500, "Hazardous"),
)


def calculate_sub_index(
    values: pd.Series,
    breakpoints: tuple[tuple[float, float, float, float], ...],
) -> pd.Series:
    values = pd.to_numeric(values)

    conditions = []
    calculations = []

    for lower, upper, aqi_lower, aqi_upper in breakpoints:
        conditions.append(values.between(lower, upper))

        calculations.append(
            aqi_lower
            + (values - lower) * (aqi_upper - aqi_lower) / (upper - lower)
        )

    return pd.Series(
        np.select(conditions, calculations, default=500.0),
        index=values.index,
    )


def calculate_aqi(dataframe: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    pm25_aqi = calculate_sub_index(dataframe["pm25"], PM25_BREAKPOINTS)
    no2_aqi = calculate_sub_index(dataframe["no2"], NO2_BREAKPOINTS)
    co2_aqi = calculate_sub_index(dataframe["co2"], CO2_BREAKPOINTS)

    aqi_value = pd.concat(
        [pm25_aqi, no2_aqi, co2_aqi],
        axis=1,
    ).max(axis=1).clip(lower=0, upper=500)

    conditions = [
        aqi_value <= threshold
        for threshold, _ in AQI_THRESHOLDS
    ]

    descriptions = [description for _, description in AQI_THRESHOLDS]

    aqi_description = pd.Series(
        np.select(conditions, descriptions, default="Hazardous"),
        index=dataframe.index,
    )

    return aqi_value, aqi_description