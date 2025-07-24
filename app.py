import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'your-very-secret-key-change-this'

# --- CONFIG & USER MANAGEMENT ---
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
BOT_WORKER_SERVICE_ID = os.getenv("BOT_WORKER_SERVICE_ID")

USERS = {
    "admin": {"password": "admin_password", "role": "admin"},
    "client_a": {"password": "123", "role": "client"},
    "client_b": {"password": "456", "role": "client"}
}

def get_bot_status_and_logs():
    """Gets the status and logs for the single bot worker from the Render API."""
    if not BOT_WORKER_SERVICE_ID or not RENDER_API_KEY:
        return "Not Configured", "Admin needs to set environment variables in the dashboard service."

    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    
    status_url = f"https://api.render.com/v1/services/{BOT_WORKER_SERVICE_ID}"
    status_res = requests.get(status_url, headers=headers)
    status = "Unknown"
    if status_res.status_code == 200:
        state = status_res.json().get('serviceDetails', {}).get('state', 'Unknown')
        # Make states more user-friendly
        if state == 'live': status = 'Running'
        elif state == 'suspended': status = 'Stopped'
        else: status = state.replace('_', ' ').title()

    logs_url = f"https://api.render.com/v1/services/{BOT_WORKER_SERVICE_ID}/logs?limit=100"
    logs_res = requests.get(logs_url, headers=headers)
    logs = "Could not fetch logs."
    if logs_res.status_code == 200:
        log_items = [item['log']['message'] for item in reversed(logs_res.json())]
        logs = "\n".join(log_items) if log_items else "No logs found."

    return status, logs

# --- FLASK ROUTES ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session["role"] = user["role"]
            return redirect(url_for("index"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("admin_dashboard")) if session["role"] == "admin" else redirect(url_for("client_dashboard"))

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin": return redirect(url_for("login"))
    
    bot_folders = [d for d in os.listdir('bots') if os.path.isdir(os.path.join('bots', d))]
    status, logs = get_bot_status_and_logs()
    current_bot = os.getenv("BOT_TO_RUN", "Not set in worker environment")
    
    return render_template("admin_dashboard.html", bot_folders=bot_folders, status=status, logs=logs, current_bot=current_bot)

@app.route("/client")
def client_dashboard():
    if session.get("role") != "client": return redirect(url_for("login"))
    
    status, logs = get_bot_status_and_logs()
    current_bot = os.getenv("BOT_TO_RUN", "None")
    
    return render_template("client_dashboard.html", status=status, logs=logs, current_bot=current_bot)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
