import logging
import sqlite3

from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def conn_sqlite(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

    with conn_sqlite(sqlite_conn_path) as conn:
        curs: sqlite3.Cursor = conn.cursor()
        curs.execute(f"SELECT * FROM {table_name};")
