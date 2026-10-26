import math
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import (
    AccountNotFoundError,
    DuplicateReferenceError,
    InsufficientBalanceError,
)
from app.models.account import Account
from app.models.transaction import Transaction


def create_transaction(
    db: Session,
    account_id: UUID,
    transaction_type: str,
    amount: Decimal,
    description: str,
    reference_id: str,
) -> Tuple[Transaction, Decimal]:
    """
    Executes an atomic credit or debit transaction on an account.
    Enforces pessimistic row locking (FOR UPDATE), duplicate reference checking,
    balance verification, and atomic commit/rollback.
    """
    reference_id = reference_id.strip()

    try:
        # Step 1: Acquire exclusive row-level lock on the target account
        # PostgreSQL: SELECT ... FROM accounts WHERE id = :id FOR UPDATE
        account = (
            db.execute(
                select(Account).where(Account.id == account_id).with_for_update()
            )
            .scalars()
            .first()
        )

        if not account:
            raise AccountNotFoundError()

        # Step 2: Check for duplicate reference_id within this account
        existing_ref = (
            db.execute(
                select(Transaction.id).where(
                    Transaction.account_id == account_id,
                    Transaction.reference_id == reference_id,
                )
            )
            .scalars()
            .first()
        )
        if existing_ref:
            raise DuplicateReferenceError()

        # Step 3: Check funds and calculate updated balance
        if transaction_type == "credit":
            new_balance = account.balance + amount
        elif transaction_type == "debit":
            if account.balance < amount:
                raise InsufficientBalanceError()
            new_balance = account.balance - amount
        else:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        # Step 4: Update account balance
        account.balance = new_balance

        # Step 5: Insert transaction record
        tx = Transaction(
            account_id=account_id,
            type=transaction_type,
            amount=amount,
            description=description,
            reference_id=reference_id,
        )
        db.add(tx)

        # Step 6: Atomic commit
        db.commit()
        db.refresh(tx)
        return tx, new_balance

    except IntegrityError as exc:
        db.rollback()
        err_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        if "uq_account_reference" in err_msg:
            raise DuplicateReferenceError()
        elif "check_account_balance_non_negative" in err_msg:
            raise InsufficientBalanceError()
        raise
    except Exception:
        db.rollback()
        raise


def get_transaction_history(
    db: Session,
    account_id: UUID,
    transaction_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[Transaction], Dict[str, int]]:
    """
    Retrieves paginated and filtered transaction history for an account.
    """
    # Step 1: Confirm account exists
    account_exists = (
        db.execute(select(Account.id).where(Account.id == account_id)).scalars().first()
    )
    if not account_exists:
        raise AccountNotFoundError()

    # Step 2: Build query with optional type filter
    base_query = select(Transaction).where(Transaction.account_id == account_id)
    if transaction_type:
        base_query = base_query.where(Transaction.type == transaction_type)

    # Step 3: Compute total records
    count_query = select(Transaction.id).where(Transaction.account_id == account_id)
    if transaction_type:
        count_query = count_query.where(Transaction.type == transaction_type)
    total_records = len(db.execute(count_query).all())

    # Step 4: Compute pagination metadata
    total_pages = math.ceil(total_records / limit) if total_records > 0 else 0
    offset = (page - 1) * limit

    # Step 5: Retrieve sorted records
    query = (
        base_query.order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.execute(query).scalars().all())

    pagination = {
        "page": page,
        "page_size": limit,
        "total_records": total_records,
        "total_pages": total_pages,
    }
    return items, pagination
