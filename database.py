import sqlite3
from contextlib import closing

DB_FILE = "trading.db"

def init_db():
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        # جدول سیگنال‌ها
        c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            direction TEXT,
            score REAL,
            entry REAL,
            sl REAL,
            tp1 REAL,
            tp2 REAL,
            delta REAL,
            consolidation INTEGER,
            stop_hunt INTEGER,
            false_breakout INTEGER,
            macro_score REAL,
            session TEXT,
            kill_zone TEXT
        )
        """)
        # جدول PnL
        c.execute("""
        CREATE TABLE IF NOT EXISTS pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            exit_price REAL,
            pnl REAL,
            status TEXT,
            FOREIGN KEY(signal_id) REFERENCES signals(id)
        )
        """)
        # جدول وزن‌دهی خودکار
        c.execute("""
        CREATE TABLE IF NOT EXISTS score_weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            weight REAL
        )
        """)
        conn.commit()

def execute(query, params=()):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.lastrowid

def fetchall(query, params=()):
    with closing(sqlite3.connect(DB_FILE)) as conn:
        c = conn.cursor()
        c.execute(query, params)
        return c.fetchall()
