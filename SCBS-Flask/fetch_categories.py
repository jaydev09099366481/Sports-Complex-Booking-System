import os
import sqlite3
from flask import Blueprint, request, jsonify
from config import DB_NAME
from history_logger import log_action

fetch_categories = Blueprint('categories', __name__)


# ======================
# GET ALL CATEGORIES
# ======================
@fetch_categories.route('/get_categories')
def get_categories():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, description, status
        FROM categories
        ORDER BY id ASC
    """)

    data = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in data])


# ======================
# CREATE CATEGORY
# ======================
@fetch_categories.route('/create_category', methods=['POST'])
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
        conn.close()

        log_action(
            action="CREATE",
            table_name="categories",
            record_id=category_id,
            description=f"Added category '{name}'"
        )

        return jsonify({"message": "Category created successfully!"})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ======================
# UPDATE CATEGORY
# ======================
@fetch_categories.route('/update_category/<int:id>', methods=['POST'])
def update_category(id):
    data = request.get_json()

    name = data.get('name')
    description = data.get('description')
    status = data.get('status')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE categories
        SET name=?, description=?, status=?
        WHERE id=?
    """, (name, description, status, id))

    conn.commit()
    conn.close()

    log_action(
        action="UPDATE",
        table_name="categories",
        record_id=id,
        description=f"Updated category '{name}'"
    )

    return jsonify({"message": "Category updated successfully!"})


# ======================
# DELETE CATEGORY
# ======================
@fetch_categories.route('/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM categories WHERE id=?", (id,))
    cat = cursor.fetchone()

    cursor.execute("DELETE FROM categories WHERE id=?", (id,))
    conn.commit()
    conn.close()

    log_action(
        action="DELETE",
        table_name="categories",
        record_id=id,
        description=f"Deleted category '{cat[0] if cat else 'Unknown'}'"
    )

    return jsonify({"message": "Category deleted successfully!"})