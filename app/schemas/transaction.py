from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Literal, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def validate_monetary_amount(v: Union[str, int, float, Decimal]) -> Decimal:
    if isinstance(v, float):
        # We prefer strings or Decimals to prevent floating point inaccuracies
        v = str(v)
    try:
        dec = Decimal(str(v).strip())
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Amount must be a valid numeric value.")

    if not dec.is_finite():
        raise ValueError("Amount must be a finite number.")

    if dec <= Decimal("0.00"):
        raise ValueError("Amount must be strictly greater than zero.")

    # Check maximum 2 decimal places: exponent should not be less than -2
    # e.g., Decimal('10.555').as_tuple().exponent == -3
    if dec.as_tuple().exponent < -2:
        raise ValueError("Amount cannot have more than two decimal places.")

    # Maximum 18 digits with 2 fractional digits -> 16 whole digits
    if dec >= Decimal("10000000000000000.00"):
        raise ValueError("Amount exceeds maximum allowed limit.")

    return dec


class TransactionCreateRequest(BaseModel):
    type: Literal["credit", "debit"] = Field(
        ..., description="Transaction type: credit or debit"
    )
    amount: Union[str, Decimal] = Field(
        ..., description="Transaction amount as a positive 2-decimal string or number"
    )
    description: str = Field(
        ..., min_length=1, max_length=500, description="Description of the transaction"
    )
    reference_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Client reference identifier, unique per account",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("amount")
    @classmethod
    def check_amount(cls, v: Any) -> Decimal:
        return validate_monetary_amount(v)

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError(
                "Description must contain at least one non-whitespace character."
            )
        return trimmed

    @field_validator("reference_id")
    @classmethod
    def check_reference_id(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError(
                "Reference ID must contain at least one non-whitespace character."
            )
        return trimmed


class TransactionItem(BaseModel):
    id: UUID
    account_id: UUID
    type: str
    amount: str
    description: str
    reference_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("amount", mode="plain")
    def serialize_amount(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    type: str
    amount: str
    description: str
    reference_id: str
    created_at: datetime
    account_balance: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("amount", mode="plain")
    def serialize_amount(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)

    @field_serializer("account_balance", mode="plain")
    def serialize_balance(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:.2f}"
        return str(value)


class PaginationMetadata(BaseModel):
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_records: int = Field(..., description="Total records matching criteria")
    total_pages: int = Field(..., description="Total pages available")


class TransactionHistoryResponse(BaseModel):
    items: List[TransactionItem]
    pagination: PaginationMetadata
