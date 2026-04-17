from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Position, Stock, Transaction, User
from app.schemas.schemas import (
    PortfolioSummaryOut,
    PositionOut,
    StockCreate,
    StockOut,
    TransactionCreate,
    TransactionOut,
    UserCreate,
    UserOut,
)
from app.services.live_updates import websocket_prices
from app.services.portfolio_service import PortfolioService
from app.workers.price_worker import PRICE_CACHE

router = APIRouter()
portfolio_service = PortfolioService()


@router.post("/users", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    exists = await db.execute(select(User).where(User.email == user.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already exists")
    row = User(name=user.name, email=user.email)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[User]:
    result = await db.execute(select(User).order_by(User.id.asc()))
    return list(result.scalars().all())


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@router.post("/stocks", response_model=StockOut)
async def add_stock(stock: StockCreate, db: AsyncSession = Depends(get_db)) -> Stock:
    existing = await db.execute(select(Stock).where(Stock.symbol == stock.symbol))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Stock already registered")
    row = Stock(
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        industry=stock.industry,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/stocks", response_model=list[StockOut])
async def list_stocks(db: AsyncSession = Depends(get_db)) -> list[Stock]:
    result = await db.execute(select(Stock).order_by(Stock.symbol))
    return list(result.scalars().all())


@router.post("/transactions", response_model=TransactionOut)
async def create_transaction(
    txn: TransactionCreate, db: AsyncSession = Depends(get_db)
) -> Transaction:
    return await portfolio_service.create_transaction(db, txn)


@router.get("/transactions/{user_id}", response_model=list[TransactionOut])
async def list_transactions(user_id: int, db: AsyncSession = Depends(get_db)) -> list[Transaction]:
    await portfolio_service.require_user(db, user_id)
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/positions/{user_id}", response_model=list[PositionOut])
async def positions(user_id: int, db: AsyncSession = Depends(get_db)) -> list[PositionOut]:
    await portfolio_service.require_user(db, user_id)
    result = await db.execute(select(Position).where(Position.user_id == user_id))
    rows = result.scalars().all()
    return [
        PositionOut(
            symbol=p.symbol,
            quantity=p.quantity,
            avg_price=p.avg_price,
            last_price=PRICE_CACHE.get(p.symbol),
        )
        for p in rows
    ]


@router.get("/portfolio/{user_id}/summary", response_model=PortfolioSummaryOut)
async def portfolio_summary(user_id: int, db: AsyncSession = Depends(get_db)) -> PortfolioSummaryOut:
    return await portfolio_service.get_portfolio_summary(db, user_id)


@router.websocket("/ws/prices")
async def prices_ws(websocket: WebSocket) -> None:
    await websocket_prices(websocket)
