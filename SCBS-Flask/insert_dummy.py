import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.executemany("""
    INSERT INTO users (name, email, password, phone, role, status)
    VALUES (?, ?, ?, ?, ?, ?)
""", [
    (
        "John Doe",
        "john@example.com",
        generate_password_hash("123456"),
        "09123456789",
        "admin",
        "active"
    ),
    (
        "Jane Smith",
        "jane@example.com",
        generate_password_hash("123456"),
        "09987654321",
        "user",
        "active"
    ),
    (
        "Michael Brown",
        "michael@example.com",
        generate_password_hash("123456"),
        "09111222333",
        "user",
        "inactive"
    ),
    (
        "Sarah Johnson",
        "sarah@example.com",
        generate_password_hash("123456"),
        "09223344556",
        "user",
        "active"
    ),
    (
        "Admin User",
        "admin@scbs.com",
        generate_password_hash("admin123"),
        "09000000000",
        "admin",
        "active"
    )
])

conn.commit()
conn.close()

print("Dummy users data inserted successfully!")