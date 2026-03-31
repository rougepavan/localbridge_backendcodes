import mysql.connector
import time

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
}

print("Testing database connection to 127.0.0.1...")
start = time.time()
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    print(f"Connected to 127.0.0.1 in {time.time() - start:.2f} seconds!")
    conn.close()
except Exception as e:
    print(f"Failed to connect to 127.0.0.1: {e}")
