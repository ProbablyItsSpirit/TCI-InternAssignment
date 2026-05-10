import sqlite3

DB_NAME = "logs.db"

def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        invoice_no TEXT,
        stage TEXT,
        subject TEXT,
        body TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def log_email(
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
        client_name,
        invoice_no,
        stage,
        subject,
        body,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
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