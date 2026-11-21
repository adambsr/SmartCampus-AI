from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    """An expected application error with an HTTP status and stable code."""

    code: str
    message: str
    status_code: int = 400
    details: list[dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message
