from app.core.database import SqlDatabase
from app.core.config import settings

class portfolio_db_service(SqlDatabase):

    def __init__(self):
        super().__init__(db_path=settings.sqlite_path)

    def get_stocks_symbols(self):
        query = "select symbols from stocks"
        output = self.fetch_all(query)
        return output

    def update_price_details(self, sym, price):
        query = "update price_history set price=%s where symbol=%s"
        output = self.fetch_one(query, (sym, price))
        return output


