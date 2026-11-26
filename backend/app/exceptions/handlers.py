from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "APP_ERROR",
        details: Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso no encontrado", details: Any = None) -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND, "NOT_FOUND", details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "No autenticado", details: Any = None) -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Acceso denegado", details: Any = None) -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN", details)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflicto con el estado actual", details: Any = None) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT", details)


class BadRequestException(AppException):
    def __init__(self, message: str = "Solicitud inválida", details: Any = None) -> None:
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", details)


class InsufficientStockException(AppException):
    def __init__(self, message: str = "Stock insuficiente", details: Any = None) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT, "INSUFFICIENT_STOCK", details)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Error de validación en los datos enviados.",
                    "details": exc.errors(),
                },
            },
        )

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Demasiadas solicitudes. Intenta nuevamente en unos segundos.",
                    "details": str(exc.detail),
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Ocurrió un error interno inesperado.",
                    "details": None,
                },
            },
        )
