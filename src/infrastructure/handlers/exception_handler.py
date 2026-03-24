from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import BusinessException


def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"message": str(exc), "error_code": exc.error_code},
    )
