import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.executemany("""
    INSERT INTO facilities (category, name, description, status)
    VALUES (?, ?, ?, ?)
""", [
    (
        "Basketball Court",
        "Main Court A",
        "Indoor full-size basketball court with LED lighting",
        "Available"
    ),
    (
        "Swimming Pool",
        "Olympic Pool",
        "50-meter Olympic size swimming pool",
        "Available"
    ),
    (
        "Tennis Court",
        "Court 1",
        "Standard clay tennis court",
        "Available"
    ),
    (
        "Gym",
        "Fitness Center",
        "Fully equipped gym with modern machines",
        "Maintenance"
    ),
    (
        "Football Field",
        "Main Field",
        "Full-size grass football field",
        "Available"
    )
])

conn.commit()
conn.close()

print("Dummy facilities data inserted successfully!")