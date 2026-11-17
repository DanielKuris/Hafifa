from pydantic import BaseModel


class ErrorResponse(BaseModel):
    errtype: str
    message: str
