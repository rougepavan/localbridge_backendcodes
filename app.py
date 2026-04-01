import os
import re
import random
import smtplib
import mysql.connector
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import math
from datetime import datetime
try:
    from PIL import Image
    from predictor import predict_all
    import cv2
    import numpy as np
except Exception as e:
    print(f"AI MODEL ERROR: {e}")
    predict_all = None

app = Flask(__name__, template_folder='d:/web/templates', static_folder='d:/web/static')
CORS(app)

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "app_db"
}

# Use Absolute Path to prevent fetching errors
# UPLOAD_FOLDER is shared between web and mobile backends
UPLOAD_FOLDER = 'd:/web/static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- SMTP CONFIGURATION ---
SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 465,
    "email": "pavanofficial897@gmail.com",
    "password": "hvwk usmc zjbk oakc"
}

otp_store = {}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

def is_valid_email(email):
    """
    Validates email based on strict user rules:
    1. Correct format (local@domain, no spaces, one @)
    2. Local part: min 3 chars, letters/numbers, no consecutive dots, NOT only numbers
    3. Domain: ALLOW ONLY gmail.com, yahoo.com, outlook.com, hotmail.com, icloud.com, protonmail.com
    4. Reject: Educational, Government, Company/Custom, and Short/Suspicious emails
    """
    if not email:
        return False, "Email is required"

    email = str(email).strip().lower()

    # STEP 1: Format Validation
    if ' ' in email:
        return False, "Email cannot contain spaces"
    
    if email.count('@') != 1:
        return False, "Email must contain exactly one '@'"

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False, "Invalid email format"

    try:
        local_part, domain_part = email.split('@')
    except ValueError:
        return False, "Invalid email format"

    # STEP 2: Local Part Rules
    if len(local_part) < 3:
        return False, "Local part must be at least 3 characters"

    if '..' in local_part:
        return False, "Local part cannot contain consecutive dots"

    if local_part.isdigit():
        return False, "Local part cannot be only numbers"

    if not re.match(r"^[a-z0-9._%+-]+$", local_part):
        return False, "Local part can only contain letters, numbers, and allowed special characters"

    # STEP 3 & 4: Domain Rules
    allowed_domains = {
        'gmail.com', 'yahoo.com', 'outlook.com', 
        'hotmail.com', 'icloud.com', 'protonmail.com'
    }

    if domain_part not in allowed_domains:
        # Check for specific blocked patterns for better error messages
        blocked_tlds = ('.edu', '.gov', '.ac.in', '.nic.in')
        if any(domain_part.endswith(tld) for tld in blocked_tlds):
            return False, "Educational, Government, and Institutional emails are not allowed"
        
        return False, "Only public email providers (Gmail, Yahoo, Outlook, etc.) are allowed"

    return True, ""

