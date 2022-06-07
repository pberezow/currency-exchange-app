from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, root_validator

from currency_exchange.dependencies import get_currency_exchange_service
from currency_exchange.enums import Currency
from currency_exchange.exceptions import ExchangeRateUnavailable
from currency_exchange.services.currency_exchange import CurrencyExchangeService

router = APIRouter()


class CurrencyExchangeRequest(BaseModel):
    exchange_date: str = Field(regex=r"\d{4}-\d{2}-\d{2}")
    in_currency: Currency
    out_currency: Currency
    amount: float

    @root_validator()
    def validate_pln_in_or_out(cls, values: dict):
        if Currency.PLN not in {values["in_currency"], values["out_currency"]}:
            raise ValueError(f"{values}One of 'in_currency', 'out_currency' has to be PLN.")
        return values


class CurrencyExchangeResponse(BaseModel):
    amount: float


@router.post("/exchange", response_model=CurrencyExchangeResponse, status_code=HTTPStatus.OK)
async def exchange(
    data: CurrencyExchangeRequest, service: CurrencyExchangeService = Depends(get_currency_exchange_service)
) -> CurrencyExchangeResponse:

    exchange_date = datetime.strptime(data.exchange_date, "%Y-%m-%d").date()
    try:
        result = await service.exchange(amount=data.amount, in_currency=data.in_currency, out_currency=data.out_currency, exchange_date=exchange_date)
    except ExchangeRateUnavailable as err:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Exchange rate unavailable for requested day."
        ) from err
    return CurrencyExchangeResponse(amount=result)
