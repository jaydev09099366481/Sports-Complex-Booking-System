import os
import re
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from fetch_users import fetch_user
from fetch_inquiries import fetch_inquiry
from fetch_categories import fetch_categories
from fetch_facility import fetch_facility
from fetch_reservations import fetch_reservations
from create_reservation import create_reservation
from chatbot import chatbot
from email_notifications import EmailNotification
from process_forgot_password import forgot_password, reset_password, create_reset_tokens_table
from fetch_sales import fetch_sales
from reply_inquiry import inquiry_actions

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
app.register_blueprint(fetch_reservations)
app.register_blueprint(create_reservation)
app.register_blueprint(chatbot)
app.register_blueprint(fetch_sales)
app.register_blueprint(inquiry_actions)

# ======================
# FORGOT PASSWORD ROUTES
# ======================
create_reset_tokens_table()
app.add_url_rule("/forgot-password", view_func=forgot_password, methods=["POST"])
app.add_url_rule("/reset-password",  view_func=reset_password,  methods=["GET", "POST"])

# ======================
# DATABASE CONNECTION
# ======================
db_path = os.path.join(BASE_DIR, 'database.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

email_service = EmailNotification(
    sender_email="sportscomplexx1@gmail.com",
    sender_password="kaiu ouav fgqv kfsa"
)

# ======================
# RBAC CONFIGURATION
# ======================
ROLE_PERMISSIONS = {
    'admin': {
        'pages':   ['dashboard', 'reservations', 'categories', 'facilities',
                    'users', 'inquiries', 'sales', 'history_log'],
        'actions': ['create', 'edit', 'delete', 'approve', 'reject', 'extend', 'end'],
    },
    'staff': {
        'pages':   ['dashboard', 'reservations', 'categories', 'facilities', 'inquiries'],
        'actions': ['extend', 'end', 'approve', 'reject'],
    },
}

def get_admin_role():
    return session.get('admin_role', None)

def get_admin_name():
    return session.get('admin_name', '')

def can_access_page(page):
    role = get_admin_role()
    if not role:
        return False
    return page in ROLE_PERMISSIONS.get(role, {}).get('pages', [])

def can_do_action(action):
    role = get_admin_role()
    if not role:
        return False
    return action in ROLE_PERMISSIONS.get(role, {}).get('actions', [])

def rbac_required(page=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'admin' not in session:
                return redirect(url_for('admin_login'))
            if page and not can_access_page(page):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def admin_template_vars():
    return {
        'admin_role': get_admin_role(),
        'admin_name': get_admin_name(),
    }

# ======================
# ERROR HANDLERS
# ======================
@app.errorhandler(403)
def forbidden(e):
    # Clear admin session so they can log in again cleanly
    session.pop('admin', None)
    session.pop('admin_role', None)
    session.pop('admin_name', None)
    return render_template('auth/403.html'), 403


# ======================
# EMAIL HELPER
# ======================
def build_email(title, name, body_html):
    return f"""
    <div style="font-family: 'Poppins', Arial, sans-serif; max-width: 520px;
                margin: 0 auto; padding: 30px; border-radius: 12px;
                border: 1px solid #e0e0e0; background: #ffffff;">
        <h2 style="color: #205072; margin-bottom: 8px;">{title}</h2>
        <p style="color: #555; font-size: 14px; line-height: 1.6;">
            Hi <strong>{name}</strong>,
        </p>
        {body_html}
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #aaa; font-size: 11px; text-align: center;">
            © 2026 Sports Complex Booking System
        </p>
    </div>
    """


# ======================
# CREATE TABLES
# ======================
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        booking_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        total_amount REAL NOT NULL,
        deposit_amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'GCash',
        gcash_reference TEXT,
        payment_screenshot TEXT,
        status TEXT DEFAULT 'Pending',
        purpose TEXT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_updated TIMESTAMP,
        FOREIGN KEY (facility_id) REFERENCES facilities(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active',
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        profile_image TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'unread',
        remarks TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        image TEXT,
        capacity INTEGER,
        price_per_hour REAL,
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
# TIME-PARSING HELPERS
# ======================
_MONTH_MAP = {
    'january':1,'february':2,'march':3,'april':4,
    'may':5,'june':6,'july':7,'august':8,
    'september':9,'october':10,'november':11,'december':12,
}

def parse_booking_date(date_str):
    date_str = date_str.strip()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    m = re.match(r'^(\w+)\s+(\d{1,2}),\s+(\d{4})$', date_str, re.IGNORECASE)
    if m:
        month_num = _MONTH_MAP.get(m.group(1).lower())
        if month_num:
            return datetime(int(m.group(3)), month_num, int(m.group(2))).date()
    raise ValueError(f"Unrecognised date format: {date_str!r}")

def parse_time_str(time_str):
    time_str = time_str.strip()
    for fmt in ("%I:%M %p", "%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised time format: {time_str!r}")

def build_iso(date_str, time_str):
    d = parse_booking_date(date_str)
    t = parse_time_str(time_str)
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second).strftime("%Y-%m-%dT%H:%M:%S")


# ======================
# HELPERS
# ======================
def render_with_active(template, active_page):
    return render_template(template, active_page=active_page, **admin_template_vars())


# ======================
# PUBLIC ROUTES
# ======================
@app.route('/')
def index():
    user_data = None
    if 'user' in session:
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT name, email, profile_image FROM users WHERE email=?", (session['user'],))
        user_data = cur.fetchone()
        c.close()

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT * FROM categories WHERE status='Available'")
    categories = cur.fetchall()
    cur.execute("SELECT * FROM facilities WHERE status='Available'")
    facilities_raw = cur.fetchall()
    c.close()

    facilities = []
    for f in facilities_raw:
        facility = dict(f)
        image_file = facility.get("image") or facility.get("facility_image")
        if image_file:
            facility["image_url"] = url_for('static', filename=f'uploads/facilities/{image_file}')
        else:
            facility["image_url"] = url_for('static', filename='uploads/facilities/default.png')
        facilities.append(facility)

    return render_template("index.html", user=user_data, categories=categories, facilities=facilities)


# ======================
# USER LOGIN
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        c = None
        try:
            c = sqlite3.connect(db_path)
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            action = request.form.get('action')

            if action == 'signup':
                name             = request.form.get('name')
                email            = request.form.get('email')
                password         = request.form.get('password')
                confirm_password = request.form.get('confirm_password')

                if password != confirm_password:
                    return jsonify({"status": "error", "message": "Passwords do not match"})

                hashed_pw = generate_password_hash(password)
                cur.execute("INSERT INTO users (name, email, password, status) VALUES (?, ?, ?, ?)",
                            (name, email, hashed_pw, "active"))
                c.commit()

                email_service.send_email(
                    recipient_email=email,
                    subject="Welcome to Sports Complex Booking System",
                    message_html=build_email(
                        title="Welcome to Sports Complex!",
                        name=name,
                        body_html="""
                        <p style="color:#555;font-size:14px;line-height:1.6;">
                            Your account has been created successfully.
                            You can now log in to the Sports Complex Booking System.
                        </p>
                        <p style="color:#555;font-size:14px;line-height:1.6;">
                            <strong>Status:</strong>
                            <span style="color:#38a169;font-weight:600;">Active</span>
                        </p>
                        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
                        <p style="color:#888;font-size:12px;line-height:1.6;">
                            If you did not create this account, please contact our support team immediately.
                        </p>
                        """
                    )
                )
                return jsonify({"status": "success", "message": "Account created successfully"})

            elif action == 'login':
                email    = request.form.get('email')
                password = request.form.get('password')
                cur.execute("SELECT * FROM users WHERE email=?", (email,))
                user = cur.fetchone()

                if not user:
                    return jsonify({"status": "error", "message": "Account not found"})

                name   = user['name']
                status = user['status'] if 'status' in user.keys() else 'active'

                if status == "inactive":
                    email_service.send_email(
                        recipient_email=email,
                        subject="Login Attempt Failed – Sports Complex",
                        message_html=build_email(title="Login Attempt Failed", name=name, body_html="""
                            <p style="color:#555;font-size:14px;line-height:1.6;">
                                Your account is currently <strong style="color:#f59e0b;">Inactive</strong>.
                                Please contact our support team to activate your account.
                            </p>""")
                    )
                    return jsonify({"status": "error", "message": "This account is not active. Please contact support."})

                if status == "banned":
                    email_service.send_email(
                        recipient_email=email,
                        subject="Login Attempt Blocked – Sports Complex",
                        message_html=build_email(title="Login Attempt Blocked", name=name, body_html="""
                            <p style="color:#555;font-size:14px;line-height:1.6;">
                                Your account has been <strong style="color:#e53e3e;">Banned</strong>.
                                Please contact our support team for more information.
                            </p>""")
                    )
                    return jsonify({"status": "error", "message": "Your account has been banned. Please contact support."})

                if check_password_hash(user['password'], password):
                    session['user'] = user['email']
                    email_service.send_email(
                        recipient_email=email,
                        subject="Login Notification – Sports Complex",
                        message_html=build_email(title="Login Notification", name=name, body_html="""
                            <p style="color:#555;font-size:14px;line-height:1.6;">
                                You have successfully logged in to your
                                <strong>Sports Complex</strong> account.
                            </p>""")
                    )
                    return jsonify({"status": "success", "message": "Login successful"})

                return jsonify({"status": "error", "message": "Invalid credentials"})

        except Exception as e:
            print("LOGIN ERROR:", e)
            return jsonify({"status": "error", "message": str(e)})
        finally:
            if c:
                c.close()

    return render_template('auth/login.html')


@app.context_processor
def inject_user():
    if 'user' in session:
        try:
            c = sqlite3.connect(db_path)
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            cur.execute("SELECT name, email, profile_image FROM users WHERE email=?", (session['user'],))
            user = cur.fetchone()
            c.close()
            if user:
                return dict(user=user)
        except Exception as e:
            print("USER FETCH ERROR:", e)
    return dict(user=None)


@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (session['user'],))
    user = cur.fetchone()
    cur.execute("SELECT id FROM users WHERE email = ?", (session['user'],))
    user_row = cur.fetchone()
    uid = user_row['id']
    cur.execute("SELECT COUNT(*) FROM reservations WHERE user_id = ?", (uid,))
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM reservations WHERE user_id = ? AND status = 'Approved'", (uid,))
    approved = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM reservations WHERE user_id = ? AND status = 'Pending'", (uid,))
    pending = cur.fetchone()[0]
    c.close()

    stats = {"total": total, "approved": approved, "pending": pending}
    return render_template("profile.html", user=user, stats=stats)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized. Please login again."}), 401

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    try:
        name    = request.form.get('name')
        phone   = request.form.get('phone')
        address = request.form.get('address')
        email   = session['user']

        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        user_row = cur.fetchone()
        if not user_row:
            return jsonify({"status": "error", "message": "User not found"}), 404

        user_id            = user_row['id']
        profile_image_path = None
        file               = request.files.get('profile_image')

        if file and file.filename != "":
            filename      = secure_filename(file.filename)
            upload_folder = os.path.join('static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            filepath      = os.path.join(upload_folder, filename)
            file.save(filepath)
            profile_image_path = "/" + filepath.replace("\\", "/")

        if profile_image_path:
            cur.execute("UPDATE users SET name=?, phone=?, address=?, profile_image=? WHERE id=?",
                        (name, phone, address, profile_image_path, user_id))
        else:
            cur.execute("UPDATE users SET name=?, phone=?, address=? WHERE id=?",
                        (name, phone, address, user_id))

        c.commit()
        return jsonify({"status": "success", "message": "Profile updated successfully"})
    except Exception as e:
        print("UPDATE PROFILE ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        c.close()


@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_pw or not new_pw or not confirm_pw:
        return jsonify({"status": "error", "message": "All fields are required."})
    if len(new_pw) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters."})
    if new_pw != confirm_pw:
        return jsonify({"status": "error", "message": "New passwords do not match."})

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (session['user'],))
    user = cur.fetchone()

    if not check_password_hash(user['password'], current_pw):
        c.close()
        return jsonify({"status": "error", "message": "Current password is incorrect."})

    cur.execute("UPDATE users SET password=? WHERE email=?",
                (generate_password_hash(new_pw), session['user']))
    c.commit()
    c.close()
    return jsonify({"status": "success"})


# ======================
# ADMIN LOGIN
# ======================
@app.route('/admin', methods=['GET', 'POST'])
@app.route('/auth/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email         = request.form.get('email')
        password      = request.form.get('password')
        selected_role = request.form.get('role', 'admin')   # 'admin' or 'staff'
        is_ajax       = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email = ? AND role IN ('admin', 'staff')",
            (email,)
        )
        admin = cur.fetchone()
        c.close()

        # Wrong email or wrong password
        if not admin or not check_password_hash(admin['password'], password):
            if is_ajax:
                return jsonify({'error': 'Invalid credentials.'})
            return render_template('auth/admin-login.html', error='Invalid credentials.')

        # Account exists but the selected tab doesn't match the account's actual role
        if admin['role'] != selected_role:
            if is_ajax:
                return jsonify({'role_mismatch': True})
            return render_template(
                'auth/admin-login.html',
                error=f"This account is not registered as a {selected_role.capitalize()}."
            )

        # Success — set session and redirect
        session['admin']      = admin['email']
        session['admin_role'] = admin['role']
        session['admin_name'] = admin['name']

        if is_ajax:
            return jsonify({'redirect': url_for('dashboard')})
        return redirect(url_for('dashboard'))

    # Already logged in
    if 'admin' in session:
        return redirect(url_for('dashboard'))

    return render_template('auth/admin-login.html')

    
# ======================
# ADMIN — DASHBOARD
# ======================
@app.route('/admin/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if not can_access_page('dashboard'):
        abort(403)

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()

    cur.execute("SELECT COUNT(*) FROM reservations")
    reservations_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM categories")
    categories_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM facilities")
    facilities_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inquiries")
    inquiries_count = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(total_amount), 0) FROM reservations WHERE status = 'Approved'")
    total_sales = cur.fetchone()[0]

    today_iso   = datetime.now().strftime("%Y-%m-%d")
    today_label = datetime.now().strftime("%B %-d, %Y")

    cur.execute("""
        SELECT
            r.id, r.booking_date, r.start_time, r.end_time, r.status,
            r.facility_id, r.user_id,
            u.name          AS user_name,
            u.profile_image AS user_profile_image,
            f.name          AS facility_name,
            f.image         AS facility_image,
            c.name          AS category_name
        FROM reservations r
        LEFT JOIN users      u ON r.user_id      = u.id
        LEFT JOIN facilities f ON r.facility_id  = f.id
        LEFT JOIN categories c ON f.category_id  = c.id
        WHERE r.status = 'Approved'
          AND (r.booking_date = ? OR r.booking_date = ?)
        ORDER BY r.start_time ASC
    """, (today_iso, today_label))

    active_rows = cur.fetchall()
    c.close()

    active_reservations = []
    for r in active_rows:
        row = dict(r)
        try:
            row['iso_start'] = build_iso(row['booking_date'], row['start_time'])
            row['iso_end']   = build_iso(row['booking_date'], row['end_time'])
        except Exception as e:
            print(f"[dashboard] date parse error for reservation {row['id']}: {e}")
            row['iso_start'] = ''
            row['iso_end']   = ''

        row['facility_image_url'] = (
            f"/static/uploads/facilities/{row['facility_image']}"
            if row.get('facility_image') else None
        )
        img = row.get('user_profile_image')
        row['user_profile_image_url'] = (
            img if img and img.startswith('/') else
            f"/static/uploads/profiles/{img}" if img else None
        )
        active_reservations.append(row)

    return render_template(
        'admin/dashboard.html',
        active_page='dashboard',
        reservations_count=reservations_count,
        categories_count=categories_count,
        facilities_count=facilities_count,
        users_count=users_count,
        inquiries_count=inquiries_count,
        total_sales=total_sales,
        active_reservations=active_reservations,
        **admin_template_vars(),
    )


# ======================
# ADMIN — OTHER PAGES
# ======================
@app.route('/reservations')
def reservations():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('reservations'):
        abort(403)
    return render_template('admin/reservations.html',
                           active_page='reservations', **admin_template_vars())


@app.route('/get_booked_slots')
def get_booked_slots():
    facility_id = request.args.get('facility_id')
    date        = request.args.get('date')
    if not facility_id or not date:
        return jsonify({'booked_slots': []})

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("""
        SELECT start_time, end_time FROM reservations
        WHERE facility_id = ? AND booking_date = ? AND status IN ('Pending', 'Approved')
    """, (facility_id, date))
    rows = cur.fetchall()
    c.close()

    slots = []
    for row in rows:
        try:
            start_dt = datetime.strptime(row['start_time'], "%I:%M %p")
            end_dt   = datetime.strptime(row['end_time'],   "%I:%M %p")
            slots.append({'start_hour': start_dt.hour, 'end_hour': end_dt.hour})
        except Exception as e:
            print("Slot parse error:", e)
    return jsonify({'booked_slots': slots})


@app.route('/categories')
def categories():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('categories'):
        abort(403)
    return render_template('admin/categories.html',
                           active_page='categories', **admin_template_vars())


@app.route('/facilities')
def facilities():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('facilities'):
        abort(403)
    return render_template('admin/facilities.html',
                           active_page='facilities', **admin_template_vars())


@app.route('/users')
def users():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('users'):
        abort(403)
    return render_template('admin/users.html',
                           active_page='users', **admin_template_vars())


@app.route('/inquiries')
def inquiries():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('inquiries'):
        abort(403)
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT * FROM inquiries ORDER BY created_at DESC")
    data = cur.fetchall()
    c.close()
    return render_template('admin/inquiries.html',
                           inquiries=data, active_page='inquiries', **admin_template_vars())


@app.route('/sales')
def sales():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('sales'):
        abort(403)
    return render_template('admin/sales.html',
                           active_page='sales', **admin_template_vars())


@app.route('/history_log')
def history_log():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if not can_access_page('history_log'):
        abort(403)
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("""
        SELECT * FROM history_log
        WHERE LOWER(action) IN ('create','update','delete','insert','add','edit','remove')
        ORDER BY created_at DESC
    """)
    raw_logs = cur.fetchall()
    c.close()

    logs = []
    for log in raw_logs:
        row = dict(log)
        try:
            dt = datetime.strptime(row['created_at'], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.now()
        row['date'] = dt.strftime("%B %d, %Y")
        row['time'] = dt.strftime("%I:%M %p")
        logs.append(row)

    return render_template('admin/history-log.html',
                           history_logs=logs, active_page='history_log', **admin_template_vars())


@app.route('/transaction_log')
def transaction_log():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_with_active('admin/transaction-log.html', 'transaction_log')


@app.route('/settings')
def settings():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_with_active('admin/settings.html', 'settings')


# ======================
# USER — MY BOOKINGS
# ======================
@app.route('/my_bookings')
def my_bookings():
    if 'user' not in session:
        return redirect(url_for('login'))

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (session['user'],))
    user_row = cur.fetchone()
    cur.execute("""
        SELECT r.*, f.name AS facility_name
        FROM reservations r
        LEFT JOIN facilities f ON r.facility_id = f.id
        WHERE r.user_id = ?
        ORDER BY r.date_created DESC
    """, (user_row['id'],))
    bookings = [dict(row) for row in cur.fetchall()]
    c.close()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel_booking/<int:id>', methods=['POST'])
def cancel_booking(id):
    if 'user' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (session['user'],))
    user_row = cur.fetchone()
    cur.execute("""
        UPDATE reservations SET status = 'Cancelled'
        WHERE id = ? AND user_id = ? AND status = 'Pending'
    """, (id, user_row['id']))
    c.commit()
    affected = cur.rowcount
    c.close()

    if affected == 0:
        return jsonify({"status": "error", "message": "Booking not found or cannot be cancelled."})
    return jsonify({"status": "success"})


# ======================
# CONTACT
# ======================
@app.route('/contact', methods=['POST'])
def contact():
    data    = request.get_json()
    name    = data.get('name')
    email   = data.get('email')
    message = data.get('message')

    cursor.execute("INSERT INTO inquiries (name, email, message) VALUES (?, ?, ?)",
                   (name, email, message))
    conn.commit()

    email_service.send_email(
        recipient_email=email,
        subject="We received your inquiry – Sports Complex",
        message_html=build_email(
            title="Inquiry Received",
            name=name,
            body_html=f"""
            <p style="color:#555;font-size:14px;line-height:1.6;">
                Thank you for reaching out! We have received your message and will get back to you soon.
            </p>
            <div style="background:#f9f9f9;border-left:4px solid #329D9C;
                        padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0;">
                <p style="color:#555;font-size:13px;margin:0 0 6px;"><strong>Your message:</strong></p>
                <p style="color:#666;font-size:13px;line-height:1.6;margin:0;">{message}</p>
            </div>
            """
        )
    )
    return jsonify({"status": "success"})


# ======================
# EXTEND RESERVATION
# ======================
@app.route('/extend_reservation', methods=['POST'])
def extend_reservation():
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    if not can_do_action('extend'):
        return jsonify({'status': 'error', 'message': 'Permission denied.'}), 403

    try:
        data           = request.get_json()
        reservation_id = data.get('reservation_id')
        minutes        = data.get('minutes')

        if isinstance(minutes, str):
            minutes = {'30 mins': 30, '1 hour': 60, '1.5 hours': 90, '2 hours': 120}.get(minutes)
        minutes = int(minutes) if minutes else None

        if not minutes or minutes <= 0:
            return jsonify({'status': 'error', 'message': 'Invalid duration.'}), 400

        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT booking_date, start_time, end_time FROM reservations WHERE id = ?",
                    (reservation_id,))
        row = cur.fetchone()

        if not row:
            c.close()
            return jsonify({'status': 'error', 'message': 'Reservation not found.'}), 404

        try:
            current_end = datetime.combine(
                parse_booking_date(row['booking_date']),
                parse_time_str(row['end_time'])
            )
        except Exception as e:
            c.close()
            return jsonify({'status': 'error', 'message': f'Date parse error: {e}'}), 500

        new_end      = current_end + timedelta(minutes=minutes)
        new_end_time = new_end.strftime('%I:%M %p')
        new_date     = new_end.strftime('%Y-%m-%d')
        new_iso_end  = new_end.strftime('%Y-%m-%dT%H:%M:%S')

        cur.execute("""
            UPDATE reservations SET end_time=?, booking_date=?, date_updated=CURRENT_TIMESTAMP
            WHERE id=?
        """, (new_end_time, new_date, reservation_id))
        c.commit()
        c.close()

        return jsonify({
            'status':       'success',
            'message':      f'Session extended by {minutes} minutes.',
            'new_end_time': new_end_time,
            'new_iso_end':  new_iso_end,
            'new_date':     new_date,
        })

    except Exception as e:
        print('EXTEND ERROR:', e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ======================
# END RESERVATION
# ======================
@app.route('/end_reservation', methods=['POST'])
def end_reservation():
    if 'admin' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    if not can_do_action('end'):
        return jsonify({'status': 'error', 'message': 'Permission denied.'}), 403

    try:
        data           = request.get_json()
        reservation_id = data.get('reservation_id')

        if not reservation_id:
            return jsonify({'status': 'error', 'message': 'Missing reservation ID.'}), 400

        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT id, status FROM reservations WHERE id = ?", (reservation_id,))
        row = cur.fetchone()

        if not row:
            c.close()
            return jsonify({'status': 'error', 'message': 'Reservation not found.'}), 404

        if row['status'] != 'Approved':
            c.close()
            return jsonify({'status': 'error', 'message': 'Only approved sessions can be ended.'}), 400

        cur.execute("""
            UPDATE reservations SET status='Completed', date_updated=CURRENT_TIMESTAMP
            WHERE id=?
        """, (reservation_id,))
        c.commit()
        c.close()

        return jsonify({'status': 'success', 'message': 'Session marked as Completed.'})

    except Exception as e:
        print('END RESERVATION ERROR:', e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


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