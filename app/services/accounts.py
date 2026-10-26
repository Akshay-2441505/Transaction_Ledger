from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.errors import AccountNotFoundError
from app.models.account import Account


def create_account(db: Session, name: str) -> Account:
    account = Account(
        name=name,
        balance=Decimal("0.00"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_account_by_id(db: Session, account_id: UUID) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise AccountNotFoundError()
    return account


def get_account_balance(db: Session, account_id: UUID) -> Decimal:
    account = get_account_by_id(db, account_id)
    return account.balance
