
from fastapi import FastAPI
import uvicorn
from app.api.routers import router
from app.api.authentication_routers import auth_router
from app.core.config import settings
from app.workers.price_worker import price_worker
from app.core.logging import setup_logger
import logging

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)


setup_logger()

logger = logging.getLogger(__name__)

def main():
    logger.info(f"Project setup started.")
    price_worker()


if __name__=="__main__":
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)
