import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydoc import synopsis

import yfinance as yf

from app.core.config import settings
import logging
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=5)


def shutdown_market_executor() -> None:
    executor.shutdown(wait=False)


class MarketService:
    """Fetches last close prices via Yahoo Finance (yfinance)."""

    def _fetch_one(self, symbol: str) -> tuple[str, float | None]:
        ticker_symbol = f"{symbol}{settings.market_suffix}"
        logger.info(f"Symbol: {ticker_symbol}")
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1d")
            if hist.empty:
                logger.warning("No price data for %s", ticker_symbol)
                return symbol, None
            return symbol, float(hist["Close"].iloc[-1])
        except Exception:
            logger.exception("Failed to fetch price for %s", ticker_symbol)
            return symbol, None

    def get_live_prices(self, symbols: list[str]) -> dict[str, float]:
        results = {}
        if not symbols:
            return results

        for symbol in symbols:
            sym, price = self._fetch_one(symbol[0])
            if price is not None:
                results[sym] = price
        return results
