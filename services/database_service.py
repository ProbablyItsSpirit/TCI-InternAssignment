import sqlite3
from pathlib import Path

import pandas as pd

DB_NAME = "logs.db"


def _get_csv_path():

    return Path(__file__).resolve().parent.parent / "invoices.csv"

def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        client_name TEXT,
        invoice_no TEXT,
        stage TEXT,
        subject TEXT,
        body TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_no TEXT PRIMARY KEY,
        client_name TEXT,
        amount INTEGER,
        due_date TEXT,
        contact_email TEXT,
        follow_up_count INTEGER,
        payment_link TEXT
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM invoices")
    invoice_count = cursor.fetchone()[0]

    if invoice_count == 0:

        csv_path = _get_csv_path()

        if csv_path.exists():

            invoices_df = pd.read_csv(csv_path)

            invoices_df.to_sql(
                "invoices",
                conn,
                if_exists="append",
                index=False
            )

    conn.commit()
    conn.close()


def fetch_invoices():

    conn = sqlite3.connect(DB_NAME)

    try:

        return pd.read_sql_query(
            """
            SELECT invoice_no, client_name, amount, due_date, contact_email,
                   follow_up_count, payment_link
            FROM invoices
            ORDER BY invoice_no
            """,
            conn
        )

    finally:

        conn.close()


def log_email(
    session_id,
    client_name,
    invoice_no,
    stage,
    subject,
    body,
    status
):
    

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO email_logs (
        session_id,
        client_name,
        invoice_no,
        stage,
        subject,
        body,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        client_name,
        invoice_no,
        stage,
        subject,
        body,
        status
    ))

    conn.commit()
    conn.close()


def fetch_logs():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM email_logs
    ORDER BY timestamp DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows