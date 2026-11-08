class AirQualityError(Exception):
    pass


class CSVProcessingError(AirQualityError):
    pass


class InvalidCSVError(CSVProcessingError):
    pass


class NoValidRowsError(CSVProcessingError):
    pass


class MeasurementNotFoundError(AirQualityError):
    pass