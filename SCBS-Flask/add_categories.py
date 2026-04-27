from flask import Blueprint, request, jsonify
import sqlite3
from config import DB_NAME
from history_logger import log_action   # ✅ IMPORT LOGGER

add_categories = Blueprint('add_categories', __name__)

@add_categories.route('/create_category', methods=['POST'])
def create_category():
    try:
        data = request.get_json()

        name = data.get('name')
        description = data.get('description')
        status = data.get('status', 'Available')

        if not name or name.strip() == "":
            return jsonify({"message": "Category name is required"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO categories (name, description, status)
            VALUES (?, ?, ?)
        """, (name, description, status))

        conn.commit()
        category_id = cursor.lastrowid

        # ✅ LOG THE ACTION
        log_action(
            action="CREATE",
            table_name="categories",
            record_id=category_id,
            description=f"Created category '{name}'"
        )

        conn.close()

        return jsonify({
            "message": "Category created successfully!",
            "id": category_id
        })

    except Exception as e:
        return jsonify({"message": str(e)}), 500