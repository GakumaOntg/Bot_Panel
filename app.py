import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests

app = Flask(__name__)
app.secret_key = 'a-different-secret-key'

# --- CONFIGURATION & USER MANAGEMENT ---
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
# You need the Service ID of your BACKGROUND WORKER, not the web service.
# Find this in the URL of your worker's page on Render.
BOT_WORKER_SERVICE_ID = os.getenv("BOT_WORKER_SERVICE_ID")

USERS = {
    "admin": {"password": "admin_password", "role": "admin"},
    "client_a": {"password": "123", "role": "client"},
    "client_b": {"password": "456", "role": "client"}
}

def get_bot_status_and_logs():
    """Gets the status and logs for the single bot worker."""
    if not BOT_WORKER_SERVICE_ID or not RENDER_API_KEY:
        return "Not Configured", "Admin needs to set environment variables."

    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    
    # Get Service Status
    status_url = f"https://api.render.com/v1/services/{BOT_WORKER_SERVICE_ID}"
    status_res = requests.get(status_url, headers=headers)
    status = "Unknown"
    if status_res.status_code == 200:
        # e.g., 'live', 'suspended', 'deploy_in_progress'
        status = status_res.json().get('serviceDetails', {}).get('state', 'Unknown')

    # Get Logs
    logs_url = f"https://api.render.com/v1/services/{BOT_WORKER_SERVICE_ID}/logs?limit=100"
    logs_res = requests.get(logs_url, headers=headers)
    logs = "Could not fetch logs."
    if logs_res.status_code == 200:
        logs = "\n".join([item['log']['message'] for item in reversed(logs_res.json())])

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
    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("client_dashboard"))

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    bot_folders = [d for d in os.listdir('bots') if os.path.isdir(os.path.join('bots', d))]
    status, logs = get_bot_status_and_logs()
    
    return render_template("admin_dashboard.html", bot_folders=bot_folders, status=status, logs=logs)

@app.route("/client")
def client_dashboard():
    if session.get("role") != "client":
        return redirect(url_for("login"))
    
    status, logs = get_bot_status_and_logs()
    # In this model, the client can only see what the admin is currently running.
    current_bot = os.getenv("BOT_TO_RUN", "None Selected")
    
    return render_template("client_dashboard.html", status=status, logs=logs, current_bot=current_bot)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))