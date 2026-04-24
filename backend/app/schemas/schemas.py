from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# from app.services.stock_validation import validate_nse_symbol


class TransactionSide(str, Enum):
    buy = "buy"
    sell = "sell"


class Timeframe(str, Enum):
    d1 = "1d"
    w1 = "1w"
    m1 = "1m"
    m3 = "3m"
    m6 = "6m"
    y1 = "1y"
    y3 = "3y"
    y5 = "5y"


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    email: str = Field(..., min_length=5, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


class StockCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=256)
    sector: str | None = Field(None, max_length=128)
    industry: str | None = Field(None, max_length=256)

    # @field_validator("symbol")
    # @classmethod
    # def normalize_symbol(cls, v: str) -> str:
    #     return validate_nse_symbol(v)


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    sector: str | None = None
    industry: str | None = None


class TransactionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    type: TransactionSide

    # @field_validator("symbol")
    # @classmethod
    # def normalize_and_validate_symbol(cls, v: str) -> str:
    #     return validate_nse_symbol(v)

class ChangePassword(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_password: str
    new_password: str


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    symbol: str
    quantity: float
    price: float
    type: str
    created_at: datetime


class PositionOut(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    last_price: float | None


class PortfolioHoldingOut(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    last_price: float
    invested_value: float
    current_value: float
    unrealized_pnl: float
    unrealized_return_pct: float | None

class PriceOut(BaseModel):
    price: float | None

class ChangePasswordOut(BaseModel):
    message: str | None


class PortfolioPeriodMetricsOut(BaseModel):
    timeframe: Timeframe
    realized_pnl: float
    unrealized_pnl: float
    total_return_pct: float | None
    xirr: float | None
    cagr: float | None


class PortfolioSummaryOut(BaseModel):
    user_id: int
    realized_pnl_total: float
    unrealized_pnl_total: float
    holdings: list[PortfolioHoldingOut]
    period_metrics: list[PortfolioPeriodMetricsOut]


# Auth Service

class LoginDetails(BaseModel):
    user_name: str
    password: str

class SignUpDetails(BaseModel):
    user_name: str
    email_address: str
    password: str

class ResetPasswordDetails(BaseModel):
    email_address: str


class RefreshToken(BaseModel):
    refresh_token: str


class AuthServiceFailedResponse(BaseModel):
    error_message: str
    user_name: str

class AuthServiceResponseModel(BaseModel):
    success: bool
    message: Optional[str] = None
    id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class Users(BaseModel):
    id: Optional[int] = None
    user_name: Optional[str] = None
    email_address: Optional[str] = None
    password: Optional[str] = None


class TokenData(BaseModel):
    username: str | None = None
    userid: int | None = None

class MailHandlerResponse(BaseModel):
    success: bool
    code: int
    status: str
    error_message: str = None


class MailHandlerRequest(BaseModel):
    message: str
    receiver_email_address: str