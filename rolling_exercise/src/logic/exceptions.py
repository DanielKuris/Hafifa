class ApplicationError(Exception):
    pass


class CSVProcessingError(ApplicationError):
    pass


class ColumnsMismatchError(CSVProcessingError):
    pass


class NoValidRowsError(CSVProcessingError):
    pass


class NoRecordsFoundError(ApplicationError):
    pass
