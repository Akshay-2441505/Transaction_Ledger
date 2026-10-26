from typing import Any, Dict, Optional


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class AccountNotFoundError(AppException):
    def __init__(self, message: str = "The requested account was not found."):
        super().__init__(
            status_code=404,
            code="ACCOUNT_NOT_FOUND",
            message=message,
        )


class DuplicateReferenceError(AppException):
    def __init__(
        self,
        message: str = "A transaction with this reference ID already exists for the account.",
    ):
        super().__init__(
            status_code=409,
            code="DUPLICATE_REFERENCE",
            message=message,
        )


class InsufficientBalanceError(AppException):
    def __init__(
        self,
        message: str = "The account does not have sufficient funds for this debit.",
    ):
        super().__init__(
            status_code=409,
            code="INSUFFICIENT_BALANCE",
            message=message,
        )


class InvalidRequestError(AppException):
    def __init__(self, message: str = "Invalid request payload."):
        super().__init__(
            status_code=400,
            code="INVALID_REQUEST",
            message=message,
        )
