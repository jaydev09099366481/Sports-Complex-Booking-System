import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ======================
# FUNCTION: GET CATEGORY ID
# ======================
def get_category_id(name):
    cursor.execute("SELECT id FROM categories WHERE name = ?", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


# ======================
# RAW DATA (WITH CATEGORY NAMES)
# ======================
raw_facilities = [
    ("Basketball Court", "Main Court A", "Indoor full-size basketball court with LED lighting", "basketball.jpg", "Available"),
    ("Swimming Pool", "Olympic Pool", "50-meter Olympic size swimming pool", "pool.jpg", "Available"),
    ("Tennis Court", "Court 1", "Standard clay tennis court", "tennis.jpg", "Available"),
    ("Gym", "Fitness Center", "Fully equipped gym with modern machines", "gym.jpg", "Maintenance"),
    ("Football Field", "Main Field", "Full-size grass football field", "football.jpg", "Available")
]


# ======================
# VALIDATE + CLEAN DATA
# ======================
clean_data = []

for category_name, name, description, image, status in raw_facilities:
    category_id = get_category_id(category_name)

    if category_id is not None:
        clean_data.append((category_id, name, description, image, status))
    else:
        print(f"⚠️ Skipped: Category '{category_name}' not found")


# ======================
# INSERT ONLY VALID DATA
# ======================
if clean_data:
    cursor.executemany("""
        INSERT INTO facilities (category_id, name, description, image, status)
        VALUES (?, ?, ?, ?, ?)
    """, clean_data)

    conn.commit()
    print(f"✅ {len(clean_data)} facilities inserted successfully!")
else:
    print("❌ No valid data to insert.")


conn.close()