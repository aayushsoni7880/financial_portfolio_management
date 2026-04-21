from datetime import datetime
from statistics import quantiles

from fastapi import HTTPException

from app.core.database import SqlDatabase
from app.core.config import settings
from app.schemas.schemas import TransactionOut, Users
from app.schemas.schemas import TransactionCreate, TransactionSide, \
    PortfolioHoldingOut, PositionOut

import logging
logger = logging.getLogger(__name__)

class portfolio_db_service(SqlDatabase):

    def __init__(self):
        super().__init__(db_path=settings.sqlite_path)

    def get_stocks_symbols(self):
        query = "select symbol from stocks"
        output = self.fetch_all(query)
        return output

    def list_stock(self):
        query  = "select symbol, name, sector, industry from stocks "
        output = self.fetch_all(query)
        return output

    def create_transactions(self, txn: TransactionCreate, user: Users):
        try:
            logger.info(f"UserId; {user.id}")
            user_id = user.id
            symbol = txn.symbol
            quantity = txn.quantity
            price = txn.price
            type = txn.type.value
            status = "failed"
            created_at = datetime.now()
            logger.info("Inserting trx to database")
            query = "insert into transactions (user_id, symbol, quantity, price, type, created_at) values (?, ?, ?, ?, ?, ?)" # default status
            trx_id = self.execute(query, (user_id, symbol, quantity, price, type, created_at))


            # return output
            query = "select * from positions where user_id=? and symbol=?"
            logger.info("Fetching exisxting holdings")
            pos = self.fetch_all(query, (user_id, symbol))
            logger.info(pos)
            if not pos:
                logger.info("No Holding Exist, Createing new entry")
                if type == TransactionSide.buy.value:
                    query = "insert into positions (user_id, symbol, quantity, avg_price) values (?, ?, ?, ?)"
                    self.execute(query, (user_id, symbol, quantity, price))

                    # udpate transactiont able status == Success
                else:
                    logger.info("Insufficient Holding for this")
                    raise HTTPException(status_code=400, detail="Insufficient holdings for this sale")

            for id, userid, sym, quantities, avg_price in pos:

                if type == TransactionSide.buy.value:
                    quantities += quantity
                    total_price = quantities * avg_price + quantity * price
                    avg_price = total_price / quantities
                    query = "update positions set quantity=?, avg_price=? where symbol=? and user_id=?"
                    output = self.execute(query, (quantities, avg_price, sym, userid))
                else:
                    if quantities < quantity:
                        raise HTTPException(status_code=400, detail="Insufficient holdings for this sale")

                    quantities -= quantity
                    if quantities==0:
                        query = "delete from positions where symbol=? and user_id=?"
                        self.execute(query, (symbol, user_id))
                    else:
                        query = "update positions set quantity=? where symbol=? and user_id=?"
                        self.execute(query, (quantities, symbol, user_id))

                # Udpate status to success
            logger.info("Transaction succesfull")
            return TransactionOut(
                id=trx_id,
                user_id=user_id,
                symbol = txn.symbol,
                quantity = txn.quantity,
                price = txn.price,
                type = txn.type.value,
                created_at = created_at
            )
        except HTTPException as err:
            logger.error(f"Transaction failed, Error: {err}")
            raise HTTPException(status_code=400, detail="Insufficient holdings for this sale")
        except Exception as err:
            raise HTTPException(status_code=400, detail=err)




    def get_user_trx(self, user_id: int):
        query = "select id, user_id, symbol, quantity, price, type, created_at from transactions where user_id=?"
        output = self.fetch_all(query, (user_id,))
        return output

    def get_portfolio_summary(self, user_id: int):

        from app.workers.price_worker import PRICE_CACHE # local import
        query = "select * from positions where user_id=?"
        pos = self.fetch_all(query, (user_id,))
        holdings: list[PortfolioHoldingOut] = []

        if pos is None:
            return holdings

        for id, user_id, symbol, quantity, avg_price  in pos:
            last_price = PRICE_CACHE.get(symbol, 0)

            invested = avg_price * quantity
            current = quantity * last_price

            unrealized_pnl = current - invested
            unrealized_return_pct = ((unrealized_pnl / invested) * 100.0 if invested > 0 else None)

            holdings.append(
                PortfolioHoldingOut(
                    symbol=symbol,
                    quantity=quantity,
                    avg_price=avg_price,
                    last_price=last_price,
                    invested_value=invested,
                    current_value=current,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_return_pct=unrealized_return_pct,
                )
            )

        return holdings


    def get_user_positions(self, user_id):
        from app.workers.price_worker import PRICE_CACHE  # local import
        query = "select * from positions where user_id=?"
        pos = self.fetch_all(query, (user_id,))
        positions: list[PositionOut] = []
        for id, user_id, symbol, quantity, avg_price  in pos:
            last_price = PRICE_CACHE.get(symbol, 0) # Problem
            positions.append(
                PositionOut(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                last_price=last_price
            )
            )
        return positions


















