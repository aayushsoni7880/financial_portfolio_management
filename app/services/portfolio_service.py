import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Position, PriceHistory, Transaction, User
from app.schemas.schemas import (
    PortfolioHoldingOut,
    PortfolioPeriodMetricsOut,
    PortfolioSummaryOut,
    Timeframe,
    TransactionCreate,
    TransactionSide,
)
from app.services.stock_validation import require_registered_stock
from app.workers.price_worker import PRICE_CACHE

_TIMEFRAME_DAYS: dict[Timeframe, int] = {
    Timeframe.d1: 1,
    Timeframe.w1: 7,
    Timeframe.m1: 30,
    Timeframe.m3: 90,
    Timeframe.m6: 180,
    Timeframe.y1: 365,
    Timeframe.y3: 365 * 3,
    Timeframe.y5: 365 * 5,
}


class PortfolioService:
    async def require_user(self, db: AsyncSession, user_id: int) -> User:
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return user

    async def create_transaction(self, db: AsyncSession, txn: TransactionCreate) -> Transaction:
        await self.require_user(db, txn.user_id)
        await require_registered_stock(db, txn.symbol)

        db_txn = Transaction(
            user_id=txn.user_id,
            symbol=txn.symbol,
            quantity=txn.quantity,
            price=txn.price,
            type=txn.type.value,
        )
        db.add(db_txn)

        result = await db.execute(
            select(Position).where(Position.user_id == txn.user_id, Position.symbol == txn.symbol)
        )
        pos = result.scalar_one_or_none()

        if txn.type == TransactionSide.buy:
            if pos:
                total = pos.avg_price * pos.quantity + txn.price * txn.quantity
                pos.quantity += txn.quantity
                pos.avg_price = total / pos.quantity
            else:
                db.add(
                    Position(
                        user_id=txn.user_id,
                        symbol=txn.symbol,
                        quantity=txn.quantity,
                        avg_price=txn.price,
                    )
                )
        elif txn.type == TransactionSide.sell:
            if not pos or txn.quantity > pos.quantity:
                raise HTTPException(status_code=400, detail="Insufficient holdings for this sale")
            pos.quantity -= txn.quantity
            if pos.quantity == 0:
                await db.delete(pos)

        await db.commit()
        await db.refresh(db_txn)
        return db_txn

    async def get_portfolio_summary(self, db: AsyncSession, user_id: int) -> PortfolioSummaryOut:
        await self.require_user(db, user_id)

        positions_res = await db.execute(select(Position).where(Position.user_id == user_id))
        positions = list(positions_res.scalars().all())
        symbols = [p.symbol for p in positions]
        latest_prices = await self._get_latest_prices(db, symbols)

        holdings: list[PortfolioHoldingOut] = []
        unrealized_pnl_total = 0.0
        for p in positions:
            last_price = PRICE_CACHE.get(p.symbol, latest_prices.get(p.symbol, p.avg_price))
            invested = p.avg_price * p.quantity
            current = last_price * p.quantity
            pnl = current - invested
            unrealized_pnl_total += pnl
            holdings.append(
                PortfolioHoldingOut(
                    symbol=p.symbol,
                    quantity=p.quantity,
                    avg_price=p.avg_price,
                    last_price=last_price,
                    invested_value=invested,
                    current_value=current,
                    unrealized_pnl=pnl,
                    unrealized_return_pct=((pnl / invested) * 100.0 if invested > 0 else None),
                )
            )

        txns_res = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.asc(), Transaction.id.asc())
        )
        all_txns = list(txns_res.scalars().all())
        _, realized_total, _ = self._build_running_state(all_txns)

        metrics: list[PortfolioPeriodMetricsOut] = []
        now = datetime.now(timezone.utc)
        for timeframe in Timeframe:
            start = now - timedelta(days=_TIMEFRAME_DAYS[timeframe])
            period_txns = [t for t in all_txns if self._ensure_utc(t.created_at) >= start]
            state, realized_pnl, buy_amount = self._build_running_state(period_txns)
            period_symbols = list(state.keys())
            period_prices = await self._get_latest_prices(db, period_symbols)
            unrealized_pnl = 0.0
            terminal_value = 0.0
            for sym, (qty, avg_cost) in state.items():
                if qty <= 0:
                    continue
                px = PRICE_CACHE.get(sym, period_prices.get(sym, avg_cost))
                unrealized_pnl += (px - avg_cost) * qty
                terminal_value += px * qty
            total_pnl = realized_pnl + unrealized_pnl
            total_return_pct = (total_pnl / buy_amount * 100.0) if buy_amount > 0 else None
            xirr = self._compute_xirr(period_txns, terminal_value, now)
            cagr = self._compute_cagr(
                start=start,
                end=now,
                invested=buy_amount,
                ending_value=(buy_amount + total_pnl),
            )
            metrics.append(
                PortfolioPeriodMetricsOut(
                    timeframe=timeframe,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=unrealized_pnl,
                    total_return_pct=total_return_pct,
                    xirr=xirr,
                    cagr=cagr,
                )
            )

        return PortfolioSummaryOut(
            user_id=user_id,
            realized_pnl_total=realized_total,
            unrealized_pnl_total=unrealized_pnl_total,
            holdings=holdings,
            period_metrics=metrics,
        )

    async def _get_latest_prices(self, db: AsyncSession, symbols: list[str]) -> dict[str, float]:
        if not symbols:
            return {}
        latest_subq = (
            select(PriceHistory.symbol, func.max(PriceHistory.timestamp).label("max_ts"))
            .where(PriceHistory.symbol.in_(symbols))
            .group_by(PriceHistory.symbol)
            .subquery()
        )
        query = (
            select(PriceHistory.symbol, PriceHistory.price)
            .join(
                latest_subq,
                and_(
                    PriceHistory.symbol == latest_subq.c.symbol,
                    PriceHistory.timestamp == latest_subq.c.max_ts,
                ),
            )
        )
        result = await db.execute(query)
        return {sym: price for sym, price in result.all()}

    def _build_running_state(
        self, txns: list[Transaction]
    ) -> tuple[dict[str, tuple[float, float]], float, float]:
        state: dict[str, tuple[float, float]] = {}
        realized_pnl = 0.0
        buy_amount = 0.0
        for t in txns:
            qty, avg = state.get(t.symbol, (0.0, 0.0))
            if t.type == TransactionSide.buy.value:
                total = avg * qty + t.price * t.quantity
                qty += t.quantity
                avg = total / qty if qty > 0 else 0.0
                buy_amount += t.price * t.quantity
            elif t.type == TransactionSide.sell.value:
                sell_qty = min(qty, t.quantity)
                realized_pnl += (t.price - avg) * sell_qty
                qty -= sell_qty
                if qty <= 1e-9:
                    qty = 0.0
                    avg = 0.0
            state[t.symbol] = (qty, avg)
        return state, realized_pnl, buy_amount

    def _compute_xirr(self, txns: list[Transaction], terminal_value: float, as_of: datetime) -> float | None:
        cashflows: list[tuple[datetime, float]] = []
        for t in txns:
            dt = self._ensure_utc(t.created_at)
            amt = -t.quantity * t.price if t.type == TransactionSide.buy.value else t.quantity * t.price
            cashflows.append((dt, amt))
        if terminal_value > 0:
            cashflows.append((as_of, terminal_value))
        if len(cashflows) < 2:
            return None
        first_date = min(d for d, _ in cashflows)
        if (as_of - first_date).days <= 0:
            return None

        def xnpv(rate: float) -> float:
            total = 0.0
            for dt, amount in cashflows:
                years = (dt - first_date).days / 365.25
                total += amount / ((1.0 + rate) ** years)
            return total

        rate = 0.1
        for _ in range(50):
            f = xnpv(rate)
            h = 1e-6
            deriv = (xnpv(rate + h) - f) / h
            if abs(deriv) < 1e-12:
                break
            new_rate = rate - (f / deriv)
            if new_rate <= -0.9999 or not math.isfinite(new_rate):
                break
            if abs(new_rate - rate) < 1e-7:
                return new_rate * 100.0
            rate = new_rate
        return None

    def _compute_cagr(
        self, start: datetime, end: datetime, invested: float, ending_value: float
    ) -> float | None:
        if invested <= 0 or ending_value <= 0:
            return None
        years = (end - start).days / 365.25
        # CAGR is meaningful for ~1Y+ windows; shorter windows rely on XIRR / return %.
        if years < 0.95:
            return None
        return (((ending_value / invested) ** (1 / years)) - 1) * 100.0

    def _ensure_utc(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
