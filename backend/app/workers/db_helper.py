import queue
import threading
import sqlite3

from app.core.config import settings

write_queue = queue.Queue()

def db_writer():
    conn = sqlite3.connect(settings.sqlite_path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")

    while True:
        query, params = write_queue.get()
        try:
            print("Executing workers queries")
            conn.execute(query, params)
            conn.commit()
        finally:
            print(f"All Workers queries get executed.")
            write_queue.task_done()

def update_price_details(sym, price):

    query = "update stocks set price=? where symbol=?"
    write_queue.put((
        query,
        (price, sym)
    ))

threading.Thread(target=db_writer, daemon=True).start()