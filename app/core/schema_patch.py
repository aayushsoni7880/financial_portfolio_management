"""SQLite additive migrations for existing local DB files."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def patch_sqlite_stocks_columns(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for ddl in (
            "ALTER TABLE stocks ADD COLUMN sector VARCHAR(128)",
            "ALTER TABLE stocks ADD COLUMN industry VARCHAR(256)",
        ):
            try:
                await conn.execute(text(ddl))
            except Exception:
                pass
