from enum import Enum


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    CHF = "CHF"
    JPY = "JPY"
    PLN = "PLN"
