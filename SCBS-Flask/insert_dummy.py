import sqlite3
import random
from datetime import datetime, timedelta

# ======================
# DATABASE CONNECTION
# ======================
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ======================
# FETCH USERS
# ======================
cursor.execute("""
    SELECT id, name
    FROM users
    WHERE role = 'user'
""")
users = cursor.fetchall()

# ======================
# FETCH FACILITIES
# ======================
cursor.execute("""
    SELECT id, name, price_per_hour
    FROM facilities
""")
facilities = cursor.fetchall()

# ======================
# VALIDATION
# ======================
if not users:
    print("❌ No users found in users table.")
    conn.close()
    exit()

if not facilities:
    print("❌ No facilities found in facilities table.")
    conn.close()
    exit()

# ======================
# SAMPLE DATA
# ======================
statuses = [
    "Pending",
    "Approved",
    "Rejected",
    "Cancelled"
]

purposes = [
    "Basketball Practice",
    "Swimming Session",
    "Training Camp",
    "Friendly Match",
    "School Tournament",
    "Fitness Workout",
    "Team Building",
    "Sports Event",
    "Competition",
    "Birthday Event"
]

time_slots = [
    ("8:00 AM", "10:00 AM", 2),
    ("9:00 AM", "11:00 AM", 2),
    ("10:00 AM", "12:00 PM", 2),
    ("1:00 PM", "3:00 PM", 2),
    ("3:00 PM", "5:00 PM", 2),
    ("5:00 PM", "7:00 PM", 2),
    ("6:00 PM", "9:00 PM", 3)
]

# ======================
# GENERATE DUMMY RESERVATIONS
# ======================
dummy_reservations = []

for i in range(15):

    user = random.choice(users)
    facility = random.choice(facilities)

    user_id = user[0]

    facility_id = facility[0]
    facility_price = facility[2] if facility[2] else 500

    # RANDOM FUTURE DATE
    booking_date = (
        datetime.now() + timedelta(days=random.randint(0, 15))
    ).strftime("%Y-%m-%d")

    # RANDOM TIME SLOT
    start_time, end_time, hours = random.choice(time_slots)

    # PAYMENT COMPUTATION
    total_amount = float(facility_price) * hours
    deposit_amount = round(total_amount * 0.30, 2)

    # PAYMENT DETAILS
    payment_method = "GCash"
    gcash_reference = f"GCASH-{random.randint(100000,999999)}"

    payment_screenshot = "/static/uploads/payments/sample_receipt.png"

    # STATUS
    status = random.choice(statuses)

    # PURPOSE
    purpose = random.choice(purposes)

    # UPDATED DATE
    date_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dummy_reservations.append((
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
        purpose,
        date_updated
    ))

# ======================
# INSERT DUMMY DATA
# ======================
cursor.executemany("""
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
        purpose,
        date_updated
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", dummy_reservations)

conn.commit()

print(f"✅ {len(dummy_reservations)} dummy reservations inserted successfully!")

conn.close()