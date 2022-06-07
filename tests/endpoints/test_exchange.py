from decimal import Decimal
from http import HTTPStatus
from typing import Any
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from currency_exchange.enums import Currency
from currency_exchange.exceptions import ExchangeRateUnavailable


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, exchange_rate",
    [
        ({"date": "2010-01-10", "in_currency": "USD", "out_currency": "PLN", "amount": 1000}, Decimal(3.5)),
        ({"date": "2010-01-10", "in_currency": "PLN", "out_currency": "USD", "amount": 1000}, Decimal(3.5)),
        ({"date": "2010-01-10", "in_currency": "EUR", "out_currency": "PLN", "amount": 0.1}, Decimal(3.865)),
        ({"date": "2010-01-10", "in_currency": "PLN", "out_currency": "EUR", "amount": 0.1}, Decimal(3.865)),
    ],
)
async def test_exchange__ok(async_client: AsyncClient, payload: dict[str, Any], exchange_rate: Decimal):
    if payload["in_currency"] == Currency.PLN:
        expected_result = float(Decimal(payload["amount"]) / exchange_rate)
    else:
        expected_result = float(Decimal(payload["amount"]) * exchange_rate)

    with patch(
        "currency_exchange.services.currency_exchange.CurrencyExchangeService._get_exchange_rate",
        return_value=exchange_rate,
    ):
        resp = await async_client.post("/exchange", json=payload)

    assert resp.status_code == HTTPStatus.OK, resp.json()
    assert resp.json()["amount"] == expected_result


async def test_exchange__not_found(async_client: AsyncClient):
    with patch(
        "currency_exchange.services.currency_exchange.CurrencyExchangeService._get_exchange_rate",
        side_effect=ExchangeRateUnavailable,
    ):
        resp = await async_client.post("/exchange", json={"date": "2010-01-10", "in_currency": "USD", "out_currency": "PLN", "amount": 1000})

    assert resp.status_code == HTTPStatus.NOT_FOUND, resp.json()


async def test_exchange_missing_pln__bad_request(async_client: AsyncClient):
    resp = await async_client.post("/exchange", json={"date": "2010-01-10", "in_currency": "USD", "out_currency": "EUR", "amount": 1000})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, resp.json()
