import os
import random
import smtplib
import mysql.connector
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app)

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "app_db"
}

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- SMTP CONFIGURATION (For OTP) ---
SMTP_CONFIG = {
    "server": "smtp.gmail.com",
    "port": 465,
    "email": "pavanofficial897@gmail.com",
    "password": "hvwk usmc zjbk oakc"
}

otp_store = {}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def generate_ai_insight(product):
    """Automated AI Insight Generator for Home Screen"""
    name = str(product.get('name', '')).lower()
    cat = str(product.get('category', '')).lower()
    dist = product.get('distance', 0)
    rating = product.get('rating', 0)

    if "bread" in name or "bakery" in cat:
        return "AI: Freshly posted! Bakery items are in high demand today."
    if dist < 1.0:
        return "AI: Local Gem! This item is just a 5-minute walk from you."
    if rating > 4.8:
        return "AI: Top Rated! Shared by a highly trusted community neighbor."
    if "produce" in cat or "fruit" in name or "veg" in name:
        return "AI: Healthy Pick! This matches your preference for fresh produce."
    if "other" in cat:
        return "AI: Rare Find! A unique item matching your local exchange circle."
    return "AI: Quality verified. Recommended for a fair and quick exchange."

def send_email(receiver_email, otp):
    # CRITICAL: Always print to console for development bypass
    print(f"\n[SECURITY] OTP for {receiver_email} is: {otp}\n")
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = SMTP_CONFIG["email"], receiver_email, "LocalLoop AI Verification"
        msg.attach(MIMEText(f"Your LocalLoop verification code is: {otp}", 'plain'))
        server = smtplib.SMTP_SSL(SMTP_CONFIG["server"], SMTP_CONFIG["port"], timeout=5)
        server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"SMTP ERROR (Check your App Password): {e}")
        return True

# --- 1. AUTHENTICATION & PROFILE ---

@app.route("/create-account", methods=["POST"])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": True, "isExistingUser": True})

        otp = str(random.randint(1000, 9999))
        otp_store[email] = otp
        send_email(email, otp)
        conn.close()
        return jsonify({"success": True, "isExistingUser": False})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    if otp_store.get(email) == otp:
        return jsonify({"success": True, "message": "OTP verified"})
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        password = data.get('password')
        hashed_pw = generate_password_hash(password)
        name = data.get('name') or data.get('fullName')
        email = data.get('email')
        location = data.get('location', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO users (name, email, password, location, trades, posted, rating, trust) VALUES (%s, %s, %s, %s, 0, 0, 5.0, 100)"
        cursor.execute(query, (name, email, hashed_pw, location))
        user_id = cursor.lastrowid
        conn.commit(); conn.close()
        return jsonify({"success": True, "userId": user_id})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (data.get('email'),))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], data.get('password')):
            return jsonify({"success": True, "userId": user['id']})
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/user-details", methods=["GET"])
def get_user_details():
    email = request.args.get('email')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, email, location, phone, bio, preferred_exchange, trades, posted, rating, trust, profile_image FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone(); conn.close()
        return jsonify(user) if user else (jsonify({"error": "Not found"}), 404)
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/update-location", methods=["POST"])
def update_location():
    data = request.get_json()
    email = data.get('email')
    location = data.get('location')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET location = %s WHERE email = %s", (location, email))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": "Location updated"})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/update-profile", methods=["POST"])
def update_profile():
    try:
        filename = None
        if 'image' in request.files:
            file = request.files['image']
            filename = f"profile_{datetime.now().timestamp()}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        data = request.form
        email = data.get('email')
        conn = get_db_connection()
        cursor = conn.cursor()

        if filename:
            query = "UPDATE users SET name=%s, phone=%s, location=%s, bio=%s, preferred_exchange=%s, profile_image=%s WHERE email=%s"
            cursor.execute(query, (data.get('name'), data.get('phone'), data.get('location'), data.get('bio'), data.get('preferred_exchange'), filename, email))
        else:
            query = "UPDATE users SET name=%s, phone=%s, location=%s, bio=%s, preferred_exchange=%s WHERE email=%s"
            cursor.execute(query, (data.get('name'), data.get('phone'), data.get('location'), data.get('bio'), data.get('preferred_exchange'), email))

        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

# --- 2. PRODUCTS ---

def get_product_coords(product_id):
    """Generate deterministic coordinates based on product ID for demo purposes"""
    random.seed(product_id)
    lat_off = (random.random() - 0.5) * 0.05
    lng_off = (random.random() - 0.5) * 0.05
    return 17.3850 + lat_off, 78.4867 + lng_off # Central Hyderabad location

@app.route("/products", methods=["GET"])
def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email ORDER BY p.id DESC"
        cursor.execute(query)
        res = cursor.fetchall(); conn.close()
        for row in res:
            if row.get('real_user_name'): row['user_name'] = row['real_user_name']
            row['rating'] = float(row['rating']) if row.get('rating') else 0.0
            row['distance'] = float(row['distance']) if row.get('distance') else 0.0
            row['ai_insight'] = generate_ai_insight(row)
            lat, lng = get_product_coords(row['id'])
            row['lat'], row['lng'] = lat, lng
        return jsonify(res)
    except: return jsonify([])

