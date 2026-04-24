import sqlite3
from abc import abstractmethod, ABC
from app.schemas.schemas import Users
import logging
logger = logging.getLogger(__name__)


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
        self.conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")

    def fetch_all(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()  # ❌ no commit

    def fetch_one(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()  # ❌ no commit

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid

    def get_user_by_id(self, user_id: int):
        query = """
            select id, user_name, user_email, password from users where id=?
        """
        user_details = self.fetch_one(query, (user_id,))
        if user_details:
           return Users(id=user_details[0], user_name=user_details[1], email_address=user_details[2], password=user_details[3])
        else:
            return Users()

    def get_user_by_name(self, user_name: str):
        query = """
            select id, user_name, user_email, password from users where user_name=?
        """
        user_details = self.fetch_one(query, (user_name,))
        logger.info(user_details)
        if user_details:
           return Users(id=user_details[0], user_name=user_details[1], email_address=user_details[2], password=user_details[3])
        else:
            return None

    def get_user_by_email(self, email_address: str):
        query = """
            select id, user_name, user_email, password from users where user_email=?
        """
        user_details = self.fetch_one(query, (email_address,))
        logger.info(user_details)
        if user_details:
           return Users(id=user_details[0], user_name=user_details[1], email_address=user_details[2], password=user_details[3])
        else:
            return None

    def insert_user(self, user_name: str, password, email_address):
        print("Inside Insert User")
        query = """
            INSERT INTO users (user_name, user_email, password)
            VALUES (?, ?, ?)
        """
        user_id = self.execute(query, (user_name, email_address, password))
        return user_id

    def reset_password(self, email_address: str, password: str):
        # update new password in database
        query = """
            update users set password=? where user_email=?
        """

        self.execute(query, (password, email_address))

    def get_token_from_db(self, jti: str):
        query = """
            select user_id, is_revoked from refresh_token where jti=?
        """
        response = self.fetch_one(query, (jti, ))
        if response:
            return response[0], response[1]
        return None, None

    def save_refresh_token(self, data: dict):
        print(data)
        user_id  = data["id"]
        type = data["type"]
        expire = data["exp"]
        jti = data["jti"]

        query = """
            insert into refresh_token (user_id, type, jti, expire) values (?, ?, ?, ?)
        """
        self.execute(query, (user_id, type, jti, expire))
        return

    def revoke_refresh_token(self, jti: str):
        query = """
            update refresh_token set is_revoked=1 where jti=?
        """
        response = self.execute(query, (jti, ))

class MongoDb(Database):
    pass
