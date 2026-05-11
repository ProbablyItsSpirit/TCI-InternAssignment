import sqlite3
from datetime import date, datetime

DB_NAME = "logs.db"


def _connect():
    return sqlite3.connect(DB_NAME)


def _ensure_columns():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(invoices)")
    cols = [r[1] for r in cur.fetchall()]

    if "next_followup_date" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN next_followup_date TEXT")
    if "last_email_sent" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN last_email_sent TEXT")
    if "followup_frequency_days" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN followup_frequency_days INTEGER")
    if "last_status" not in cols:
        cur.execute("ALTER TABLE invoices ADD COLUMN last_status TEXT")

    conn.commit()
    conn.close()


def should_send_followup(next_followup_date):
    if not next_followup_date:
        return True

    try:
        nf = datetime.strptime(next_followup_date, "%Y-%m-%d").date()
    except Exception:
        return True

    return date.today() >= nf


def update_last_email_sent(invoice_no):
    _ensure_columns()
    conn = _connect()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "UPDATE invoices SET last_email_sent = ? WHERE invoice_no = ?",
        (now, invoice_no)
    )
    conn.commit()
    conn.close()


def update_next_followup(invoice_no, next_followup_date, mail_frequency=None):
    _ensure_columns()
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE invoices SET next_followup_date = ?, followup_frequency_days = ? WHERE invoice_no = ?",
        (next_followup_date, mail_frequency, invoice_no)
    )
    conn.commit()
    conn.close()


def increment_followup_count(invoice_no):
    _ensure_columns()
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE invoices SET follow_up_count = COALESCE(follow_up_count, 0) + 1 WHERE invoice_no = ?",
        (invoice_no,)
    )
    conn.commit()
    conn.close()


def update_invoice_status(invoice_no, status):
    _ensure_columns()
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE invoices SET last_status = ? WHERE invoice_no = ?",
        (status, invoice_no)
    )
    conn.commit()
    conn.close()
