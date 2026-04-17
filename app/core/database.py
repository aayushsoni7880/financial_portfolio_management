import sqlite3
from abc import abstractmethod, ABC

class Database(ABC):
    @abstractmethod
    def __init__(self, db_path):
        pass

    @abstractmethod
    def fetch_all(self, query, params=()):
        pass

    @abstractmethod
    def fetch_one(self, query, params=()):
        pass

    @abstractmethod
    def execute(self, query, params=()):
        pass



class SqlDatabase(Database):

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def fetch_all(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params = ()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()


class MongoDb(Database):
    pass
