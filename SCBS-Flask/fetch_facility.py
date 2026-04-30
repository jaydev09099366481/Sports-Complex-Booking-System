import os
import sqlite3
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from config import DB_NAME
from history_logger import log_action

fetch_facility = Blueprint('fetch_facility', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# ✅ UPLOAD FOLDER
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads/facilities')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ======================
# FETCH PAGE + DATA
# ======================
@fetch_facility.route('/facilities')
def facilities():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            f.id,
            f.date_created,
            f.name,
            f.description,
            f.image,
            f.capacity,
            f.price_per_hour,
            f.status,
            c.name AS category_name
        FROM facilities f
        LEFT JOIN categories c ON f.category_id = c.id
        ORDER BY f.id ASC
    """)

    data = cursor.fetchall()

    cursor.execute("SELECT id, name FROM categories WHERE status='Available'")
    categories = cursor.fetchall()

    conn.close()

    return render_template(
        'admin/facilities.html',
        facilities=data,
        categories=categories,
        active_page='facilities'
    )


# ======================
# CREATE FACILITY (UPDATED)
# ======================
@fetch_facility.route('/create_facility', methods=['POST'])
def create_facility():
    try:
        # ✅ GET FORM DATA
        category_id = request.form.get('category_id')
        name = request.form.get('name')
        description = request.form.get('description')
        capacity = request.form.get('capacity')
        price = request.form.get('price_per_hour')
        status = request.form.get('status', 'Available')

        # ✅ HANDLE IMAGE
        file = request.files.get('image')
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO facilities 
            (category_id, name, description, image, capacity, price_per_hour, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            category_id,
            name,
            description,
            filename,
            capacity,
            price,
            status
        ))

        conn.commit()
        facility_id = cursor.lastrowid

        log_action(
            action="CREATE",
            table_name="facilities",
            record_id=facility_id,
            description=f"Added facility '{name}'"
        )

        conn.close()

        return jsonify({"message": "Facility created successfully"})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ======================
# GET SINGLE FACILITY
# ======================
@fetch_facility.route('/get_facility/<int:id>')
def get_facility(id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM facilities WHERE id=?", (id,))
    row = cursor.fetchone()

    conn.close()

    return jsonify(dict(row)) if row else jsonify({"error": "Not found"})


# ======================
# UPDATE FACILITY (UPDATED)
# ======================
@fetch_facility.route('/update_facility/<int:id>', methods=['POST'])
def update_facility(id):
    try:
        category_id = request.form.get('category_id')
        name = request.form.get('name')
        description = request.form.get('description')
        capacity = request.form.get('capacity')
        price = request.form.get('price_per_hour')
        status = request.form.get('status')

        file = request.files.get('image')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # ✅ GET OLD IMAGE
        cursor.execute("SELECT image FROM facilities WHERE id=?", (id,))
        old = cursor.fetchone()
        old_image = old[0] if old else None

        filename = old_image

        # ✅ IF NEW IMAGE UPLOADED
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        cursor.execute("""
            UPDATE facilities
            SET category_id=?,
                name=?,
                description=?,
                image=?,
                capacity=?,
                price_per_hour=?,
                status=?
            WHERE id=?
        """, (
            category_id,
            name,
            description,
            filename,
            capacity,
            price,
            status,
            id
        ))

        conn.commit()

        log_action(
            action="UPDATE",
            table_name="facilities",
            record_id=id,
            description=f"Updated facility '{name}'"
        )

        conn.close()

        return jsonify({"message": "Facility updated successfully"})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ======================
# DELETE FACILITY (UPDATED - DELETE IMAGE FILE)
# ======================
@fetch_facility.route('/delete_facility/<int:id>', methods=['POST'])
def delete_facility(id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # get name + image
        cursor.execute("SELECT name, image FROM facilities WHERE id=?", (id,))
        row = cursor.fetchone()

        name = row[0] if row else "Unknown"
        image = row[1] if row else None

        # delete DB record
        cursor.execute("DELETE FROM facilities WHERE id=?", (id,))
        conn.commit()

        # delete image file
        if image:
            path = os.path.join(UPLOAD_FOLDER, image)
            if os.path.exists(path):
                os.remove(path)

        log_action(
            action="DELETE",
            table_name="facilities",
            record_id=id,
            description=f"Deleted facility '{name}'"
        )

        conn.close()

        return jsonify({"message": "Facility deleted successfully"})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# ======================
# FETCH DATA (AJAX)
# ======================
@fetch_facility.route('/facilities_data')
def facilities_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            f.*,
            c.name AS category_name
        FROM facilities f
        LEFT JOIN categories c ON f.category_id = c.id
        ORDER BY f.id ASC
    """)

    data = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in data])