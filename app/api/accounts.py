from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.account import (
    AccountBalanceResponse,
    AccountCreateRequest,
    AccountResponse,
)
from app.schemas.errors import ErrorResponse
from app.services.accounts import create_account, get_account_balance

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Account",
    description="Create a new ledger account. Balance is initialized to 0.00.",
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
    },
)
def create_account_endpoint(
    payload: AccountCreateRequest,
    db: Session = Depends(get_db),
):
    account = create_account(db, name=payload.name)
    return AccountResponse(
        id=account.id,
        name=account.name,
        balance=f"{account.balance:.2f}",
        created_at=account.created_at,
    )


@router.get(
    "/{account_id}/balance",
    response_model=AccountBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Account Balance",
    description="Retrieve the current available balance for an account.",
    responses={
        404: {"model": ErrorResponse, "description": "Account Not Found"},
    },
)
def get_balance_endpoint(
    account_id: UUID,
    db: Session = Depends(get_db),
):
    balance = get_account_balance(db, account_id)
    return AccountBalanceResponse(
        account_id=account_id,
        balance=f"{balance:.2f}",
    )
