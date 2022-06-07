from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from currency_exchange.endpoints.exchange import router as exchange_router


def setup_application() -> FastAPI:
    application = FastAPI()

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.router.include_router(exchange_router)
    return application


app = setup_application()
