import uuid
from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    account = relationship("Account", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference"),
        CheckConstraint("amount > 0", name="check_transaction_amount_positive"),
        CheckConstraint("type IN ('credit', 'debit')", name="check_transaction_type"),
        Index(
            "ix_transactions_account_created_id",
            "account_id",
            created_at.desc(),
            id.desc(),
        ),
    )
