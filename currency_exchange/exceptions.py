class BaseCustomException(Exception):
    """Base Exception for other custom exceptions."""


class ExchangeRateUnavailable(BaseCustomException):
    """Exception raised when exchange rate for some date is unavailable."""


class ExchangeRateRecordDoesNotExist(BaseCustomException):
    """Exception raised when exchange rate is not available in the database."""
