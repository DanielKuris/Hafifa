from response_schemas.alert import AlertResponse
from response_schemas.air_quality import AirQualityResponse

HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422

TEST_DATABASE_NAME = "air_quality_test_db"
MISSING_CITY = "__missing_city__"

ALERT_FIELDS = set(AlertResponse.model_fields)
AIR_QUALITY_FIELDS = set(AirQualityResponse.model_fields)