import asyncio
import logging
from fastapi import FastAPI
import uvicorn
from app.api.router import router
from app.core.config import settings
from app.workers.price_worker import price_worker

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__file__)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)

def main():
    logger.info(f"Project setup started.")
    price_worker()


if __name__=="__main__":
    uvicorn.run("main:app", "localhost", 8080)