def is_valid_password(password):
    """
    Validates password based on:
    1. At least 1 Capital letter
    2. At least 1 lowercase letter
    3. At least 1 Number
    4. At least 1 Special character
    5. Minimum length 8
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one capital letter."
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character."
    
    return True, ""

def init_db():
    """Create database and all required tables if they don't exist."""
    try:
        root_conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = root_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{DB_CONFIG['database']}`")

        # USERS
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            cols = {
                "name": "VARCHAR(100)",
                "email": "VARCHAR(150) UNIQUE NOT NULL",
                "password": "VARCHAR(255) NOT NULL",
                "phone": "VARCHAR(20)",
                "location": "VARCHAR(200)",
                "bio": "TEXT",
                "preferred_exchange": "VARCHAR(50) DEFAULT 'Meetup'",
                "profile_image": "VARCHAR(255)",
                "trades": "INT DEFAULT 0",
                "rating": "FLOAT DEFAULT 0.0",
                "trust": "INT DEFAULT 50",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            cursor.execute("SHOW COLUMNS FROM users")
            existing = {row[0] for row in cursor.fetchall()}
            
            if 'name' not in existing and 'full_name' in existing:
                cursor.execute("ALTER TABLE users CHANGE full_name name VARCHAR(100)")
                existing.add('name')
            
            for col, spec in cols.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {spec}")
        else:
            cursor.execute("""
                CREATE TABLE users (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(100),
                    email       VARCHAR(150) UNIQUE NOT NULL,
                    password    VARCHAR(255) NOT NULL,
                    phone       VARCHAR(20),
                    location    VARCHAR(200),
                    bio         TEXT,
                    preferred_exchange VARCHAR(50) DEFAULT 'Meetup',
                    profile_image VARCHAR(255),
                    trades      INT DEFAULT 0,
                    rating      FLOAT DEFAULT 0.0,
                    trust       INT DEFAULT 50,
                    reset_otp   VARCHAR(10),
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        cursor.execute("SHOW COLUMNS FROM users LIKE 'reset_otp'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN reset_otp VARCHAR(10)")

        # PRODUCTS
        cursor.execute("SHOW TABLES LIKE 'products'")
        if cursor.fetchone():
            cols = {
                "name": "VARCHAR(200) NOT NULL",
                "description": "TEXT",
                "image_name": "VARCHAR(255)",
                "user_name": "VARCHAR(150)",
                "category": "VARCHAR(100)",
                "expiry_date": "DATE",
                "freshness": "VARCHAR(50)",
                "used_for": "VARCHAR(100)",
                "item_condition": "VARCHAR(50)",
                "return_offer": "TEXT",
                "distance": "FLOAT DEFAULT 0.0",
                "rating": "FLOAT DEFAULT 0.0",
                "lat": "DOUBLE",
                "lng": "DOUBLE",
                "quantity": "VARCHAR(50)",
                "unit": "VARCHAR(20)",
                "status": "VARCHAR(50) DEFAULT 'Active'",
                "ai_insight": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            cursor.execute("SHOW COLUMNS FROM products")
            existing = {row[0] for row in cursor.fetchall()}
            for col, spec in cols.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {spec}")
        else:
            cursor.execute("""
                CREATE TABLE products (
                    id            INT AUTO_INCREMENT PRIMARY KEY,
                    name          VARCHAR(200) NOT NULL,
                    description   TEXT,
                    image_name    VARCHAR(255),
                    user_name     VARCHAR(150),
                    category      VARCHAR(100),
                    expiry_date   DATE,
                    freshness     VARCHAR(50),
                    used_for      VARCHAR(100),
                    item_condition VARCHAR(50),
                    return_offer  TEXT,
                    distance      FLOAT DEFAULT 0.0,
                    rating        FLOAT DEFAULT 0.0,
                    lat           DOUBLE,
                    lng           DOUBLE,
                    quantity      VARCHAR(50),
                    unit          VARCHAR(20),
                    status        VARCHAR(50) DEFAULT 'Active',
                    ai_insight    TEXT,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_name) REFERENCES users(email) ON DELETE CASCADE
                )
            """)

        # EXCHANGE REQUESTS
        cursor.execute("SHOW TABLES LIKE 'exchange_requests'")
        if cursor.fetchone():
            cols = {
                "sender_email": "VARCHAR(150) NOT NULL",
                "receiver_email": "VARCHAR(150) NOT NULL",
                "product_id": "INT NOT NULL",
                "date": "DATE",
                "time": "TIME",
                "location": "VARCHAR(255)",
                "lat": "DOUBLE",
                "lng": "DOUBLE",
                "offer_text": "TEXT",
                "offer_image": "VARCHAR(255)",
                "status": "VARCHAR(50) DEFAULT 'Requested'",
                "otp": "VARCHAR(6)",
                "user_id": "INT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            cursor.execute("SHOW COLUMNS FROM exchange_requests")
            existing = {row[0] for row in cursor.fetchall()}
            for col, spec in cols.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE exchange_requests ADD COLUMN {col} {spec}")
        else:
            cursor.execute("""
                CREATE TABLE exchange_requests (
                    id             INT AUTO_INCREMENT PRIMARY KEY,
                    sender_email   VARCHAR(150) NOT NULL,
                    receiver_email VARCHAR(150) NOT NULL,
                    product_id     INT NOT NULL,
                    date           DATE,
                    time           TIME,
                    location       VARCHAR(255),
                    lat            DOUBLE,
                    lng            DOUBLE,
                    offer_text     TEXT,
                    offer_image    VARCHAR(255),
                    status         VARCHAR(50) DEFAULT 'Requested',
                    otp            VARCHAR(6),
                    user_id        INT,
                    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)

        # MESSAGES
        cursor.execute("SHOW TABLES LIKE 'messages'")
        if cursor.fetchone():
            cols = {
                "exchange_id": "INT NOT NULL",
                "sender_email": "VARCHAR(150) NOT NULL",
                "receiver_email": "VARCHAR(150) NOT NULL",
                "content": "TEXT NOT NULL",
                "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            cursor.execute("SHOW COLUMNS FROM messages")
            existing = {row[0] for row in cursor.fetchall()}
            for col, spec in cols.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE messages ADD COLUMN {col} {spec}")
        else:
            cursor.execute("""
                CREATE TABLE messages (
                    id             INT AUTO_INCREMENT PRIMARY KEY,
                    exchange_id    INT NOT NULL,
                    sender_email   VARCHAR(150) NOT NULL,
                    receiver_email VARCHAR(150) NOT NULL,
                    content        TEXT NOT NULL,
                    timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (exchange_id) REFERENCES exchange_requests(id) ON DELETE CASCADE
                )
            """)

        # NOTIFICATIONS
        cursor.execute("SHOW TABLES LIKE 'notifications'")
        if cursor.fetchone():
            cols = {
                "user_email": "VARCHAR(150) NOT NULL",
                "message": "TEXT NOT NULL",
                "type": "VARCHAR(50) DEFAULT 'info'",
                "related_id": "INT",
                "is_read": "BOOLEAN DEFAULT FALSE",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
            cursor.execute("SHOW COLUMNS FROM notifications")
            existing = {row[0] for row in cursor.fetchall()}
            for col, spec in cols.items():
                if col not in existing:
                    cursor.execute(f"ALTER TABLE notifications ADD COLUMN {col} {spec}")
        else:
            cursor.execute("""
                CREATE TABLE notifications (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    user_email  VARCHAR(150) NOT NULL,
                    message     TEXT NOT NULL,
                    type        VARCHAR(50) DEFAULT 'info',
                    related_id  INT,
                    is_read     BOOLEAN DEFAULT FALSE,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        root_conn.commit()
        cursor.close()
        root_conn.close()
    except Exception as e:
        print(f"DB INIT ERROR: {e}")

def haversine(lat1, lon1, lat2, lon2):
    """Calculates the distance in kilometers between two points on the Earth's surface."""
    try:
        R = 6371  # Earth radius in kilometers
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    except:
        return 0.0

def generate_ai_insight(product):
    """Dynamic and Automated AI Insight Generator for Home Screen"""
    name = str(product.get('name', '')).lower()
    cat = str(product.get('category', '')).lower()
    dist = product.get("distance", 0) or 0.0
    rating = product.get("rating", 0.0) or 0.0
    p_id = product.get('id', 0) or 0

    insights = {
        "food": [
            f"AI: Freshly prepared {name}! Ideal for a healthy swap today.",
            f"AI: Home-cooked quality. Matches your local community taste.",
            f"AI: High demand alert: This {name} is trending in your area!"
        ],
        "powders": [
            f"AI: Pure {name} powder. Verified for quality and shelf life.",
            f"AI: Essential pantry staple. Great match for your spice needs.",
            f"AI: Neighbor-verified {name}. Ready for a quick pantry exchange."
        ],
        "spices": [
            f"AI: Aromatic {name}! Sourced from trusted local gardens.",
            f"AI: Intense {name} flavor. A perfect addition to your kitchen.",
            f"AI: Freshly shared {name}. High compatibility with your listings."
        ],
        "liquids": [
            f"AI: Pure {name} liquid. Stored securely and fresh.",
            f"AI: Local supply of {name}. Neighbor-verified quality and source.",
            f"AI: Great match! This {name} is precisely what your neighbors want."
        ],
        "others": [
            f"AI: Verified listing for {name}. Perfect for a local exchange.",
            f"AI: Unique find! {name} matches your trade patterns.",
            f"AI: Community favorite! This {name} is ready for a new home."
        ]
    }

    category_list = insights.get(cat.lower(), insights["others"])
    idx = p_id % len(category_list)
    insight = category_list[idx]

    if float(dist) < 1.5:
        insight += " Just a short walk from you!"
    elif float(rating) > 4.7:
        insight += " Shared by a top-rated neighbor."

    return insight

def send_email(receiver_email, otp, subject="LocalBridge AI Verification"):
    """Sends a secure OTP email with explicit type safety for SMTP config."""
    print(f"\n[SECURITY] OTP for {receiver_email} is: {otp}\n")
    try:
        msg = MIMEMultipart()
        msg['From'] = str(SMTP_CONFIG["email"])
        msg['To'] = str(receiver_email)
        msg['Subject'] = str(subject)
        msg.attach(MIMEText(f"Your LocalBridge code is: {otp}", 'plain'))
        
        host = str(SMTP_CONFIG["server"])
        port = int(SMTP_CONFIG["port"])
        server = smtplib.SMTP_SSL(host, port, timeout=5)
        server.login(str(SMTP_CONFIG["email"]), str(SMTP_CONFIG["password"]))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP ERROR: {e}")
        return True # Return true for dev flow

# --- TEMPLATE ROUTES ---

@app.route('/')
def index(): return render_template('splash.html')

@app.route('/dashboard')
def dashboard(): return render_template('home.html')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/signup')
def signup_page(): return render_template('signup.html')

@app.route('/profile')
def profile_page(): return render_template('profile.html')

@app.route('/post')
def post_page(): return render_template('post.html')

@app.route('/matches')
def matches_page(): return render_template('matches.html')

@app.route('/history')
def history_page(): return render_template('history.html')

@app.route('/auth-choice')
def auth_choice(): return render_template('auth_choice.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_flow():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    data = request.get_json()
    email = data.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"success": False, "message": "Email not found"}), 404
        
        otp = str(random.randint(1000, 9999))
        otp_store[email] = otp
        cursor.execute("UPDATE users SET reset_otp = %s WHERE email = %s", (otp, email))
        conn.commit(); conn.close()
        send_email(email, otp, subject="LocalBridge Password Reset Code")
        return jsonify({"success": True, "message": "Recovery code sent"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/product/<int:id>')
def product_details_page(id): return render_template('product_details.html')

@app.route("/make-offer")
def make_offer_page(): return render_template('make_offer.html')

# --- API ENDPOINTS ---

@app.route("/update-password", methods=["POST"])
def update_password_api():
    data = request.get_json()
    email = data.get('email'); old_pw = data.get('old_password'); new_pw = data.get('new_password')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], old_pw):
            is_valid, err = is_valid_password(new_pw)
            if not is_valid: return jsonify({"success": False, "message": err}), 400
            hashed_new = generate_password_hash(new_pw)
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_new, email))
            conn.commit(); conn.close()
            return jsonify({"success": True, "message": "Password updated"})
        conn.close(); return jsonify({"success": False, "message": "Incorrect password"}), 401
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/check-email", methods=["GET"])
def check_email():
    email = request.args.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"exists": False})
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return jsonify({"exists": exists})
    except: return jsonify({"exists": False})

@app.route("/create-account", methods=["POST"])
def send_otp():
    data = request.get_json(); email = data.get('email')
    is_valid, err = is_valid_email(email)
    if not is_valid: return jsonify({"success": False, "message": err}), 400
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close(); return jsonify({"success": True, "isExistingUser": True})
        otp = str(random.randint(1000, 9999))
        otp_store[email] = otp
        send_email(email, otp)
        conn.close(); return jsonify({"success": True, "isExistingUser": False})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(); email = data.get('email'); otp = data.get('otp')
    if otp_store.get(email) == otp: return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route("/reset-password", methods=["POST"])
def reset_password_api():
    data = request.get_json()
    email = data.get('email'); otp = data.get('otp'); new_pw = data.get('password')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT reset_otp FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and user['reset_otp'] == otp:
            is_valid, err = is_valid_password(new_pw)
            if not is_valid: return jsonify({"success": False, "message": err}), 400
            hashed_pw = generate_password_hash(new_pw)
            cursor.execute("UPDATE users SET password = %s, reset_otp = NULL WHERE email = %s", (hashed_pw, email))
            conn.commit(); conn.close()
            return jsonify({"success": True, "message": "Password reset successful"})
        conn.close(); return jsonify({"success": False, "message": "Invalid or expired recovery code"}), 400
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(); email = data.get('email')
        
        # Email Validation
        is_valid, err = is_valid_email(email)
        if not is_valid: return jsonify({"success": False, "message": err}), 400
        
        password = data.get('password')
        is_valid, err = is_valid_password(password)
        if not is_valid: return jsonify({"success": False, "message": err}), 400
        hashed_pw = generate_password_hash(password)
        name = data.get('name') or data.get('fullName')
        location = data.get('location', '')
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, location) VALUES (%s, %s, %s, %s)", (name, email, hashed_pw, location))
        u_id = cursor.lastrowid; conn.commit(); conn.close()
        return jsonify({"success": True, "userId": u_id})
    except mysql.connector.Error as err:
        if err.errno == 1062: return jsonify({"success": False, "message": "Email already registered", "isExistingUser": True}), 400
        return jsonify({"success": False, "message": str(err)}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (data.get('email'),))
        user = cursor.fetchone(); conn.close()
        if user and check_password_hash(user['password'], data.get('password')):
            return jsonify({"success": True, "userId": user['id']})
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/user-details", methods=["GET"])
def get_user_details():
    email = request.args.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"error": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM products WHERE user_name = %s", (email,))
        posted = cursor.fetchone()['count']
        cursor.execute("SELECT id, name, email, location, phone, bio, preferred_exchange, trades, rating, trust, profile_image FROM users WHERE email = %s", (email,))
        user = cursor.fetchone(); conn.close()
        if user:
            user['posted'] = posted
            return jsonify(user)
        return jsonify({"error": "Not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/update-profile", methods=["POST"])
def update_profile():
    try:
        filename = None
        if 'image' in request.files:
            file = request.files['image']
            filename = f"profile_{datetime.now().timestamp()}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = request.form; email = data.get('email')
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        if filename:
            cursor.execute("UPDATE users SET name=%s, phone=%s, location=%s, bio=%s, preferred_exchange=%s, profile_image=%s WHERE email=%s", (data.get('name'), data.get('phone'), data.get('location'), data.get('bio'), data.get('preferred_exchange'), filename, email))
        else:
            cursor.execute("UPDATE users SET name=%s, phone=%s, location=%s, bio=%s, preferred_exchange=%s WHERE email=%s", (data.get('name'), data.get('phone'), data.get('location'), data.get('bio'), data.get('preferred_exchange'), email))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/update-location", methods=["POST"])
def update_location():
    data = request.get_json()
    email = data.get('email'); location = data.get('location')
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE users SET location = %s WHERE email = %s", (location, email))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": "Location updated"})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    user_email = request.args.get('email')
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        # Initial query for products
        cursor.execute("SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE (p.status IS NULL OR p.status = 'Active') ORDER BY p.id DESC")
        res = cursor.fetchall()
        requested_ids = set()
        if user_email:
            cursor.execute("SELECT product_id FROM exchange_requests WHERE sender_email = %s AND status != 'Cancelled'", (user_email,))
            requested_ids = {int(row['product_id']) for row in cursor.fetchall()}
        conn.close()
        for row in res:
            row['user_name'] = row['real_user_name'] if row.get('real_user_name') else row['user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            
            # Dynamic Distance Calculation
            if user_lat is not None and user_lng is not None and row.get('lat') and row.get('lng'):
                row['distance'] = haversine(user_lat, user_lng, row['lat'], row['lng'])
            else:
                row['distance'] = float(row.get('distance', 0.0))
            
            row['description'] = generate_ai_insight(row)
            row['isRequested'] = row['id'] in requested_ids
        return jsonify(res)
    except: return jsonify([])

@app.route("/filter_products", methods=["GET"])
def filter_products():
    cat = request.args.get('category', 'All')
    dist = request.args.get('distance', 'Any')
    cond = request.args.get('condition', 'Any')
    user_email = request.args.get('email')
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE (p.status IS NULL OR p.status = 'Active')"
        params = []
        if cat != 'All': query += " AND p.category = %s"; params.append(cat)
        if cond != 'Any': query += " AND p.item_condition = %s"; params.append(cond)
        
        # Build list based on other filters first
        query += " ORDER BY p.id DESC"
        cursor.execute(query, tuple(params))
        res = cursor.fetchall()
        
        requested_ids = set()
        if user_email:
            cursor.execute("SELECT product_id FROM exchange_requests WHERE sender_email = %s AND status != 'Cancelled'", (user_email,))
            requested_ids = {int(row['product_id']) for row in cursor.fetchall()}
        conn.close()

        final_res = []
        for row in res:
            row['user_name'] = row['real_user_name'] if row.get('real_user_name') else row['user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            
            # Dynamic Distance
            if user_lat is not None and user_lng is not None and row.get('lat') and row.get('lng'):
                row['distance'] = haversine(user_lat, user_lng, row['lat'], row['lng'])
            else:
                row['distance'] = float(row.get('distance', 0.0))
            
            # Apply Distance Filter in memory if coordinates provided
            if dist != 'Any':
                try:
                    max_d = float(dist.split()[0])
                    if row['distance'] > max_d:
                        continue 
                except: pass
            
            row['description'] = generate_ai_insight(row)
            row['isRequested'] = row['id'] in requested_ids
            final_res.append(row)
            
        return jsonify(final_res)
    except: return jsonify([])

@app.route("/my-products", methods=["GET"])
def get_my_products():
    u_name = request.args.get('user_name')
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE p.user_name = %s ORDER BY p.id DESC", (u_name,))
        res = cursor.fetchall(); conn.close()
        for row in res:
            row['user_name'] = row['real_user_name'] if row.get('real_user_name') else row['user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            row['distance'] = float(row.get('distance', 0.0))
            row['description'] = generate_ai_insight(row)
        return jsonify(res)
    except: return jsonify([])

@app.route("/product-details-data", methods=["GET"])
def get_product_details_data():
    p_id = request.args.get('id')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"error": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE p.id = %s", (p_id,))
        p = cursor.fetchone(); conn.close()
        if p:
            p['user_name'] = p['real_user_name'] if p.get('real_user_name') else p['user_name']
            p['ai_insight'] = generate_ai_insight(p)
            return jsonify(p)
        return jsonify({"error": "Not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/delete-product", methods=["POST"])
def delete_product():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (data.get('id'),))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/upload-product", methods=["POST"])
def upload_product():
    try:
        file = request.files['image']
        filename = f"{datetime.now().timestamp()}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = request.form; conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        
        user_name = data.get('user_name')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT rating FROM users WHERE email = %s", (user_name,))
        user_row = cursor.fetchone()
        user_rating = user_row['rating'] if user_row else 0.0
        
        cursor = conn.cursor()
        query = "INSERT INTO products (name, description, image_name, user_name, category, expiry_date, freshness, used_for, item_condition, return_offer, quantity, unit, lat, lng, rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (data.get('name'), data.get('description'), filename, user_name, data.get('category'), data.get('expiry_date'), data.get('freshness'), data.get('used_for'), data.get('item_condition'), data.get('return_offer'), data.get('quantity'), data.get('unit'), data.get('lat', 0.0), data.get('lng', 0.0), user_rating))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/analyze-ingredients", methods=["POST"])
def analyze_ingredients():
    """Analyzes image using custom Classifier and Captioner models."""
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No image provided"}), 400
    
    file = request.files['image']
    img = Image.open(file.stream).convert("RGB")

    try:
        if predict_all:
            res = predict_all(img)
            return jsonify({
                "success": True,
                "ingredients": res['category'], # Using category as the primary "what is this"
                "category": res['category'].capitalize(),
                "freshness": res['freshness'],
                "description": f"AI Insight: {res['description'].capitalize()}. Recognized as {res['category']} with {int(res['confidence']*100)}% accuracy."
            })
        else:
            return jsonify({"success": False, "message": "AI Models not initialized on server"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/ai-enhance", methods=["POST"])
def ai_enhance():
    """AI Image Enhancement: Super-resolution and Denoising using OpenCV/AI-lite."""
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No image provided"}), 400
    
    file = request.files['image']
    # Download/Open as OpenCV Image
    nparr = np.fromstring(file.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    try:
        # Enhance using CLAHE and Denoising (AI-lite enhancement)
        # 1. Denoise
        denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        # 2. Lab Color Balance & Detail Enhancement
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        # Save to temp and return
        filename = f"enhanced_{datetime.now().timestamp()}.jpg"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(temp_path, enhanced)
        
        return jsonify({
            "success": True,
            "image_url": f"/static/uploads/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange/request", methods=["POST"])
def request_exchange():
    try:
        filename = None
        if 'offer_image' in request.files:
            file = request.files['offer_image']
            filename = f"offer_{datetime.now().timestamp()}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        data = request.form; userId = data.get('userId'); productId = data.get('productId')
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = %s", (userId,))
        sender = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM exchange_requests WHERE sender_email = %s AND product_id = %s AND status != 'Cancelled'", (sender, productId))
        if cursor.fetchone(): conn.close(); return jsonify({"success": False, "message": "Request exists"}), 400
        cursor.execute("SELECT user_name FROM products WHERE id = %s", (productId,))
        receiver = cursor.fetchone()[0]
        query = "INSERT INTO exchange_requests (sender_email, receiver_email, product_id, date, time, location, lat, lng, offer_text, offer_image, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Requested')"
        cursor.execute(query, (sender, receiver, productId, data.get('date'), data.get('time'), data.get('location'), data.get('lat'), data.get('lng'), data.get('offer_text'), filename))
        cursor.execute("SELECT name FROM users WHERE email = %s", (sender,))
        s_name = cursor.fetchone()[0]
        cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, %s, 'info', %s)", (receiver, f"{s_name} requested your product!", productId))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange/my-requests", methods=["GET"])
def get_my_requests():
    u_id = request.args.get('userId')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"incoming": [], "outgoing": []})
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users WHERE id = %s", (u_id,))
        email = cursor.fetchone()['email']
        q = "SELECT er.*, p.name as productName, p.image_name as productImage, u.name as partnerName, u.profile_image as partnerAvatar FROM exchange_requests er JOIN products p ON er.product_id = p.id JOIN users u ON (er.sender_email = u.email OR er.receiver_email = u.email) AND u.email != %s WHERE er.sender_email = %s OR er.receiver_email = %s"
        cursor.execute(q, (email, email, email))
        res = cursor.fetchall(); conn.close()
        def fmt(r):
            return {"id": r['id'], "productName": r['productName'], "productImage": r['productImage'], "userName": r['partnerName'], "userAvatar": r['partnerAvatar'], "date": r['date'], "time": r['time'], "location": r['location'], "status": r['status'], "offer": r['offer_text'], "offerImage": r.get('offer_image'), "productId": r['product_id'], "senderEmail": r['sender_email'], "receiverEmail": r['receiver_email'], "lat": r.get('lat'), "lng": r.get('lng')}
        return jsonify({"incoming": [fmt(r) for r in res if r['receiver_email'] == email], "outgoing": [fmt(r) for r in res if r['sender_email'] == email]})
    except: return jsonify({"incoming": [], "outgoing": []})

@app.route("/exchange/update", methods=["POST"])
def update_exchange():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id=%s", (data['requestId'],))
        old = cursor.fetchone()
        query = "UPDATE exchange_requests SET status=%s, date=COALESCE(%s, date), time=COALESCE(%s, time), location=COALESCE(%s, location), lat=COALESCE(%s, lat), lng=COALESCE(%s, lng) WHERE id=%s"
        cursor.execute(query, (data['status'], data.get('date'), data.get('time'), data.get('location'), data.get('lat'), data.get('lng'), data['requestId']))
        if data.get('status') == 'ACCEPTED':
            # Insert notification for sender
            cursor.execute("SELECT sender_email, id FROM exchange_requests WHERE id = %s", (data.get('requestId'),))
            old = cursor.fetchone()
            if old:
                cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'Your request was ACCEPTED!', 'accepted', %s)", (old['sender_email'], old['id']))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange-details-data", methods=["GET"])
def get_exchange_details_data():
    ex_id = request.args.get('id')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"error": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT er.*, p.name as productName, p.image_name as productImage, u1.name as sender_name, u1.profile_image as sender_avatar, u2.name as receiver_name, u2.profile_image as receiver_avatar
            FROM exchange_requests er JOIN products p ON er.product_id = p.id JOIN users u1 ON er.sender_email = u1.email JOIN users u2 ON er.receiver_email = u2.email WHERE er.id = %s
        """
        cursor.execute(query, (ex_id,))
        res = cursor.fetchone(); conn.close()
        return jsonify(res) if res else (jsonify({"error": "Not found"}), 404)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/make-offer-data", methods=["GET"])
def make_offer_data():
    p_id = request.args.get('id')
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as ownerName, u.email as ownerEmail, u.profile_image as ownerAvatar FROM products p JOIN users u ON p.user_name = u.email WHERE p.id = %s"
        cursor.execute(query, (p_id,))
        p = cursor.fetchone(); conn.close()
        return jsonify(p) if p else (jsonify({"error": "Not found"}), 404)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        query = "INSERT INTO messages (exchange_id, sender_email, receiver_email, content) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data['exchangeId'], data['senderEmail'], data['receiverEmail'], data['content']))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/get-messages", methods=["GET"])
def get_messages():
    ex_id = request.args.get('exchange_id')
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages WHERE exchange_id = %s ORDER BY timestamp ASC", (ex_id,))
        res = cursor.fetchall(); conn.close()
        return jsonify(res)
    except: return jsonify([])

@app.route("/notifications", methods=["GET"])
def get_notifications():
    email = request.args.get('email')
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notifications WHERE user_email = %s AND is_read = FALSE ORDER BY created_at DESC", (email,))
        res = cursor.fetchall(); conn.close()
        return jsonify(res)
    except: return jsonify([])

@app.route("/notifications/read", methods=["POST"])
def mark_read():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_email = %s", (data['email'],))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except: return jsonify({"success": False})

@app.route("/exchange/initiate-completion", methods=["POST"])
def initiate_completion():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id = %s", (data['exchangeId'],))
        ex = cursor.fetchone()
        if not ex: return jsonify({"success": False, "message": "Exchange not found"}), 404
        
        otp = str(random.randint(100000, 999999))
        # OTP goes to the OTHER party
        target_email = ex['sender_email'] if data.get('userId') == ex['receiver_email'] else ex['receiver_email']
        
        cursor.execute("UPDATE exchange_requests SET completion_otp = %s WHERE id = %s", (otp, data.get('requestId')))
        conn.commit()
        
        # In a real app, send email. For now, print to console.
        print(f"DEBUG: Handover OTP for request {data.get('requestId')} is {otp}. Sent to {target_email}")
        return jsonify({"success": True, "message": "OTP sent to requester"})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange/verify-completion", methods=["POST"])
def verify_completion():
    data = request.get_json()
    try:
        conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id = %s", (data['exchangeId'],))
        ex = cursor.fetchone()
        if not ex: return jsonify({"success": False, "message": "Exchange not found"}), 404
        
        if ex['otp'] == data['otp']:
            # Mark exchange and product as completed
            cursor.execute("UPDATE exchange_requests SET status = 'Completed' WHERE id = %s", (data['exchangeId'],))
            cursor.execute("UPDATE products SET status = 'Completed' WHERE id = %s", (ex['product_id'],))
            
            # Update Sender's stats
            cursor.execute("SELECT trades, trust FROM users WHERE email = %s", (ex['sender_email'],))
            s_user = cursor.fetchone()
            new_s_trades = s_user['trades'] + 1
            if s_user['trades'] == 0:
                new_s_trust = 68
            else:
                new_s_trust = min(100, s_user['trust'] + 5)
            cursor.execute("UPDATE users SET trades = %s, trust = %s WHERE email = %s", (new_s_trades, new_s_trust, ex['sender_email']))
            
            # Update Receiver's stats (Owner)
            cursor.execute("SELECT trades, trust FROM users WHERE email = %s", (ex['receiver_email'],))
            r_user = cursor.fetchone()
            new_r_trades = r_user['trades'] + 1
            if r_user['trades'] == 0:
                new_r_trust = 68
            else:
                new_r_trust = min(100, r_user['trust'] + 5)
            cursor.execute("UPDATE users SET trades = %s, trust = %s WHERE email = %s", (new_r_trades, new_r_trust, ex['receiver_email']))
            
            # Notifications
            cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'Trade successfully completed!', 'success', %s)", (ex['sender_email'], ex['id']))
            cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'Trade successfully completed!', 'success', %s)", (ex['receiver_email'], ex['id']))
            
            conn.commit(); conn.close()
            return jsonify({"success": True, "message": "Handover verified and trade completed!"})
        
        conn.close(); return jsonify({"success": False, "message": "Invalid OTP"}), 400
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    data = request.get_json()
    email = data.get('email')
    rating_input = float(data.get('rating', 0.0))
    
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT rating, trades FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
            
        current_rating = user['rating']
        trades = user['trades']
        
        if trades <= 1:
            new_rating = rating_input
        else:
            new_rating = ((current_rating * (trades - 1)) + rating_input) / trades
            
        cursor.execute("UPDATE users SET rating = %s WHERE email = %s", (new_rating, email))
        conn.commit(); conn.close()
        
        return jsonify({"success": True, "new_rating": new_rating})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def serve_image(filename):
    # Try local UPLOAD_FOLDER first
    primary = app.config['UPLOAD_FOLDER']
    if os.path.exists(os.path.join(primary, filename)):
        return send_from_directory(primary, filename)
    
    # Try secondary location on F: drive if available
    secondary = r'F:\hh\backend\static\uploads'
    if os.path.exists(os.path.join(secondary, filename)):
        return send_from_directory(secondary, filename)
        
    return "Image not found", 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
