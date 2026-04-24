from curl_cffi.requests.utils import quote_path_and_params

from app.services.auth_services import AuthService
from app.services.db_service import portfolio_db_service
from fastapi import Depends
from app.schemas.schemas import TransactionCreate, StockOut, TransactionOut, ChangePasswordOut, ChangePassword

import logging
logger = logging.getLogger(__name__)

class PortfolioEndpoints:

    @staticmethod
    def list_stock():
        logger.info("Listing all stocks")
        service = portfolio_db_service()
        result = service.list_stock()
        stocks: list[StockOut] = []
        for sym, name, sector, industry in result:
            res = StockOut(
                symbol=sym,
                name=name,
                sector=sector,
                industry=industry
            )
            stocks.append(res)
        return stocks

    @staticmethod
    def transactions(trx: TransactionCreate, user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        result = service.create_transactions(trx, user)
        return result

    @staticmethod
    def get_user_transactions_details(user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        result = service.get_user_trx(user.id)

        transactions: list[TransactionOut] = []
        for id, user_id, symbol, quantity, price, type, created_at in result:
            obj = TransactionOut(
                id=id,
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                price=price,
                type=type,
                created_at=created_at
            )
            transactions.append(obj)
        return transactions

    @staticmethod
    def get_user_positions(user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        positions = service.get_user_positions(user.id)
        return positions

    @staticmethod
    def get_portfolio_summary(user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        holding = service.get_portfolio_summary(user.id)
        return holding

    @staticmethod
    def get_latest_price(symbol: str, user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        result = service.get_price(symbol)
        logger.info(result.price)
        return result

    @staticmethod
    def change_password(request: ChangePassword, user = Depends(AuthService.get_current_user)):
        service = portfolio_db_service()
        result = service.change_password(user.id,  request.current_password, request.new_password)
        if result:
            return ChangePasswordOut(message="Password Change successfully.")
        return result
