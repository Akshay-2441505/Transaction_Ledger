from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Check operational status of the service.",
    response_model=dict,
)
def health_check():
    return {"status": "ok"}


@router.get(
    "/health/db",
    summary="Database Health Check",
    description="Verify active connectivity to PostgreSQL database.",
)
def health_db_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "disconnected", "detail": str(exc)},
        )

