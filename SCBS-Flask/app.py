import sqlite3
from flask import Flask, render_template, redirect, url_for, session, request, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ======================
# DATABASE CONNECTION
# ======================
conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ======================
# CREATE TABLES
# ======================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    message TEXT
)
""")

conn.commit()


# ======================
# HELPER FUNCTION
# ======================
def render_with_active(template, active_page):
    return render_template(template, active_page=active_page)


# ======================
# LANDING PAGE
# ======================
@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)


# ======================
# LOGIN & SIGNUP
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        action = request.form.get('action')

        # ======================
        # SIGNUP
        # ======================
        if action == 'signup':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not name or not email or not password or not confirm_password:
                return jsonify({"status": "error", "message": "All fields are required"})

            if password != confirm_password:
                return jsonify({"status": "error", "message": "Passwords do not match"})

            try:
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password)
                )
                conn.commit()

                return jsonify({"status": "success"})

            except sqlite3.IntegrityError:
                return jsonify({"status": "error", "message": "Email already exists"})


        # ======================
        # LOGIN
        # ======================
        elif action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')

            cursor.execute(
                "SELECT * FROM users WHERE email=? AND password=?",
                (email, password)
            )
            user = cursor.fetchone()

            if user:
                session['user'] = user['email']
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "message": "Invalid email or password"})

    return render_template('auth/login.html')


# ======================
# ADMIN DASHBOARD
# ======================
@app.route('/admin')
def dashboard():
    return render_with_active('admin/dashboard.html', 'dashboard')


# ======================
# STATIC ADMIN PAGES
# ======================
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
# ✅ FIXED INQUIRIES ROUTE (USE EXISTING SQLITE CONNECTION)
# ======================
@app.route('/inquiries')
def inquiries():
    cursor.execute("SELECT * FROM inquiries")
    inquiries = cursor.fetchall()

    return render_template('admin/inquiries.html', inquiries=inquiries, active_page='inquiries')


# ======================
# ✅ DELETE INQUIRY (NEW)
# ======================
@app.route('/delete_inquiry/<int:id>')
def delete_inquiry(id):
    cursor.execute("DELETE FROM inquiries WHERE id = ?", (id,))
    conn.commit()

    return redirect(url_for('inquiries'))


@app.route('/transaction_log')
def transaction_log():
    return render_with_active('admin/transaction-log.html', 'transaction_log')


@app.route('/history_log')
def history_log():
    return render_with_active('admin/history-log.html', 'history_log')


@app.route('/chatbot')
def chatbot():
    return render_with_active('admin/chatbot.html', 'chatbot')


@app.route('/settings')
def settings():
    return render_with_active('admin/settings.html', 'settings')


# ======================
# CONTACT FORM (SQLite)
# ======================
@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not name or not email or not message:
        return jsonify({"status": "error", "message": "All fields are required"})

    if "@gmail.com" not in email:
        return jsonify({"status": "error", "message": "Email must be Gmail only"})

    try:
        cursor.execute(
            "INSERT INTO inquiries (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ======================
# LOGOUT
# ======================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ======================
# RUN
# ======================
if __name__ == '__main__':
    app.run(debug=True)