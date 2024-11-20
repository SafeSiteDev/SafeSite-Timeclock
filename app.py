from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

# Data directory
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.json")
LOG_FILE = os.path.join(DATA_DIR, "logs.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize files if they don't exist
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        json.dump({}, f)


def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if not username or not password or not role:
            flash("All fields are required!", "error")
            return redirect(url_for("register"))

        users = load_json(USER_FILE)
        if username in users:
            flash("Username already exists!", "error")
            return redirect(url_for("register"))

        users[username] = {"password": password, "role": role}
        save_json(USER_FILE, users)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_json(USER_FILE)
        if username in users and users[username]["password"] == password:
            session["username"] = username
            session["role"] = users[username]["role"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    role = session["role"]
    logs = load_json(LOG_FILE)

    if role == "admin":
        return render_template("admin_dashboard.html", logs=logs, users=load_json(USER_FILE))
    else:
        user_logs = logs.get(username, [])
        return render_template("employee_dashboard.html", logs=user_logs)


@app.route("/clock", methods=["POST"])
def clock():
    if "username" not in session:
        return redirect(url_for("login"))

    action = request.form.get("action")
    username = session["username"]
    logs = load_json(LOG_FILE)

    if username not in logs:
        logs[username] = []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs[username].append({"action": action, "timestamp": timestamp})
    save_json(LOG_FILE, logs)

    flash(f"Clock {action} successful!", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
