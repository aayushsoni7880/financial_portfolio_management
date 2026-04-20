from fastapi import APIRouter
from app.services.endpoints import PortfolioEndpoints
from app.schemas.schemas import StockOut, TransactionOut, TransactionCreate, \
    PortfolioSummaryOut, PortfolioHoldingOut, PositionOut

router = APIRouter()

router.add_api_route(
    "/stocks",
    PortfolioEndpoints.list_stock,
    methods=["GET"],
    response_model=list[StockOut]
)

router.add_api_route(
    "/transactions",
    PortfolioEndpoints.transactions,
    methods=["POST"],
    response_model=TransactionOut
)

router.add_api_route(
    "/transactions",
    PortfolioEndpoints.get_user_transactions_details,
    methods=["GET"],
    response_model=list[TransactionOut]
)

router.add_api_route(
    "/positions",
    PortfolioEndpoints.get_user_positions,
    methods=["GET"],
    response_model=list[PositionOut]
)

router.add_api_route(
    "/portfolio/summary",
    PortfolioEndpoints.get_portfolio_summary,
    methods=["GET"],
    response_model=list[PortfolioHoldingOut] #PortfolioSummaryOut
)