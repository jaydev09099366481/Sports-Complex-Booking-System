import os
import sqlite3
from flask import Blueprint, jsonify

fetch_categories = Blueprint('fetch_categories', __name__)

DB_NAME = os.path.join(os.getcwd(), "database.db")

@fetch_categories.route('/get_categories')
def get_categories():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            name,
            description,
            status
        FROM categories
        ORDER BY id ASC
    """)

    data = cursor.fetchall()   # ✅ FIX: fetch the data

    conn.close()

    return jsonify([dict(row) for row in data])  # ✅ FIX: use data