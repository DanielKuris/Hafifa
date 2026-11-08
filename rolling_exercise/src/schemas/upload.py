from pydantic import BaseModel


class UploadResponse(BaseModel):
    total_rows: int
    inserted_rows: int
    ignored_rows: int
    alerts_created: int