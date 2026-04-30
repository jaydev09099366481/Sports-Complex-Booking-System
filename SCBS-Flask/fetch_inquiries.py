from flask import Blueprint, jsonify, request
import sqlite3
import os

from history_logger import log_action  # ✅ history logging

fetch_inquiry = Blueprint('fetch_inquiry', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')


# ======================
# GET ALL INQUIRIES
# ======================
@fetch_inquiry.route('/get_inquiries')
def get_inquiries():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            name,
            email,
            message,
            remarks,
            status,
            created_at
        FROM inquiries
        ORDER BY id DESC
    """)

    data = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in data])


# ======================
# GET SINGLE INQUIRY + AUTO MARK READ + LOG VIEW
# ======================
@fetch_inquiry.route('/get_inquiry/<int:id>')
def get_inquiry(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get inquiry first (needed for logging name)
    cursor.execute("""
        SELECT id, name, email, message, remarks, status, created_at
        FROM inquiries
        WHERE id = ?
    """, (id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"})

    # Mark as READ
    cursor.execute("""
        UPDATE inquiries
        SET status = 'read'
        WHERE id = ?
    """, (id,))

    conn.commit()

    # LOG VIEW ACTION (human-readable)
    log_action(
        action="VIEW",
        table_name="inquiries",
        record_id=id,
        description=f"Admin viewed inquiry from '{row['name']}'"
    )

    conn.close()

    return jsonify(dict(row))


# ======================
# UPDATE REMARKS ONLY + LOG UPDATE
# ======================
@fetch_inquiry.route('/update_inquiry/<int:id>', methods=['POST'])
def update_inquiry(id):
    data = request.get_json()
    remarks = data.get('remarks')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get name for logging
    cursor.execute("SELECT name FROM inquiries WHERE id = ?", (id,))
    row = cursor.fetchone()
    name = row[0] if row else "Unknown"

    cursor.execute("""
        UPDATE inquiries
        SET remarks = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (remarks, id))

    conn.commit()
    conn.close()

    # LOG UPDATE ACTION
    log_action(
        action="UPDATE",
        table_name="inquiries",
        record_id=id,
        description=f"Admin updated inquiry from '{name}'"
    )

    return jsonify({"status": "success"})


# ======================
# DELETE INQUIRY + LOG DELETE
# ======================
@fetch_inquiry.route('/delete_inquiry/<int:id>', methods=['POST'])
def delete_inquiry(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get name before delete
    cursor.execute("SELECT name FROM inquiries WHERE id = ?", (id,))
    row = cursor.fetchone()
    name = row[0] if row else "Unknown"

    cursor.execute("DELETE FROM inquiries WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    # LOG DELETE ACTION
    log_action(
        action="DELETE",
        table_name="inquiries",
        record_id=id,
        description=f"Admin deleted inquiry from '{name}'"
    )

    return jsonify({"status": "success"})