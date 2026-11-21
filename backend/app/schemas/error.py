from pydantic import BaseModel, Field


class ErrorDetailSchema(BaseModel):
    field: str | None = None
    reason: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetailSchema] = Field(default_factory=list)
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
