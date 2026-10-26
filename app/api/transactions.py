from typing import Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.errors import ErrorResponse
from app.schemas.transaction import (
    PaginationMetadata,
    TransactionCreateRequest,
    TransactionHistoryResponse,
    TransactionItem,
    TransactionResponse,
)
from app.services.transactions import create_transaction, get_transaction_history

router = APIRouter(prefix="/accounts", tags=["Transactions"])


@router.post(
    "/{account_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transaction",
    description="Record an atomic credit or debit transaction on an account.",
    responses={
        404: {"model": ErrorResponse, "description": "Account Not Found"},
        409: {
            "model": ErrorResponse,
            "description": "Duplicate Reference or Insufficient Balance",
        },
        422: {"model": ErrorResponse, "description": "Validation Error"},
    },
)
def create_transaction_endpoint(
    account_id: UUID,
    payload: TransactionCreateRequest,
    db: Session = Depends(get_db),
):
    tx, new_balance = create_transaction(
        db=db,
        account_id=account_id,
        transaction_type=payload.type,
        amount=payload.amount,
        description=payload.description,
        reference_id=payload.reference_id,
    )
    return TransactionResponse(
        id=tx.id,
        account_id=tx.account_id,
        type=tx.type,
        amount=f"{tx.amount:.2f}",
        description=tx.description,
        reference_id=tx.reference_id,
        created_at=tx.created_at,
        account_balance=f"{new_balance:.2f}",
    )


@router.get(
    "/{account_id}/transactions",
    response_model=TransactionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Transaction History",
    description="Retrieve paginated and optionally filtered transaction history for an account.",
    responses={
        404: {"model": ErrorResponse, "description": "Account Not Found"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
    },
)
def get_transaction_history_endpoint(
    account_id: UUID,
    type: Optional[Literal["credit", "debit"]] = Query(
        None, description="Filter transactions by type: credit or debit"
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(
        20, ge=1, le=100, description="Items per page (1-100, default 20)"
    ),
    db: Session = Depends(get_db),
):
    items, pagination = get_transaction_history(
        db=db,
        account_id=account_id,
        transaction_type=type,
        page=page,
        limit=limit,
    )

    transaction_items = [
        TransactionItem(
            id=item.id,
            account_id=item.account_id,
            type=item.type,
            amount=f"{item.amount:.2f}",
            description=item.description,
            reference_id=item.reference_id,
            created_at=item.created_at,
        )
        for item in items
    ]

    return TransactionHistoryResponse(
        items=transaction_items,
        pagination=PaginationMetadata(**pagination),
    )
