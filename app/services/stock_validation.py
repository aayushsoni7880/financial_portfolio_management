import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Stock

_NSE_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9&.\-]{0,31}$")


def validate_nse_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not _NSE_SYMBOL_RE.fullmatch(s):
        raise ValueError("Invalid symbol format (expected NSE-style ticker)")
    return s


async def require_registered_stock(db: AsyncSession, symbol: str) -> Stock:
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Symbol {symbol} is not in the stock registry. "
                "Run `python feed.py` to load Nifty 500 data, or add it via POST /api/stocks."
            ),
        )
    return row
