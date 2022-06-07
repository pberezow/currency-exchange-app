from datetime import date
from typing import Optional

from sqlalchemy import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from currency_exchange.database.tables import ExchangeRate
from currency_exchange.enums import Currency


async def get_exchange_rate_from_db(
    async_session: AsyncSession, currency: Currency, exchange_date: date
) -> Optional[ExchangeRate]:
    query = select(ExchangeRate).where(and_(ExchangeRate.currency == currency, ExchangeRate.rate_date == exchange_date))
    return (await async_session.execute(query)).scalar_one_or_none()
