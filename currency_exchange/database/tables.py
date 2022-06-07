from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as EnumType
from sqlmodel import Field, SQLModel

from currency_exchange.enums import Currency


class ExchangeRate(SQLModel, table=True):
    rate_date: date = Field(primary_key=True)
    currency: Currency = Field(primary_key=True, sa_column=Column(EnumType(Currency)))
    rate: Optional[Decimal]
