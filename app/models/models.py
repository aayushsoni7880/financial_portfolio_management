from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Stock(Base):
    __tablename__ = "stocks"

    symbol = Column(String(32), primary_key=True)
    name = Column(String(256), nullable=False)
    sector = Column(String(128), nullable=True)
    industry = Column(String(256), nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(32), ForeignKey("stocks.symbol", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String(8), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_position_user_symbol"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(32), ForeignKey("stocks.symbol", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), ForeignKey("stocks.symbol", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)
