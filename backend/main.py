import threading

from fastapi import FastAPI
import uvicorn
from app.api.routers import router
from app.api.authentication_routers import auth_router
from app.core.config import settings
from app.core.database import SqlDatabase

from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logger
import logging


app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logger()



logger = logging.getLogger(__name__)

def run_api_server():
    uvicorn.run("main:app", host="localhost", port=8080)

def run_worker():
    pass
    # price_worker()  # infinite loop is fine

if __name__ == "__main__":
    t = threading.Thread(target=run_worker, daemon=True)
    t.start()

    run_api_server()   # main thread runs API
