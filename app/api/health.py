from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Check operational status of the service.",
    response_model=dict,
)
def health_check():
    return {"status": "ok"}
