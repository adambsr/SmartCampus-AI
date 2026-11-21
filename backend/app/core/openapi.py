from app.schemas.error import ErrorResponse

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Application error"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Request validation error"},
    500: {"model": ErrorResponse, "description": "Unexpected server error"},
}
