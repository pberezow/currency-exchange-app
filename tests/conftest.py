# pylint: disable=redefined-outer-name
import asyncio
from asyncio import AbstractEventLoop

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from currency_exchange.asgi import setup_application
from currency_exchange.config import AppConfig
from currency_exchange.database.repositories import ExchangeRateRepository
from currency_exchange.dependencies import get_async_db_session
from currency_exchange.services.currency_exchange import CurrencyExchangeService
from currency_exchange.services.nbp_api import NBPApiService


@pytest.fixture(scope="session")
def app_config() -> AppConfig:
    config = AppConfig()
    config.postgres_db = f"{config.postgres_db}_test"
    return config


@pytest.fixture(scope="session", autouse=True)
def test_db(app_config: AppConfig):
    db_uri = (f"postgresql://{app_config.postgres_user}:{app_config.postgres_password}@"
              f"{app_config.postgres_host}:{app_config.postgres_port}/{app_config.postgres_db}")
    if database_exists(db_uri):
        drop_database(db_uri)
    create_database(db_uri)

    yield

    if database_exists(db_uri):
        drop_database(db_uri)


@pytest.fixture(scope="session")
def event_loop() -> AbstractEventLoop:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session(app_config: AppConfig) -> AsyncSession:
    async_engine = create_async_engine(app_config.database_url, echo=True, future=True)
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with session() as ses:
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        yield ses

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await async_engine.dispose()


@pytest.fixture
def test_app(async_session: AsyncSession) -> FastAPI:
    app = setup_application()

    async def test_get_async_db_session() -> AsyncSession:
        yield async_session

    app.dependency_overrides[get_async_db_session] = test_get_async_db_session
    return app


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncClient:
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def nbp_api_service() -> NBPApiService:
    return NBPApiService()


@pytest.fixture
def exchange_rate_repository(async_session: AsyncSession) -> ExchangeRateRepository:
    return ExchangeRateRepository(async_session)


@pytest.fixture
def currency_exchange_service(
    exchange_rate_repository: ExchangeRateRepository, nbp_api_service: NBPApiService
) -> CurrencyExchangeService:
    return CurrencyExchangeService(exchange_rate_repository, nbp_api_service)
