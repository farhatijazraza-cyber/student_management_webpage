from flask import Flask, render_template, redirect, url_for, request, flash
from database import init_db
from modules.admission import admission_bp
from modules.exams import exams_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
from flask_login import login_required

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = "supersecretkey"

app.config['UPLOAD_FOLDER'] = 'static/uploads/students'

# ---------------- DATABASE ----------------
init_db()

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- DEMO USER ----------------
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Demo credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ---------------- TEMPLATE FILTER ----------------
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        return date_obj.strftime('%A')
    except:
        return value

# ---------------- LOGIN ROUTE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            user = User(1)
            login_user(user)

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid username or password")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ---------------- REGISTER BLUEPRINTS ----------------
app.register_blueprint(admission_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)