import sqlite3
from config import DB_NAME

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