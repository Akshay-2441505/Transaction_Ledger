import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.accounts import router as accounts_router
from app.api.health import router as health_router
from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.errors import AppException

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("ledger_api")

app = FastAPI(
    title="Transaction Ledger API",
    description="A reliable, atomic REST API for managing accounts and simulated financial transactions.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    sanitized_errors = []
    for err in exc.errors():
        sanitized_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid value"),
                "type": err.get("type", "value_error"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed for request parameters or payload.",
                "details": {"errors": sanitized_errors},
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code_map.get(exc.status_code, "HTTP_ERROR"),
                "message": exc.detail
                if isinstance(exc.detail, str)
                else "HTTP error occurred",
                "details": {},
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
                "details": {},
            }
        },
    )


# Register routers
app.include_router(health_router)
app.include_router(accounts_router)
app.include_router(transactions_router)

# Mount static directory and serve browser dashboard
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
@app.get("/api", include_in_schema=False)
@app.get("/api/", include_in_schema=False)
@app.get("/api/index", include_in_schema=False)
@app.get("/api/index.py", include_in_schema=False)
def serve_dashboard():
    candidates = [
        STATIC_DIR / "index.html",
        Path("static/index.html"),
        Path(__file__).resolve().parent / "static" / "index.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return HTMLResponse(content=candidate.read_text(encoding="utf-8"))
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "Dashboard UI not found.",
            }
        },
    )
