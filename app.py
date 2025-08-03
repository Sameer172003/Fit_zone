from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import csv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "my_secret_key"

# ========== MAIL CONFIGURATION ==========
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ojhasameer24@gmail.com'
app.config['MAIL_PASSWORD'] = 'bmhh cozq raed qdwo'

mail = Mail(app)

# ========== DATABASE INITIALIZATION ==========
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            email TEXT,
            phone TEXT,
            months INTEGER
        )
    ''')

    conn.commit()
    conn.close()

# ========== ROUTES ==========
@app.route("/")
def home():
    return render_template("base.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Registered successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('about'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')

@app.route('/contact')
def contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('contact.html')

@app.route("/membership", methods=["GET", "POST"])
def membership():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        phone = request.form['phone']
        months = int(request.form['months'])

        # Save to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO members (name, age, email, phone, months)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, age, email, phone, months))
        conn.commit()
        conn.close()

        # Save to CSV
        file_exists = os.path.isfile("member_data.csv")
        with open("member_data.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Name", "Age", "Email", "Phone", "Months"])
            writer.writerow([name, age, email, phone, months])

        return redirect(url_for('pay', months=months))

    return render_template("form.html")

@app.route("/pay", methods=["GET", "POST"])
def pay():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    months = int(request.args.get('months', 1))
    amount = months  # ₹1 per month

    if request.method == 'POST':
        return redirect(url_for('confirm', months=months))

    return render_template("pay.html", amount=amount, months=months)

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method == 'POST':
        months = int(request.form.get('months', 1))
    else:
        months = int(request.args.get('months', 1))

    amount = months

    # Get latest member's email
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, name FROM members ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        recipient_email, name = result
        try:
            msg = Message(
                subject="✅ Gym Membership Payment Confirmation",
                sender=app.config['MAIL_USERNAME'],
                recipients=[recipient_email],
                body=f"Hello {name},\n\nYour payment of ₹{amount} for a {months}-month gym membership has been successfully received.\n\nThank you for joining FitZone!\n\n- FitZone Team"
            )
            mail.send(msg)
            flash("Payment confirmation email sent successfully!", "success")
        except Exception as e:
            print("Email Sending Error:", e)
            flash("Payment confirmed, but email could not be sent.", "warning")

    return render_template("confirm.html", months=months, amount=amount)

# ========== RUN ==========
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
