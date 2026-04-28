from flask import Blueprint, jsonify, request
import sqlite3
import os
from werkzeug.security import generate_password_hash
from history_logger import log_action   # ✅ IMPORT LOGGER

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

    cursor.execute("""
        SELECT 
            id, 
            name, 
            email, 
            phone,
            address,
            role,
            status,
            profile_image,
            date_created
        FROM users
        ORDER BY id DESC
    """)

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
# CREATE USER
# ======================
@fetch_user.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password', '123456')
    phone = data.get('phone')
    address = data.get('address')
    role = data.get('role', 'user')
    status = data.get('status', 'active')
    profile_image = data.get('profile_image', '/static/default.png')

    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users 
            (name, email, password, phone, address, role, status, profile_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, hashed_password, phone, address, role, status, profile_image))

        conn.commit()

    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Email already exists"})

    finally:
        
        user_id = cursor.lastrowid
        # ✅ LOG THE ACTION
        log_action(
            action="CREATE",
            table_name="users",
            record_id=user_id,
            description=f"Admin added user '{name}'"
        )

        conn.close()

    return jsonify({"status": "success", "message": "User created successfully"})

# ======================
# UPDATE USER
# ======================
@fetch_user.route('/update_user/<int:id>', methods=['POST'])
def update_user(id):
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    role = data.get('role')
    status = data.get('status')
    profile_image = data.get('profile_image')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users 
        SET name=?, email=?, phone=?, address=?, role=?, status=?, profile_image=?
        WHERE id=?
    """, (name, email, phone, address, role, status, profile_image, id))

    conn.commit()
    conn.close()

    # ✅ LOG THE ACTION
    log_action(
        action="UPDATE",
        table_name="users",
        record_id=id,
        description=f"Admin updated user '{name}'"
    )

    return jsonify({"status": "success", "message": "User updated successfully"})


# ======================
# DELETE USER
# ======================
@fetch_user.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ✅ get user first
    cursor.execute("SELECT name FROM users WHERE id=?", (id,))
    user = cursor.fetchone()

    # delete user
    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    # log action
    log_action(
        action="DELETE",
        table_name="users",
        record_id=id,
        description=f"Admin deleted user '{user[0] if user else 'Unknown'}'"
    )

    return jsonify({"status": "success", "message": "User deleted successfully"})