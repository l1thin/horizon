# AntiGravity - database.py - owned by Dev 2 (Backend)
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "candidates.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = f.read()
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

def get_db():
    init_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
