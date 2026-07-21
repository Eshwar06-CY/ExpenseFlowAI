import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception handlers on the FastAPI application.
    Standardizes error responses to return JSON formats.
    """
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP error occurred: {exc.detail} (status code: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "detail": exc.detail,
                "error_code": f"HTTP_{exc.status_code}"
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        
        # Sanitize error ctx if they contain raw non-serializable exception objects
        sanitized_errors = []
        for err in exc.errors():
            err_copy = dict(err)
            if "ctx" in err_copy:
                err_copy["ctx"] = {
                    k: str(v) if isinstance(v, Exception) else v 
                    for k, v in err_copy["ctx"].items()
                }
            sanitized_errors.append(err_copy)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "detail": "Request validation failed.",
                "errors": sanitized_errors,
                "error_code": "VALIDATION_ERROR"
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database transaction error occurred:")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "detail": "A database error occurred. Please contact system support.",
                "error_code": "DATABASE_ERROR"
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Uncaught application error occurred:")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "detail": "An internal server error occurred.",
                "error_code": "INTERNAL_SERVER_ERROR"
            }
        )
