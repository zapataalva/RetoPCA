from typing import Optional


class BusinessException(Exception):
    def __init__(self, message: str, status_code: int = 400, detail: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
