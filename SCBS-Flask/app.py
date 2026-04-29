import os
import sqlite3
from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from fetch_users import fetch_user
from fetch_inquiries import fetch_inquiry
from fetch_categories import fetch_categories
from fetch_facility import fetch_facility

# ======================
# BASE DIRECTORY
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.secret_key = 'your_secret_key_here'

# ======================
# BLUEPRINTS
# ======================
app.register_blueprint(fetch_user)
app.register_blueprint(fetch_inquiry)
app.register_blueprint(fetch_categories)
app.register_blueprint(fetch_facility)

# ======================
# DATABASE CONNECTION
# ======================
db_path = os.path.join(BASE_DIR, 'database.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()



# ======================
# CREATE TABLES
# ======================
def init_db():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        role TEXT DEFAULT 'user',              -- admin / user
        status TEXT DEFAULT 'active',          -- active / inactive / banned
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        profile_image TEXT                    -- optional (path or URL)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        message TEXT,
        status TEXT DEFAULT 'unread'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Available',
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ======================
    # FACILITIES TABLE (UPDATED)
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category_id INTEGER NOT NULL,  -- 🔗 FK to categories
        name TEXT NOT NULL,
        description TEXT,
        image TEXT,                    -- 📷 store filename or path
        capacity INTEGER,              -- 👥 max number of users
        price_per_hour REAL,           -- 💰 optional pricing
        status TEXT DEFAULT 'Available',
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        table_name TEXT NOT NULL,
        record_id INTEGER,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

init_db()

# ======================
# HELPERS
# ======================
def render_with_active(template, active_page):
    return render_template(template, active_page=active_page)

# ======================
# ROUTES
# ======================
@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        conn = None

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            action = request.form.get('action')

            # ======================
            # SIGNUP
            # ======================
            if action == 'signup':
                name = request.form.get('name')
                email = request.form.get('email')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')

                if password != confirm_password:
                    return jsonify({"status": "error", "message": "Passwords do not match"})

                # ✅ HASH PASSWORD PROPERLY
                hashed_pw = generate_password_hash(password)

                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, hashed_pw)
                )

                conn.commit()
                return jsonify({"status": "success"})

            # ======================
            # LOGIN
            # ======================
            elif action == 'login':
                email = request.form.get('email')
                password = request.form.get('password')

                cursor.execute(
                    "SELECT * FROM users WHERE email=?",
                    (email,)
                )

                user = cursor.fetchone()

                if user and check_password_hash(user['password'], password):
                    session['user'] = user['email']
                    return jsonify({"status": "success"})

                return jsonify({"status": "error", "message": "Invalid credentials"})

        except Exception as e:
            print("LOGIN ERROR:", e)
            return jsonify({"status": "error", "message": str(e)})

        finally:
            if conn:
                conn.close()

    return render_template('auth/login.html')

# ======================
# ADMIN PAGES
# ======================
@app.route('/admin')
def dashboard():
    return render_with_active('admin/dashboard.html', 'dashboard')

@app.route('/reservations')
def reservations():
    return render_with_active('admin/reservations.html', 'reservations')

@app.route('/categories')
def categories():
    return render_with_active('admin/categories.html', 'categories')

@app.route('/facilities')
def facilities():
    return render_with_active('admin/facilities.html', 'facilities')

@app.route('/users')
def users():
    return render_with_active('admin/users.html', 'users')

# ======================
# INQUIRIES
# ======================
@app.route('/inquiries')
def inquiries():
    cursor.execute("SELECT * FROM inquiries")
    data = cursor.fetchall()
    return render_template('admin/inquiries.html', inquiries=data, active_page='inquiries')

@app.route('/delete_inquiry/<int:id>')
def delete_inquiry(id):
    cursor.execute("DELETE FROM inquiries WHERE id = ?", (id,))
    conn.commit()
    return redirect(url_for('inquiries'))

@app.route('/update_inquiry/<int:id>', methods=['POST'])
def update_inquiry(id):
    data = request.get_json()

    cursor.execute("""
        UPDATE inquiries 
        SET name=?, email=?, message=? 
        WHERE id=?
    """, (data['name'], data['email'], data['message'], id))

    conn.commit()
    return jsonify({"status": "success"})

# ======================
# HISTORY LOG (IMPORTANT FIX HERE)
# ======================
@app.route('/history_log')
def history_log():
    cursor.execute("SELECT * FROM history_log ORDER BY created_at DESC")
    logs = cursor.fetchall()

    return render_template(
        'admin/history-log.html',
        history_logs=logs,
        active_page='history_log'
    )

# ======================
# OTHER PAGES
# ======================
@app.route('/transaction_log')
def transaction_log():
    return render_with_active('admin/transaction-log.html', 'transaction_log')

@app.route('/settings')
def settings():
    return render_with_active('admin/settings.html', 'settings')

# ======================
# CONTACT
# ======================
@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    cursor.execute(
        "INSERT INTO inquiries (name, email, message) VALUES (?, ?, ?)",
        (name, email, message)
    )
    conn.commit()

    return jsonify({"status": "success"})


# ======================
# LOGOUT
# ======================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ======================
# RUN APP
# ======================
if __name__ == '__main__':
    app.run(debug=True)