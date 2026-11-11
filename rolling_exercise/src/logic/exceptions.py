class AirQualityError(Exception):
    pass


class CSVProcessingError(AirQualityError):
    pass


class ColumnsMismatchError(CSVProcessingError):
    pass


class NoValidRowsError(CSVProcessingError):
    pass


class NoRecordsFoundError(AirQualityError):
    pass
