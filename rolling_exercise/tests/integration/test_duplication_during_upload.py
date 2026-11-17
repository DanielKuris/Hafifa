import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tests.fixtures.constants import AIR_QUALITY_FIELDS, TO_CSV_COLUMN_NAMES


@pytest.mark.integration
def test_upload_measurements_with_duplicates(
    client: TestClient,
    measurement_dataframe_with_duplicates: pd.DataFrame,
    measurements_that_would_produce_alerts: pd.DataFrame,
) -> None:
    duplicate_count = measurement_dataframe_with_duplicates.duplicated(
        subset=["date", "city"]
    ).sum()

    csv_dataframe = measurement_dataframe_with_duplicates.loc[
        :,
        [
            field
            for field in AIR_QUALITY_FIELDS
            if field not in {"id", "aqi", "aqi_level"}
        ],
    ].rename(columns=TO_CSV_COLUMN_NAMES)

    response = client.post(
        "/air-quality/upload",
        files={
            "file": (
                "measurements.csv",
                csv_dataframe.to_csv(index=False).encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    upload_summary = response.json()

    assert upload_summary["total_rows"] == len(measurement_dataframe_with_duplicates)
    assert upload_summary["inserted_rows"] == len(measurement_dataframe_with_duplicates)
    assert upload_summary["ignored_rows"] == 0
    assert upload_summary["alerts_created"] == len(
        measurements_that_would_produce_alerts
    )

    measurements_response = client.get("/air-quality/measurements")

    assert measurements_response.status_code == 200

    measurements = pd.DataFrame(measurements_response.json())

    assert len(measurements) == len(measurement_dataframe_with_duplicates)
    assert measurements.duplicated(subset=["date", "city"]).sum() == duplicate_count
