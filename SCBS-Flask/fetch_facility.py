import os
import sqlite3
from flask import Blueprint, render_template
from config import DB_NAME

fetch_facility = Blueprint('fetch_facility', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)


# ======================
# FETCH ALL FACILITIES
# ======================
@fetch_facility.route('/facilities')
def facilities():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            date_created,
            category,
            name,
            description,
            status
        FROM facilities
        ORDER BY id ASC
    """)

    data = cursor.fetchall()
    conn.close()

    return render_template(
        'admin/facilities.html',
        facilities=data,
        active_page='facilities'
    )