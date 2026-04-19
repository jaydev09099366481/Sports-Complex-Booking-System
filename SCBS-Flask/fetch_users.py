from flask import Blueprint, jsonify
import sqlite3
import os

# Create Blueprint
fetch_user = Blueprint('fetch_user', __name__)

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# ======================
# GET ALL USERS
# ======================
@fetch_user.route('/get_users')
def get_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

    conn.close()

    return jsonify([dict(user) for user in users])


# ======================
# GET SINGLE USER
# ======================
@fetch_user.route('/get_user/<int:id>')
def get_user(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id=?", (id,))
    user = cursor.fetchone()

    conn.close()

    if user:
        return jsonify(dict(user))
    return jsonify({"error": "User not found"})


# ======================
# UPDATE USER
# ======================
@fetch_user.route('/update_user/<int:id>', methods=['POST'])
def update_user(id):
    from flask import request

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET name=?, email=? WHERE id=?",
        (name, email, id)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ======================
# DELETE USER
# ======================
@fetch_user.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})