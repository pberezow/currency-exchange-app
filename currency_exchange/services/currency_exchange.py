from datetime import date
from decimal import Decimal

import httpx

from currency_exchange.database.repositories import ExchangeRateRepository
from currency_exchange.enums import Currency
from currency_exchange.exceptions import (
    ExchangeRateRecordDoesNotExist,
    ExchangeRateUnavailable,
)
from currency_exchange.services.nbp_api import NBPApiService


class CurrencyExchangeService:
    def __init__(self, exchange_rate_repository: ExchangeRateRepository, nbp_api_service: NBPApiService):
        self.exchange_rate_repository = exchange_rate_repository
        self.nbp_api_service = nbp_api_service

    async def _get_exchange_rate(self, rate_date: date, currency: Currency) -> Decimal:
        try:
            exchange_rate = await self.exchange_rate_repository.get_exchange_rate(rate_date, currency)
            if exchange_rate.rate is None:
                raise ExchangeRateUnavailable()
            return exchange_rate.rate
        except ExchangeRateRecordDoesNotExist:
            try:
                rate = await self.nbp_api_service.get_exchange_rate(rate_date, currency)
            except ExchangeRateUnavailable:
                # if exchange rate is unavailable for specific date then insert null value to database
                await self.exchange_rate_repository.insert_exchange_rate(rate_date, currency, None)
                raise
            except httpx.HTTPError as err:
                # if api call failed raise exception, but don't save null value of the exchange rate
                raise ExchangeRateUnavailable() from err
            await self.exchange_rate_repository.insert_exchange_rate(rate_date, currency, rate)
        return rate

    async def exchange(self, amount: float, in_currency: Currency, out_currency: Currency, exchange_date: date) -> float:
        if in_currency == Currency.PLN:
            exchange_rate = await self._get_exchange_rate(exchange_date, out_currency)
            return float(Decimal(amount) / exchange_rate)
        if out_currency == Currency.PLN:
            exchange_rate = await self._get_exchange_rate(exchange_date, in_currency)
            return float(Decimal(amount) * exchange_rate)
        raise ValueError("in_currency or out_currency argument has to be PLN.")
