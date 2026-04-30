from flask import Blueprint, jsonify, request
import sqlite3
import os
import time
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename  # ✅ FIX: MISSING IMPORT
from history_logger import log_action

# Create Blueprint
fetch_user = Blueprint('fetch_user', __name__)

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# ✅ FIX: CORRECT ABSOLUTE UPLOAD PATH
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'profiles')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password', '123456')
    phone = request.form.get('phone')
    address = request.form.get('address')
    role = request.form.get('role', 'user')
    status = request.form.get('status', 'active')

    file = request.files.get('profile_image')

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        profile_image = f"/static/uploads/profiles/{filename}"
    else:
        profile_image = "/static/uploads/profiles/default.png"

    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users 
            (name, email, password, phone, address, role, status, profile_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            phone,
            address,
            role,
            status,
            profile_image
        ))

        conn.commit()
        user_id = cursor.lastrowid

        log_action(
            action="CREATE",
            table_name="users",
            record_id=user_id,
            description=f"Admin added user '{name}'"
        )

    except sqlite3.IntegrityError:
        return jsonify({
            "status": "error",
            "message": "Email already exists"
        })

    finally:
        conn.close()

    return jsonify({
        "status": "success",
        "message": "User created successfully"
    })


# ======================
# UPDATE USER (FIXED FILE UPLOAD)
# ======================
@fetch_user.route('/update_user/<int:id>', methods=['POST'])
def update_user(id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    role = request.form.get('role')
    status = request.form.get('status')

    file = request.files.get('profile_image')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ✅ Get existing image (to keep if no new upload)
    cursor.execute("SELECT profile_image FROM users WHERE id=?", (id,))
    old_user = cursor.fetchone()

    profile_image = old_user[0] if old_user else "/static/uploads/profiles/default.png"

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filename = f"{int(time.time())}_{filename}"

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        profile_image = f"/static/uploads/profiles/{filename}"

    cursor.execute("""
        UPDATE users 
        SET name=?, email=?, phone=?, address=?, role=?, status=?, profile_image=?
        WHERE id=?
    """, (name, email, phone, address, role, status, profile_image, id))

    conn.commit()
    conn.close()

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

    cursor.execute("SELECT name FROM users WHERE id=?", (id,))
    user = cursor.fetchone()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    log_action(
        action="DELETE",
        table_name="users",
        record_id=id,
        description=f"Admin deleted user '{user[0] if user else 'Unknown'}'"
    )

    return jsonify({"status": "success", "message": "User deleted successfully"})