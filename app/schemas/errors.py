from typing import Any, Dict
from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context or field-level validation details",
    )


class ErrorResponse(BaseModel):
    error: ErrorDetails
