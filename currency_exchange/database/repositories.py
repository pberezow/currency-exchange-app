from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from currency_exchange.database.tables import ExchangeRate
from currency_exchange.enums import Currency
from currency_exchange.exceptions import ExchangeRateRecordDoesNotExist


class ExchangeRateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_exchange_rate(self, rate_date: date, currency: Currency, rate: Optional[Decimal]) -> None:
        exchange_rate = ExchangeRate(rate_date=rate_date, currency=currency, rate=rate)
        self.session.add(exchange_rate)
        await self.session.commit()

    async def get_exchange_rate(self, rate_date: date, currency: Currency) -> ExchangeRate:
        query = select(ExchangeRate).where(and_(ExchangeRate.rate_date == rate_date, ExchangeRate.currency == currency))
        result = (await self.session.execute(query)).scalar_one_or_none()
        if not result:
            raise ExchangeRateRecordDoesNotExist()
        return result
