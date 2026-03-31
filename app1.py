import os
import re
import random
import smtplib
import mysql.connector
import math
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
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
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- SMTP CONFIGURATION ---
SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 465,
    "email": "localbridgeofficial@gmail.com",
    "password": "jnfd voxt vgwf nqik"
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

    email = email.strip().lower()

    # STEP 1: Format Validation
    if ' ' in email:
        return False, "Email cannot contain spaces"
    
    if email.count('@') != 1:
        return False, "Email must contain exactly one '@'"

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False, "Invalid email format"

    local_part, domain_part = email.split('@')

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
                "content": "TEXT",
                "image_name": "VARCHAR(255)",
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
                    content        TEXT,
                    image_name     VARCHAR(255),
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

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine Formula to calculate distance between two coordinates in km."""
    try:
        # Check for None or (0,0) which indicates missing location data
        if None in [lat1, lon1, lat2, lon2]: return 0.0
        if (float(lat1) == 0.0 and float(lon1) == 0.0) or (float(lat2) == 0.0 and float(lon2) == 0.0):
            return 0.0 # Return 0.0 or a very small fallback to avoid 8000km+ errors
        
        R = 6371.0 # Earth radius in km
        dlat = math.radians(float(lat2) - float(lat1))
        dlon = math.radians(float(lon2) - float(lon1))
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)
    except: return 0.0 # Default fallback on error

# --- EMAIL TEMPLATES ---
EMAIL_STYLE = """
<style>
    body { margin: 0; padding: 0; background-color: #f4f6fb; }
    .wrapper { background-color: #f4f6fb; padding: 30px 15px; }
    .container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .header { background: linear-gradient(135deg, #6e8efb 0%, #a777e3 100%); color: white; padding: 32px 24px; text-align: center; }
    .header h1 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }
    .header p { margin: 6px 0 0; font-size: 13px; opacity: 0.88; }
    .content { padding: 32px 28px; line-height: 1.7; color: #444; }
    .content p { margin: 0 0 14px; }
    .otp-box { background: linear-gradient(135deg, #f0ecff, #e8f0ff); border: 2px dashed #a777e3; border-radius: 12px; padding: 18px; text-align: center; margin: 24px 0; }
    .otp { font-size: 38px; font-weight: 800; color: #6e8efb; letter-spacing: 8px; display: block; }
    .otp-label { font-size: 12px; color: #888; margin-top: 6px; display: block; }
    .divider { border: none; border-top: 1px solid #eee; margin: 20px 0; }
    .note { background: #fff8e1; border-left: 4px solid #ffc107; border-radius: 4px; padding: 10px 14px; font-size: 13px; color: #856404; margin-top: 10px; }
    .btn { display: inline-block; background: linear-gradient(135deg, #6e8efb, #a777e3); color: white; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 14px; margin-top: 16px; }
    .footer { text-align: center; font-size: 12px; color: #aaa; padding: 20px 24px; border-top: 1px solid #f0f0f0; }
    .footer a { color: #a777e3; text-decoration: none; }
</style>
"""

WELCOME_OTP_TEMPLATE = """
<html>
<head>{{STYLE}}</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>&#127968; Welcome to LocalBridge!</h1>
        <p>Your local community trade platform</p>
      </div>
      <div class="content">
        <p>Hi there,</p>
        <p>Thanks for signing up! You're just one step away from joining your local community of traders.</p>
        <p>Please verify your email address using the code below:</p>
        <div class="otp-box">
          <span class="otp">{{otp}}</span>
          <span class="otp-label">Your verification code &mdash; valid for 10 minutes</span>
        </div>
        <hr class="divider">
        <div class="note">&#128274; If you didn't create a LocalBridge account, you can safely ignore this email.</div>
      </div>
      <div class="footer">
        &copy; 2026 LocalBridge &mdash; Connecting Neighbors, Building Communities<br>
        <a href="#">Unsubscribe</a> &middot; <a href="#">Privacy Policy</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

WELCOME_BACK_TEMPLATE = """
<html>
<head>{{STYLE}}</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>&#128075; Welcome Back!</h1>
        <p>LocalBridge &mdash; Your Community Marketplace</p>
      </div>
      <div class="content">
        <p>Hi {{name}},</p>
        <p>Great to see you again! You've successfully signed in to your LocalBridge account.</p>
        <p>You can now browse listings, make offers, and connect with neighbors nearby.</p>
        <hr class="divider">
        <div class="note">&#128680; If this wasn't you, <strong>secure your account immediately</strong> by resetting your password.</div>
      </div>
      <div class="footer">
        &copy; 2026 LocalBridge &mdash; Connecting Neighbors, Building Communities<br>
        <a href="#">Unsubscribe</a> &middot; <a href="#">Privacy Policy</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

RESET_PASSWORD_TEMPLATE = """
<html>
<head>{{STYLE}}</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>&#128274; Password Reset Request</h1>
        <p>LocalBridge Account Security</p>
      </div>
      <div class="content">
        <p>Hello,</p>
        <p>We received a request to reset the password for your LocalBridge account.</p>
        <p>Enter the recovery code below in the app to create a new password:</p>
        <div class="otp-box">
          <span class="otp">{{otp}}</span>
          <span class="otp-label">Recovery code &mdash; expires in 10 minutes</span>
        </div>
        <hr class="divider">
        <div class="note">&#128274; If you didn't request a password reset, ignore this email. Your account remains secure.</div>
      </div>
      <div class="footer">
        &copy; 2026 LocalBridge &mdash; Connecting Neighbors, Building Communities<br>
        <a href="#">Unsubscribe</a> &middot; <a href="#">Privacy Policy</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

PASSWORD_UPDATED_TEMPLATE = """
<html>
<head>{{STYLE}}</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>&#9989; Password Changed Successfully</h1>
        <p>LocalBridge Account Security</p>
      </div>
      <div class="content">
        <p>Hello,</p>
        <p>Your LocalBridge account password has been updated successfully.</p>
        <p>You can now log in with your new password. If you did not make this change, please contact our support team immediately.</p>
        <hr class="divider">
        <div class="note">&#128680; Didn't change your password? Contact support right away to secure your account.</div>
      </div>
      <div class="footer">
        &copy; 2026 LocalBridge &mdash; Connecting Neighbors, Building Communities<br>
        <a href="#">Unsubscribe</a> &middot; <a href="#">Privacy Policy</a>
      </div>
    </div>
  </div>
</body>
</html>
"""

TRADE_OTP_TEMPLATE = """
<html>
<head>{EMAIL_STYLE}</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>&#129309; Trade Handover Code</h1>
        <p>LocalBridge Secure Exchange</p>
      </div>
      <div class="content">
        <p>Dear Neighbor,</p>
        <p>Your One Time Password (OTP) for verifying your product handover is:</p>
        <div class="otp-container">
          <span class="otp">{otp}</span>
          <span class="otp-label">Handover code &mdash; expires in 5 minutes</span>
        </div>
        <hr class="divider">
        <div class="note">&#128274; Do not share this OTP with anyone except the neighbor you are trading with.</div>
      </div>
      <div class="footer">
        &copy; 2026 LocalBridge &mdash; Connecting Neighbors, Building Communities<br>
        <a href="#">Unsubscribe</a> &middot; <a href="#">Privacy Policy</a>
      </div>
    </div>
  </div>
</body>
</html>
"""


def send_email(receiver_email, subject, body, is_html=True):
    """Sends a professional email with HTML support."""
    try:
        msg = MIMEMultipart()
        msg['From'] = str(SMTP_CONFIG["email"])
        msg['To'] = str(receiver_email)
        msg['Subject'] = str(subject)
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        host = str(SMTP_CONFIG["server"])
        port = int(SMTP_CONFIG["port"])
        server = smtplib.SMTP_SSL(host, port, timeout=10)
        server.login(str(SMTP_CONFIG["email"]), str(SMTP_CONFIG["password"]))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP ERROR: {e}")
        return False

def send_welcome_email(receiver_email, name):
    """Sends a welcome back email on successful login."""
    return send_email(receiver_email, "\U0001f44b You're Signed In to LocalBridge", WELCOME_BACK_TEMPLATE.format(name=name))

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
    email = data.get('email', '').strip().lower()
    is_valid, err = is_valid_email(email)
    if not is_valid: return jsonify({"success": False, "message": err}), 400
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({"success": False, "message": "Email not found", "notRegistered": True}), 404
        
        otp = str(random.randint(1000, 9999))
        otp_store[email] = otp
        cursor.execute("UPDATE users SET reset_otp = %s WHERE email = %s", (otp, email))
        
        # Professional Email Template
        html = RESET_PASSWORD_TEMPLATE.replace('{{STYLE}}', EMAIL_STYLE).replace('{{otp}}', otp)
        if send_email(email, "Reset Your LocalBridge Password", html):
            conn.commit(); conn.close()
            return jsonify({"success": True, "message": "Verification code sent"})
        else:
            conn.close()
            return jsonify({"success": False, "message": "Failed to send email"}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/send-signup-otp", methods=["POST"])
def send_signup_otp():
    try:
        data = request.get_json(); email = data.get('email', '').strip().lower()
        is_valid, err = is_valid_email(email)
        if not is_valid: return jsonify({"success": False, "message": err}), 400
        
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already exists", "isExistingUser": True}), 400
            
        otp = str(random.randint(1000, 9999))
        otp_store[email] = otp
        
        # Professional Email Template
        html = WELCOME_OTP_TEMPLATE.replace('{{STYLE}}', EMAIL_STYLE).replace('{{otp}}', otp)
        if send_email(email, "\u26a1 Verify Your LocalBridge Account", html):
            conn.close()
            return jsonify({"success": True, "message": "Verification code sent to your email"})
        else:
            conn.close()
            return jsonify({"success": False, "message": "Failed to send email"}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route('/product/<int:id>')
def product_details_page(id): return render_template('product_details.html', product_id=id)

@app.route("/make-offer")
def make_offer_page(): return render_template('make_offer.html')

# --- API ENDPOINTS ---

def is_valid_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one capital letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        return False, "Password must contain at least one special character"
    return True, ""

@app.route("/update-password", methods=["POST"])
def update_password_api():
    data = request.get_json()
    email = data.get('email'); old_pw = data.get('old_password'); new_pw = data.get('new_password')
    
    # Password Validation
    is_valid, err = is_valid_password(new_pw)
    if not is_valid: return jsonify({"success": False, "message": err}), 400

    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], old_pw):
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
    data = request.get_json(); email = data.get('email', '').strip().lower()
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
        if send_email(email, "\U0001f3e0 Verify Your LocalBridge Account", WELCOME_OTP_TEMPLATE.replace('{{STYLE}}', EMAIL_STYLE).replace('{{otp}}', otp)):
            conn.close(); return jsonify({"success": True, "isExistingUser": False})
        else:
            conn.close(); return jsonify({"success": False, "message": "Failed to send verification email"}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(); email = data.get('email', '').strip().lower(); otp = data.get('otp')
    if otp_store.get(email) == otp: return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password_flow():
    if request.method == "GET":
        return render_template('reset_password.html')
    data = request.get_json()
    email = data.get('email', '').strip().lower(); otp = str(data.get('otp', '')); new_pw = data.get('password')

    # Password Validation
    is_valid, err = is_valid_password(new_pw)
    if not is_valid: return jsonify({"success": False, "message": err}), 400

    # Check otp_store first, then fall back to DB column
    stored_otp = otp_store.get(email)
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT reset_otp FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        db_otp = str(user['reset_otp']) if user and user.get('reset_otp') else None

        otp_valid = (stored_otp and stored_otp == otp) or (db_otp and db_otp == otp)
        if otp_valid:
            hashed_pw = generate_password_hash(new_pw)
            cursor.execute("UPDATE users SET password = %s, reset_otp = NULL WHERE email = %s", (hashed_pw, email))
            conn.commit(); conn.close()
            body = PASSWORD_UPDATED_TEMPLATE.replace('{{STYLE}}', EMAIL_STYLE)
            send_email(email, "\u2705 Your LocalBridge Password Has Been Reset", body)
            return jsonify({"success": True, "message": "Password reset successful"})
        conn.close()
        return jsonify({"success": False, "message": "Invalid or expired recovery code"}), 400
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(); email = data.get('email', '').strip().lower()
        
        # OTP Verification
        otp = data.get('otp')
        if not otp or otp_store.get(email) != str(otp):
            return jsonify({"success": False, "message": "Invalid or expired verification code"}), 400
        
        # Email Validation
        is_valid, err = is_valid_email(email)
        if not is_valid: return jsonify({"success": False, "message": err}), 400
        
        password = data.get('password')
        # Password Validation
        is_valid, err = is_valid_password(password)
        if not is_valid: return jsonify({"success": False, "message": err}), 400

        hashed_pw = generate_password_hash(password)
        name = data.get('name') or data.get('fullName')
        location = data.get('location', '')
        
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password, location) VALUES (%s, %s, %s, %s)", (name, email, hashed_pw, location))
        u_id = cursor.lastrowid; conn.commit()
        
        # Clear OTP after successful registration
        if email in otp_store: del otp_store[email]
        
        conn.close()
        return jsonify({"success": True, "userId": u_id})
    except mysql.connector.Error as err:
        if err.errno == 1062: return jsonify({"success": False, "message": "Email already registered", "isExistingUser": True}), 400
        return jsonify({"success": False, "message": f"Database error: {err}"}), 500
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password')

    # Basic Email String Validation
    is_valid, err = is_valid_email(email)
    if not is_valid: return jsonify({"success": False, "message": err}), 400

    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone(); conn.close()
        
        if not user:
            return jsonify({"success": False, "message": "Email not registered", "notRegistered": True}), 404
        
        if check_password_hash(user['password'], password):
            body = WELCOME_BACK_TEMPLATE.replace('{{STYLE}}', EMAIL_STYLE).replace('{{name}}', user['name'])
            send_email(email, "\U0001f44b You're Signed In to LocalBridge", body)
            return jsonify({"success": True, "userId": user['id']})
        
        return jsonify({"success": False, "message": "Incorrect password"}), 401
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
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET location = %s WHERE email = %s", (location, email))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": "Location updated"})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    user_email = request.args.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE (p.status IS NULL OR p.status = 'Active') ORDER BY p.id DESC")
        res = cursor.fetchall()
        requested_ids = set()
        if user_email:
            cursor.execute("SELECT product_id FROM exchange_requests WHERE sender_email = %s AND status != 'Cancelled'", (user_email,))
            requested_ids = {int(row['product_id']) for row in cursor.fetchall()}
            
        lat_raw = request.args.get('lat')
        lng_raw = request.args.get('lng')
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except:
            lat = None; lng = None
            
        conn.close()
        for row in res:
            row['user_name'] = row['real_user_name'] if row.get('real_user_name') else row['user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            
            # Real-time distance calculation
            if lat is not None and lng is not None and row.get('lat') is not None and row.get('lng') is not None:
                dist = calculate_distance(lat, lng, row['lat'], row['lng'])
                row['distance'] = max(0.1, dist)
            else:
                row['distance'] = float(row.get('distance') if row.get('distance') is not None else 0.0)
                
            row['isRequested'] = row['id'] in requested_ids
        return jsonify(res)
    except: return jsonify([])

@app.route("/filter_products", methods=["GET"])
def filter_products():
    cat = request.args.get('category', 'All')
    dist = request.args.get('distance', 'Any')
    cond = request.args.get('condition', 'Any')
    user_email = request.args.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE (p.status IS NULL OR p.status = 'Active')"
        params = []
        if cat != 'All': query += " AND p.category = %s"; params.append(cat)
        if cond != 'Any': query += " AND p.item_condition = %s"; params.append(cond)
        if dist != 'Any':
            try:
                max_d = float(dist.split()[0])
                query += " AND p.distance <= %s"; params.append(max_d)
            except: pass
        query += " ORDER BY p.id DESC"
        cursor.execute(query, tuple(params))
        res = cursor.fetchall()
        requested_ids = set()
        if user_email:
            cursor.execute("SELECT product_id FROM exchange_requests WHERE sender_email = %s AND status != 'Cancelled'", (user_email,))
            requested_ids = {int(row['product_id']) for row in cursor.fetchall()}
        lat_raw = request.args.get('lat')
        lng_raw = request.args.get('lng')
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except:
            lat = None; lng = None
            
        conn.close()
        for row in res:
            row['user_name'] = row['real_user_name'] if row.get('real_user_name') else row['user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            
            # Real-time distance calculation
            if lat is not None and lng is not None and row.get('lat') is not None and row.get('lng') is not None:
                dist = calculate_distance(lat, lng, row['lat'], row['lng'])
                row['distance'] = max(0.1, dist)
            else:
                row['distance'] = float(row.get('distance') if row.get('distance') is not None else 0.0)
            row['isRequested'] = row['id'] in requested_ids
        return jsonify(res)
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
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        p = cursor.fetchone(); conn.close()
        if p:
            p['user_name'] = p['real_user_name'] if p.get('real_user_name') else p['user_name']
            
            # Real-time distance calculation
            if lat is not None and lng is not None and p.get('lat') is not None and p.get('lng') is not None:
                dist = calculate_distance(lat, lng, p['lat'], p['lng'])
                p['distance'] = max(0.1, dist)
            return jsonify(p)
        return jsonify({"error": "Not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/delete-product", methods=["POST"])
def delete_product():
    data = request.get_json()
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
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
        user = cursor.fetchone()
        user_rating = user['rating'] if user else 0.0
        
        cursor = conn.cursor()
        query = "INSERT INTO products (name, description, image_name, user_name, category, expiry_date, freshness, used_for, item_condition, return_offer, quantity, unit, lat, lng, rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        lat_val = data.get('lat'); lng_val = data.get('lng')
        # Ensure we store None if empty string is passed
        lat_val = float(lat_val) if lat_val else None
        lng_val = float(lng_val) if lng_val else None
        
        cursor.execute(query, (data.get('name'), data.get('description'), filename, user_name, data.get('category'), data.get('expiry_date'), data.get('freshness'), data.get('used_for'), data.get('item_condition'), data.get('return_offer'), data.get('quantity'), data.get('unit'), lat_val, lng_val, user_rating))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

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
        exchange_id = cursor.lastrowid
        cursor.execute("SELECT name FROM users WHERE email = %s", (sender,))
        s_name = cursor.fetchone()[0]
        cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, %s, 'info', %s)", (receiver, f"{s_name} requested your product!", exchange_id))
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
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"incoming": [], "outgoing": []})
        email = user_row['email']
        q = "SELECT er.*, p.name as productName, p.image_name as productImage, u.name as partnerName, u.email as partnerEmail, u.profile_image as partnerAvatar FROM exchange_requests er JOIN products p ON er.product_id = p.id JOIN users u ON (er.sender_email = u.email OR er.receiver_email = u.email) AND u.email != %s WHERE er.sender_email = %s OR er.receiver_email = %s"
        cursor.execute(q, (email, email, email))
        res = cursor.fetchall(); conn.close()
        def fmt(r):
            return {"id": r['id'], "productName": r['productName'], "productImage": r['productImage'], "userName": r['partnerName'], "userAvatar": r['partnerAvatar'], "partnerEmail": r['partnerEmail'], "date": str(r['date']) if r['date'] is not None else None, "time": str(r['time']) if r['time'] is not None else None, "location": r['location'], "status": r['status'], "offer": r['offer_text'], "offerImage": r.get('offer_image'), "productId": r['product_id'], "senderEmail": r['sender_email'], "receiverEmail": r['receiver_email'], "lat": r.get('lat'), "lng": r.get('lng')}
        email_lower = email.lower()
        return jsonify({"incoming": [fmt(r) for r in res if r['receiver_email'].lower() == email_lower], "outgoing": [fmt(r) for r in res if r['sender_email'].lower() == email_lower]})
    except Exception as e:
        print(f"Error in get_my_requests: {e}")
        return jsonify({"incoming": [], "outgoing": []})

@app.route("/exchange/update", methods=["POST"])
def update_exchange():
    data = request.get_json()
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id=%s", (data['requestId'],))
        old = cursor.fetchone()
        
        # Check if meetup details are being updated
        is_meetup_update = any(data.get(k) is not None for k in ['date', 'time', 'location'])
        
        query = "UPDATE exchange_requests SET status=%s, date=COALESCE(%s, date), time=COALESCE(%s, time), location=COALESCE(%s, location), lat=COALESCE(%s, lat), lng=COALESCE(%s, lng) WHERE id=%s"
        cursor.execute(query, (data['status'], data.get('date'), data.get('time'), data.get('location'), data.get('lat'), data.get('lng'), data['requestId']))
        
        if data['status'] == 'Accepted' and old['status'] != 'Accepted':
            cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'Your request was accepted!', 'accepted', %s)", (old['sender_email'], old['id']))
        elif data['status'] == 'Cancelled':
            # Notify the partner about the cancellation
            partner_email = old['receiver_email'] if data.get('isSender') else old['sender_email']
            cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'An exchange request was cancelled.', 'info', %s)", (partner_email, old['id']))
        elif is_meetup_update:
            # Notify the partner about the meetup update
            updater_email = data.get('current_user_email')
            if updater_email:
                partner_email = old['receiver_email'] if updater_email == old['sender_email'] else old['sender_email']
                cursor.execute("SELECT name FROM users WHERE email = %s", (updater_email,))
                updater_name = cursor.fetchone()['name']
                cursor.execute("SELECT name FROM products WHERE id = %s", (old['product_id'],))
                product_name = cursor.fetchone()['name']
                cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, %s, 'info', %s)", (partner_email, f"{updater_name} updated meetup details for {product_name}", old['id']))
        
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
        if res:
            res['date'] = str(res['date']) if res.get('date') is not None else None
            res['time'] = str(res['time']) if res.get('time') is not None else None
            res['created_at'] = str(res['created_at']) if res.get('created_at') is not None else None
            return jsonify(res)
        return jsonify({"error": "Not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/make-offer-data", methods=["GET"])
def make_offer_data():
    p_id = request.args.get('id')
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"error": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as ownerName, u.email as ownerEmail, u.profile_image as ownerAvatar FROM products p JOIN users u ON p.user_name = u.email WHERE p.id = %s"
        cursor.execute(query, (p_id,))
        p = cursor.fetchone(); conn.close()
        return jsonify(p) if p else (jsonify({"error": "Not found"}), 404)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/send-message", methods=["POST"])
def send_message():
    try:
        if request.is_json:
            data = request.get_json()
            exchange_id = data.get('exchangeId')
            sender_email = data.get('senderEmail')
            receiver_email = data.get('receiverEmail')
            content = data.get('content')
            image_filename = None
        else:
            # Handle Multipart (Text + Image)
            exchange_id = request.form.get('exchangeId')
            sender_email = request.form.get('senderEmail')
            receiver_email = request.form.get('receiverEmail')
            content = request.form.get('content')
            image_filename = None
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    image_filename = f"chat_{datetime.now().timestamp()}_{secure_filename(file.filename)}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor()
        query = "INSERT INTO messages (exchange_id, sender_email, receiver_email, content, image_name) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (exchange_id, sender_email, receiver_email, content, image_filename))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/get-messages", methods=["GET"])
def get_messages():
    ex_id = request.args.get('exchange_id')
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages WHERE exchange_id = %s ORDER BY timestamp ASC", (ex_id,))
        res = cursor.fetchall(); conn.close()
        return jsonify(res)
    except: return jsonify([])

@app.route("/notifications", methods=["GET"])
def get_notifications():
    email = request.args.get('email')
    try:
        conn = get_db_connection()
        if not conn: return jsonify([])
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notifications WHERE user_email = %s AND is_read = FALSE ORDER BY created_at DESC", (email,))
        res = cursor.fetchall(); conn.close()
        return jsonify(res)
    except: return jsonify([])

@app.route("/notifications/read", methods=["POST"])
def mark_read():
    data = request.get_json()
    try:
        conn = get_db_connection()
        if not conn: return jsonify({"success": False})
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_email = %s", (data['email'],))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except: return jsonify({"success": False})

@app.route("/exchange/initiate-completion", methods=["POST"])
def initiate_completion():
    data = request.get_json()
    try:
        ex_id = data.get('exchangeId') or data.get('requestId')
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id = %s", (ex_id,))
        ex = cursor.fetchone()
        if not ex: return jsonify({"success": False, "message": "Exchange not found"}), 404
        
        # Security check: Only the receiver (owner of the product) can initiate completion
        user_id_raw = data.get('userId')
        user_email = str(user_id_raw) if user_id_raw else None
        
        # If userId is numeric, resolve it to email
        if user_email and user_email.isdigit():
            cursor.execute("SELECT email FROM users WHERE id = %s", (int(user_email),))
            row = cursor.fetchone()
            if row: user_email = row['email']

        if ex['receiver_email'] != user_email:
            conn.close()
            return jsonify({"success": False, "message": f"Unauthorized: User {user_email} cannot mark handover for this exchange owned by {ex['receiver_email']}."}), 403
            
        otp = str(random.randint(100000, 999999))
        cursor.execute("UPDATE exchange_requests SET otp = %s WHERE id = %s", (otp, ex_id))
        conn.commit()
        conn.close()
        
        # Professional Email Template
        html = TRADE_OTP_TEMPLATE.replace('{EMAIL_STYLE}', EMAIL_STYLE).replace('{otp}', otp)
        if send_email(ex['sender_email'], "🤝 LocalBridge Trade Completion Code", html, is_html=True):
            return jsonify({"success": True, "message": "OTP sent to requester"})
        else:
            return jsonify({"success": False, "message": "Failed to send email"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange/verify-completion", methods=["POST"])
def verify_completion():
    data = request.get_json()
    try:
        ex_id = data.get('exchangeId') or data.get('requestId')
        conn = get_db_connection()
        if not conn: return jsonify({"success": False, "message": "DB error"}), 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM exchange_requests WHERE id = %s", (ex_id,))
        ex = cursor.fetchone()
        if not ex: return jsonify({"success": False, "message": "Exchange not found"}), 404
        
        if ex['otp'] == data['otp']:
            # Mark exchange and product as completed
            cursor.execute("UPDATE exchange_requests SET status = 'Completed' WHERE id = %s", (ex_id,))
            cursor.execute("UPDATE products SET status = 'Completed' WHERE id = %s", (ex['product_id'],))
            
            # Cancel all other pending requests for this product and notify users
            cursor.execute("SELECT id, sender_email FROM exchange_requests WHERE product_id = %s AND id != %s AND status != 'Cancelled'", (ex['product_id'], ex_id))
            other_requests = cursor.fetchall()
            for req in other_requests:
                cursor.execute("UPDATE exchange_requests SET status = 'Cancelled' WHERE id = %s", (req['id'],))
                cursor.execute("INSERT INTO notifications (user_email, message, type, related_id) VALUES (%s, 'The product you requested has been traded with someone else. Your request was cancelled automatically.', 'info', %s)", (req['sender_email'], req['id']))
            
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
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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
        
        # Calculate new average rating
        # If trades is 0, just set the rating. 
        # But rating is usually submitted after a trade, so trades should be >= 1
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
    # Try the configured UPLOAD_FOLDER (F:\backend\static\uploads)
    primary = app.config['UPLOAD_FOLDER']
    if os.path.exists(os.path.join(primary, filename)):
        return send_from_directory(primary, filename)
    
    # Fallback to local web uploads if name matches
    secondary = r'd:\web\static\uploads'
    if os.path.exists(os.path.join(secondary, filename)):   
        return send_from_directory(secondary, filename)
        
    return "Image not found", 404

if __name__ == "__main__": 
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000) 
