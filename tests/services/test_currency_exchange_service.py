from datetime import date
from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from currency_exchange.enums import Currency
from currency_exchange.exceptions import ExchangeRateUnavailable
from currency_exchange.services.currency_exchange import CurrencyExchangeService
from tests.helpers import get_exchange_rate_from_db


@pytest.mark.parametrize(
    "in_currency, out_currency, rate, amount, exchange_date",
    [
        (Currency.EUR, Currency.PLN, Decimal(1.6), 1000, date(2001, 1, 1)),
        (Currency.PLN, Currency.EUR, Decimal(1.6), 1000, date(2001, 1, 1)),
        (Currency.USD, Currency.PLN, Decimal(9.3), 0.5, date(2006, 1, 10)),
        (Currency.PLN, Currency.USD, Decimal(9.3), 0.5, date(2006, 1, 10)),
        (Currency.JPY, Currency.PLN, Decimal(0.01), 999999999999999999999, date(2030, 12, 31)),
        (Currency.PLN, Currency.JPY, Decimal(0.01), 999999999999999999999, date(2030, 12, 31)),
    ],
)
async def test_exchange_service__rate_saved(  # pylint: disable=too-many-arguments
    currency_exchange_service: CurrencyExchangeService,
    async_session: AsyncSession,
    in_currency: Currency, out_currency: Currency,
    rate: Decimal,
    amount: float,
    exchange_date: date,
):
    if in_currency == Currency.PLN:
        foreign_currency = out_currency
        expected_result = float(Decimal(amount) / rate)
    else:
        foreign_currency = in_currency
        expected_result = float(Decimal(amount) * rate)

    with patch("currency_exchange.services.nbp_api.NBPApiService.get_exchange_rate", return_value=rate) as mock:
        result = await currency_exchange_service.exchange(amount=amount, in_currency=in_currency, out_currency=out_currency, exchange_date=exchange_date)

        # check if nbp api was called
        assert result == expected_result
        mock.assert_awaited_once_with(exchange_date, foreign_currency)
        mock.reset_mock()

        # check if record was added to the database
        row = await get_exchange_rate_from_db(async_session, foreign_currency, exchange_date)
        assert row is not None
        assert row.rate == rate

        # check if nbp api was not called when record is present
        await currency_exchange_service.exchange(amount=amount, in_currency=in_currency, out_currency=out_currency, exchange_date=exchange_date)
        await currency_exchange_service.exchange(amount=amount, in_currency=out_currency, out_currency=in_currency, exchange_date=exchange_date)
        mock.assert_not_awaited()


async def test_exchange_service_rate_unavailable__raises_exception(
    currency_exchange_service: CurrencyExchangeService, async_session: AsyncSession
):
    with patch(
        "currency_exchange.services.nbp_api.NBPApiService.get_exchange_rate", side_effect=ExchangeRateUnavailable
    ) as mock:
        # check if nbp api was called
        with pytest.raises(ExchangeRateUnavailable):
            await currency_exchange_service.exchange(amount=1, in_currency=Currency.JPY, out_currency=Currency.PLN, exchange_date=date.today())

        mock.assert_awaited_once_with(date.today(), Currency.JPY)
        mock.reset_mock()

        # check if record was added to the database
        row = await get_exchange_rate_from_db(async_session, Currency.JPY, date.today())
        assert row is not None
        assert row.rate is None

        # check if nbp api was not called when record is present
        with pytest.raises(ExchangeRateUnavailable):
            await currency_exchange_service.exchange(amount=1, in_currency=Currency.JPY, out_currency=Currency.PLN, exchange_date=date.today())

        with pytest.raises(ExchangeRateUnavailable):
            await currency_exchange_service.exchange(amount=1, in_currency=Currency.PLN, out_currency=Currency.JPY, exchange_date=date.today())

        mock.assert_not_awaited()


async def test_exchange_service_nbp_api_unavailable__raises_exception(
    currency_exchange_service: CurrencyExchangeService, async_session: AsyncSession
):
    with patch(
        "currency_exchange.services.nbp_api.NBPApiService.get_exchange_rate", side_effect=httpx.HTTPError("Api error")
    ) as mock:
        # check if nbp api was called
        with pytest.raises(ExchangeRateUnavailable):
            await currency_exchange_service.exchange(amount=1, in_currency=Currency.JPY, out_currency=Currency.PLN, exchange_date=date.today())

        mock.assert_awaited_once_with(date.today(), Currency.JPY)

        # check if record was not added to the database
        row = await get_exchange_rate_from_db(async_session, Currency.JPY, date.today())
        assert row is None


async def test_exchange_service_not_pln_exchange__raises_exception(
        currency_exchange_service: CurrencyExchangeService
):
    with pytest.raises(ValueError):
        await currency_exchange_service.exchange(amount=1, in_currency=Currency.JPY, out_currency=Currency.EUR, exchange_date=date.today())
