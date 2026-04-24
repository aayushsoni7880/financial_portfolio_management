import asyncio
from fastapi import WebSocket

from app.workers.price_worker import PRICE_CACHE
import logging
logger = logging.getLogger(__name__)


async def websocket_prices(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(2)
            await websocket.send_json(dict(PRICE_CACHE))
    except Exception:
        logger.debug("WebSocket closed", exc_info=True)
