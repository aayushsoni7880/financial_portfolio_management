# create table
from app.core.config import settings
from app.core.database import SqlDatabase

db = SqlDatabase(db_path=settings.sqlite_path)

def drop_user_table():
    query  = """
        drop table users
    """
    db.execute(query)

def drop_refresh_token_table():
    query  = """
        drop table refresh_token
    """
    db.execute(query)

def truncate_table():
    query  = """
        truncate table users
    """
    db.execute(query)

def create_users_table():
    query = """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        password TEXT NOT NULL
    )
        """
    db.execute(query)

def create_refresh_token_table():
    # create table
    query = """
            CREATE TABLE IF NOT EXISTS refresh_token (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    jti TEXT NOT NULL,
    expire TEXT NOT NULL,
    is_revoked INTEGER DEFAULT 0
)
    """
    db.execute(query)

drop_refresh_token_table()
# create_users_table()
create_refresh_token_table()
# truncate_table()


