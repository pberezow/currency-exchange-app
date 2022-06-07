from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from currency_exchange.config import AppConfig
from currency_exchange.database.repositories import ExchangeRateRepository
from currency_exchange.services.currency_exchange import CurrencyExchangeService
from currency_exchange.services.nbp_api import NBPApiService

async_engine = create_async_engine(AppConfig().database_url, echo=True, future=True)


async def get_async_db_session() -> AsyncSession:
    async_session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def get_exchange_rate_repository(session: AsyncSession = Depends(get_async_db_session)) -> ExchangeRateRepository:
    return ExchangeRateRepository(session)


async def get_nbp_api_service() -> NBPApiService:
    return NBPApiService()


async def get_currency_exchange_service(
    exchange_rate_repository: ExchangeRateRepository = Depends(get_exchange_rate_repository),
    nbp_api_service: NBPApiService = Depends(get_nbp_api_service),
) -> CurrencyExchangeService:
    return CurrencyExchangeService(exchange_rate_repository, nbp_api_service)
