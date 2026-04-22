import os
import sqlite3
from flask import Blueprint, jsonify

fetch_categories = Blueprint('fetch_categories', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
conn = sqlite3.connect(os.path.join(BASE_DIR, 'database.db'), check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ======================
# FETCH ALL CATEGORIES
# ======================
@fetch_categories.route('/get_categories')
def get_categories():
    cursor.execute("SELECT * FROM categories")
    data = cursor.fetchall()

    categories = [dict(row) for row in data]

    return jsonify(categories)