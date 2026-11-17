import allure
import pandas as pd
from fastapi.testclient import TestClient

from tests.fixtures.constants import (
    HTTP_OK,
)


@allure.story("CSV Upload")
@allure.title("Upload CSV and return the upload summary")
def test_upload_measurements(
    client: TestClient,
    csv_dataframe: pd.DataFrame,
) -> None:
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

    assert response.status_code == HTTP_OK

    upload_summary = response.json()
    alerts = client.get("/alerts/").json()

    assert upload_summary["total_rows"] == len(csv_dataframe)
    assert upload_summary["inserted_rows"] == len(csv_dataframe)
    assert upload_summary["ignored_rows"] == 0
    assert upload_summary["alerts_created"] == len(alerts)
