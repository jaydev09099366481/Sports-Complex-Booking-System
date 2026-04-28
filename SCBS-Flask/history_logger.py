import sqlite3
from config import DB_NAME
from datetime import datetime

def format_logs(logs):
    formatted = []

    for log in logs:
        dt = datetime.strptime(log["created_at"], "%Y-%m-%d %H:%M:%S")

        log["date"] = dt.strftime("%B %d, %Y")   # April 29, 2026
        log["time"] = dt.strftime("%I:%M %p")    # 01:40 AM

        formatted.append(log)

    return formatted

def log_action(action, table_name, record_id=None, description=None):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO history_log (action, table_name, record_id, description)
            VALUES (?, ?, ?, ?)
        """, (action, table_name, record_id, description))

        conn.commit()
        conn.close()

    except Exception as e:
        print("History Log Error:", e)