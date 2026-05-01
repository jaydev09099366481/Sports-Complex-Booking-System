from flask import Blueprint, jsonify, request
import sqlite3
import os

# ======================
# Blueprint
# ======================
fetch_reservations = Blueprint('fetch_reservations', __name__)

# ======================
# DATABASE PATH
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')


# ======================
# GET ALL RESERVATIONS
# ======================
@fetch_reservations.route('/get_reservations')
def get_reservations():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            r.id,
            r.facility_id,
            r.user_id,

            r.booking_date,
            r.start_time,
            r.end_time,

            r.total_amount,
            r.deposit_amount,
            r.payment_method,

            r.gcash_reference,
            r.payment_screenshot,

            r.status,
            r.purpose,

            r.date_created,
            r.date_updated,

            u.name AS user_name,
            u.email AS user_email,
            u.phone AS user_phone,

            f.name AS facility_name,
            f.price_per_hour

        FROM reservations r

        LEFT JOIN users u
            ON r.user_id = u.id

        LEFT JOIN facilities f
            ON r.facility_id = f.id

        ORDER BY r.id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# ======================
# GET SINGLE RESERVATION
# ======================
@fetch_reservations.route('/get_reservation/<int:id>')
def get_reservation(id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            r.*,

            u.name AS user_name,
            u.email AS user_email,
            u.phone AS user_phone,

            f.name AS facility_name,
            f.description AS facility_description,
            f.image AS facility_image,
            f.price_per_hour

        FROM reservations r

        LEFT JOIN users u
            ON r.user_id = u.id

        LEFT JOIN facilities f
            ON r.facility_id = f.id

        WHERE r.id = ?

    """, (id,))

    reservation = cursor.fetchone()

    conn.close()

    if reservation:
        return jsonify(dict(reservation))

    return jsonify({
        "status": "error",
        "message": "Reservation not found"
    })


# ======================
# UPDATE RESERVATION STATUS
# ======================
@fetch_reservations.route('/update_reservation_status/<int:id>', methods=['POST'])
def update_reservation_status(id):

    status = request.form.get('status')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE reservations
        SET
            status = ?,
            date_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, id))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Reservation updated successfully"
    })


# ======================
# DELETE RESERVATION
# ======================
@fetch_reservations.route('/delete_reservation/<int:id>', methods=['POST'])
def delete_reservation(id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM reservations
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Reservation deleted successfully"
    })