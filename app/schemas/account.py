from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class AccountCreateRequest(BaseModel):
    name: str = Field(
        ..., description="Account holder name", min_length=1, max_length=150
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError(
                "Account name must contain at least one non-whitespace character."
            )
        return trimmed


class AccountResponse(BaseModel):
    id: UUID
    name: str
    balance: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("balance", mode="plain")
    def serialize_balance(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)


class AccountBalanceResponse(BaseModel):
    account_id: UUID
    balance: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("balance", mode="plain")
    def serialize_balance(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)
