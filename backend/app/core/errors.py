from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette import status


@dataclass(slots=True)
class AppError(Exception):
    code: str
    message: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: list[dict[str, Any]] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