@app.route("/product-details", methods=["GET"])
def get_product_details():
    product_id = request.args.get('id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.*, u.name as real_user_name, u.email as ownerEmail, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE p.id = %s"
        cursor.execute(query, (product_id,))
        p = cursor.fetchone(); conn.close()
        if p:
            if p.get('real_user_name'): p['user_name'] = p['real_user_name']
            lat, lng = get_product_coords(p['id'])
            p['lat'], p['lng'] = lat, lng
            return jsonify(p)
        return jsonify({"error": "Not found"}), 404
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/delete-product", methods=["POST"])
def delete_product():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (data.get('id'),))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/my-products", methods=["GET"])
def get_my_products():
    user_email = request.args.get('user_name')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT p.*, u.name as real_user_name, u.profile_image as userAvatar FROM products p LEFT JOIN users u ON p.user_name = u.email WHERE p.user_name = %s ORDER BY p.id DESC", (user_email,))
        res = cursor.fetchall(); conn.close()
        for row in res:
            if row.get('real_user_name'): row['user_name'] = row['real_user_name']
        return jsonify(res)
    except: return jsonify([])

@app.route("/upload-product", methods=["POST"])
def upload_product():
    try:
        file = request.files['image']
        filename = f"{datetime.now().timestamp()}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO products (name, description, image_name, user_name, category, expiry_date, freshness, used_for, item_condition, return_offer) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (request.form.get('name'), request.form.get('description'), filename, request.form.get('user_name'), request.form.get('category'), request.form.get('expiry_date'), request.form.get('freshness'), request.form.get('used_for'), request.form.get('item_condition'), request.form.get('return_offer')))
        cursor.execute("UPDATE users SET posted = posted + 1 WHERE email = %s", (request.form.get('user_name'),))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

# --- 3. EXCHANGE & MESSAGING ---

@app.route("/exchange/request", methods=["POST"])
def request_exchange():
    try:
        offer_image_filename = None
        if 'offer_image' in request.files:
            file = request.files['offer_image']
            offer_image_filename = f"offer_{datetime.now().timestamp()}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], offer_image_filename))

        data = request.form
        user_id = data.get('userId')
        product_id = data.get('productId')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_name FROM products WHERE id = %s", (product_id,))
        receiver_email = cursor.fetchone()[0]
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        sender_email = cursor.fetchone()[0]

        query = "INSERT INTO exchange_requests (sender_email, receiver_email, product_id, date, time, location, offer_text, offer_image, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Requested')"
        cursor.execute(query, (sender_email, receiver_email, product_id, data.get('date'), data.get('time'), data.get('location'), data.get('offer_text'), offer_image_filename))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/exchange/my-requests", methods=["GET"])
def get_my_requests():
    user_id = request.args.get('userId')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        user_email = cursor.fetchone()['email']

        q_inc = "SELECT er.*, p.name as productName, p.image_name as productImage, u.name as partnerName, u.profile_image as partnerAvatar FROM exchange_requests er JOIN products p ON er.product_id = p.id JOIN users u ON er.sender_email = u.email WHERE er.receiver_email = %s"
        cursor.execute(q_inc, (user_email,))
        inc = cursor.fetchall()

        q_out = "SELECT er.*, p.name as productName, p.image_name as productImage, u.name as partnerName, u.profile_image as partnerAvatar FROM exchange_requests er JOIN products p ON er.product_id = p.id JOIN users u ON er.receiver_email = u.email WHERE er.sender_email = %s"
        cursor.execute(q_out, (user_email,))
        out = cursor.fetchall(); conn.close()

        def fmt(res):
            return [{
                "id": r['id'], "productName": r['productName'], "productImage": r['productImage'],
                "userName": r['partnerName'], "userAvatar": r['partnerAvatar'], "date": r['date'], "time": r['time'], "location": r['location'],
                "status": r['status'], "offer": r['offer_text'], "offerImage": r.get('offer_image'),
                "productId": r['product_id'], "senderEmail": r['sender_email'], "receiverEmail": r['receiver_email']
            } for r in res]

        return jsonify({"incoming": fmt(inc), "outgoing": fmt(out)})
    except Exception as e: return jsonify({"incoming": [], "outgoing": []})

@app.route("/exchange/update", methods=["POST"])
def update_exchange():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE exchange_requests SET status=%s, date=COALESCE(%s, date), time=COALESCE(%s, time), location=COALESCE(%s, location) WHERE id=%s"
        cursor.execute(query, (data['status'], data.get('date'), data.get('time'), data.get('location'), data['requestId']))

        if data.get('date') or data.get('time') or data.get('location'):
            cursor.execute("SELECT sender_email, receiver_email FROM exchange_requests WHERE id = %s", (data['requestId'],))
            row = cursor.fetchone()
            if row:
                content = f"Proposal updated: {data.get('date') or ''} {data.get('time') or ''} at {data.get('location') or ''}"
                cursor.execute("INSERT INTO messages (exchange_id, sender_email, receiver_email, content) VALUES (%s, 'System', %s, %s)", (data['requestId'], row[0], content))
                cursor.execute("INSERT INTO messages (exchange_id, sender_email, receiver_email, content) VALUES (%s, 'System', %s, %s)", (data['requestId'], row[1], content))

        conn.commit(); conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)}), 500

@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO messages (exchange_id, sender_email, receiver_email, content) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (data['exchangeId'], data['senderEmail'], data['receiverEmail'], data['content']))
        conn.commit(); conn.close()
        return jsonify({"success": True})
    except: return jsonify({"success": False}), 500

@app.route("/get-messages", methods=["GET"])
def get_messages():
    exchange_id = request.args.get('exchange_id')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages WHERE exchange_id = %s ORDER BY timestamp ASC", (exchange_id,))
        res = cursor.fetchall(); conn.close()
        return jsonify(res)
    except: return jsonify([])

@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
