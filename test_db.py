import mysql.connector
import time

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
}

print("Testing database connection...")
start = time.time()
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print(f"Connected in {time.time() - start:.2f} seconds!")
    conn.close()
except Exception as e:
    print(f"Failed to connect: {e}")
