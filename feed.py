#!/usr/bin/env python3
"""
Seed the local SQLite DB with Nifty 500–style Indian equities: symbol, company name,
sector/industry (when Yahoo Finance returns them), and a price snapshot in `price_history`.

Run from the project root:
  python feed.py
  python feed.py --limit 50    # subset for a quick test

Requires network access (CSV download + Yahoo Finance).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.schema_patch import patch_sqlite_stocks_columns
from app.models.models import PriceHistory, Stock
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NIFTY500_CSV_URL = (
    "https://raw.githubusercontent.com/yogeshnarang/Nifty-Index-Clustering/master/"
    "nse-indices-symbols.csv"
)


def load_nifty500_symbols() -> list[str]:
    req = urllib.request.Request(
        NIFTY500_CSV_URL,
        headers={"User-Agent": "portfolio-feed/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames or "nifty500" not in reader.fieldnames:
        raise RuntimeError(f"Unexpected CSV columns: {reader.fieldnames}")

    seen: set[str] = set()
    for row in reader:
        cell = (row.get("nifty500") or "").strip()
        if not cell:
            continue
        if cell.upper().endswith(".NS"):
            cell = cell[:-3]
        sym = cell.strip().upper()
        if sym:
            seen.add(sym)
    return sorted(seen)


def fetch_yahoo_bundle(symbol: str) -> dict:
    """One Yahoo Finance pass per symbol (price + metadata)."""
    ysym = f"{symbol}{settings.market_suffix}"
    t = yf.Ticker(ysym)
    name = symbol
    sector = None
    industry = None
    price = None

    try:
        info = getattr(t, "info", None) or {}
        name = (
            info.get("longName")
            or info.get("shortName")
            or info.get("name")
            or symbol
        )
        s = info.get("sector")
        ind = info.get("industry")
        if s:
            sector = str(s)[:128]
        if ind:
            industry = str(ind)[:256]
    except Exception:
        logger.debug("info failed for %s", symbol, exc_info=True)

    try:
        hist = t.history(period="5d")
        if not hist.empty:
            price = float(hist["Close"].iloc[-1])
    except Exception:
        logger.debug("history failed for %s", symbol, exc_info=True)

    return {
        "symbol": symbol,
        "name": str(name)[:256],
        "sector": sector,
        "industry": industry,
        "price": price,
    }


async def upsert_rows(rows: list[dict]) -> tuple[int, int]:
    inserted = 0
    snapshots = 0
    async with AsyncSessionLocal() as db:
        for r in rows:
            sym = r["symbol"]
            q = await db.execute(select(Stock).where(Stock.symbol == sym))
            existing = q.scalar_one_or_none()
            if existing:
                existing.name = r["name"]
                existing.sector = r["sector"]
                existing.industry = r["industry"]
            else:
                db.add(
                    Stock(
                        symbol=sym,
                        name=r["name"],
                        sector=r["sector"],
                        industry=r["industry"],
                    )
                )
                inserted += 1
            if r["price"] is not None:
                db.add(PriceHistory(symbol=sym, price=r["price"]))
                snapshots += 1
        await db.commit()
    return inserted, snapshots


async def run_async(limit: int | None, workers: int) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await patch_sqlite_stocks_columns(engine)

    symbols = load_nifty500_symbols()
    logger.info("Loaded %s unique symbols from Nifty 500 column", len(symbols))
    if limit is not None:
        symbols = symbols[:limit]

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_yahoo_bundle, s): s for s in symbols}
        done = 0
        for fut in as_completed(futures):
            rows.append(fut.result())
            done += 1
            if done % 50 == 0 or done == len(symbols):
                logger.info("Fetched Yahoo data: %s / %s", done, len(symbols))

    inserted, snapshots = await upsert_rows(rows)
    logger.info(
        "Done. New stocks inserted: %s (others updated in place). Price snapshots saved: %s",
        inserted,
        snapshots,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Nifty ~500 stocks into SQLite")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N symbols (for testing)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Parallel Yahoo Finance workers",
    )
    args = parser.parse_args()
    asyncio.run(run_async(args.limit, args.workers))


if __name__ == "__main__":
    main()
