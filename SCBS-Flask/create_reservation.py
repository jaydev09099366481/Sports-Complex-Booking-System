from flask import Blueprint, request, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename

# ======================
# BLUEPRINT
# ======================
create_reservation = Blueprint('create_reservation', __name__)

# ======================
# DATABASE
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# ======================
# UPLOAD FOLDER
# ======================
UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    'static',
    'uploads',
    'payments'
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================
# CREATE RESERVATION
# ======================
@create_reservation.route('/create_reservation', methods=['POST'])
def create_new_reservation():

    try:

        # ======================
        # CHECK LOGIN
        # ======================
        if 'user' not in session:

            return jsonify({
                "status": "error",
                "message": "Please login first"
            })

        # ======================
        # DATABASE
        # ======================
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ======================
        # GET USER
        # ======================
        cursor.execute(
            "SELECT id FROM users WHERE email=?",
            (session['user'],)
        )

        user = cursor.fetchone()

        if not user:

            conn.close()

            return jsonify({
                "status": "error",
                "message": "User not found"
            })

        user_id = user['id']

        # ======================
        # FORM DATA
        # ======================
        facility_id = request.form.get('facility_id')
        booking_date = request.form.get('booking_date')

        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        total_amount = request.form.get('total_amount')
        deposit_amount = request.form.get('deposit_amount')

        purpose = request.form.get('purpose')

        gcash_reference = request.form.get('gcash_reference')

        # ======================
        # UPLOAD FILE
        # ======================
        screenshot = request.files.get('payment_screenshot')

        screenshot_filename = None

        if screenshot:

            filename = secure_filename(screenshot.filename)

            screenshot_filename = f"{gcash_reference}_{filename}"

            screenshot.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    screenshot_filename
                )
            )

        # ======================
        # INSERT RESERVATION
        # ======================
        cursor.execute("""
            INSERT INTO reservations (

                facility_id,
                user_id,

                booking_date,
                start_time,
                end_time,

                total_amount,
                deposit_amount,

                payment_method,

                gcash_reference,
                payment_screenshot,

                status,
                purpose

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            facility_id,
            user_id,

            booking_date,
            start_time,
            end_time,

            total_amount,
            deposit_amount,

            'GCash',

            gcash_reference,
            screenshot_filename,

            'Pending',
            purpose
        ))

        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Reservation created successfully"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })