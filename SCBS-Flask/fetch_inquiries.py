from flask import Blueprint, jsonify, request
import sqlite3
import os

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

    cursor.execute("SELECT * FROM inquiries")
    data = cursor.fetchall()

    conn.close()

    return jsonify([dict(row) for row in data])


# ======================
# GET SINGLE INQUIRY
# ======================
@fetch_inquiry.route('/get_inquiry/<int:id>')
def get_inquiry(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM inquiries WHERE id=?", (id,))
    row = cursor.fetchone()

    conn.close()

    return jsonify(dict(row)) if row else jsonify({"error": "Not found"})


# ======================
# UPDATE INQUIRY
# ======================
@fetch_inquiry.route('/update_inquiry/<int:id>', methods=['POST'])
def update_inquiry(id):
    data = request.get_json()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE inquiries
        SET name=?, email=?, message=?
        WHERE id=?
    """, (data['name'], data['email'], data['message'], id))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ======================
# DELETE INQUIRY
# ======================
@fetch_inquiry.route('/delete_inquiry/<int:id>', methods=['POST'])
def delete_inquiry(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM inquiries WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})