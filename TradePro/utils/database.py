import sqlite3
import pandas as pd

DB_FILE = "data/trading_journal.db"

def init_db():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        ticker TEXT,
        action TEXT,
        price REAL,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_journal(
    date,
    ticker,
    action,
    price,
    notes
):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO journal
        (
        date,
        ticker,
        action,
        price,
        notes
        )
        VALUES (?,?,?,?,?)
        """,
        (
            date,
            ticker,
            action,
            price,
            notes
        )
    )

    conn.commit()
    conn.close()


def get_journal():

    conn = sqlite3.connect(DB_FILE)

    df = pd.read_sql(
        "SELECT * FROM journal ORDER BY id DESC",
        conn
    )

    conn.close()

    return df
