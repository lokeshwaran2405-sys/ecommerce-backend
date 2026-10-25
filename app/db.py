import os
import sqlite3
from contextlib import contextmanager

from flask import current_app, g

_HERE = os.path.dirname(__file__)


def connect(path):
    """Open a SQLite connection in autocommit mode (transactions are explicit)."""
    conn = sqlite3.connect(path, isolation_level=None, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def run_script(conn, filename):
    with open(os.path.join(_HERE, filename), encoding="utf-8") as fh:
        conn.executescript(fh.read())


def init_db(path, with_indexes=True):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = connect(path)
    run_script(conn, "schema.sql")
    if with_indexes:
        run_script(conn, "indexes.sql")
    conn.close()


@contextmanager
def transaction(conn):
    """BEGIN IMMEDIATE takes the write lock up front so stock checks are race-free."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
