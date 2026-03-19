from fastapi.responses import JSONResponse
from fastapi import Request

from src.domain.exceptions import BusinessException


def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "detail": exc.detail},
    )
