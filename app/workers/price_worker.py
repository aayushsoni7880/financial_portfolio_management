import logging
from app.services.db_service import portfolio_db_service
from app.services.market_service import MarketService
import time
logger = logging.getLogger(__name__)

PRICE_CACHE: dict[str, float] = {}

def price_worker() -> None:
    try:
        while True:
            logger.info("Price worker started.")
            db_service = portfolio_db_service()
            market_service = MarketService()

            symbols = db_service.get_stocks_symbols()
            prices = market_service.get_live_prices(symbols)

            for sym, price in prices.items():
                PRICE_CACHE[sym] = price

            for sym, price in prices.items():
                db_service.update_price_details(sym, price)
            logger.info(f"Price worker finished, Sleeping for 15 minutes.")
            time.sleep(300)
    except Exception as err:
        logger.error(f"Failed in price worker, Error: {err}")


