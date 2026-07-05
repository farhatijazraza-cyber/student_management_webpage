from flask import Flask, render_template
from database import init_db
from modules.admission import admission_bp
from modules.exams import exams_bp
from modules.fees import fees_bp
from modules.attendance import attendance_bp
from flask import render_template
from flask import redirect, url_for
app = Flask(__name__)
from datetime import datetime

@app.template_filter('date timeformat')
def datetimeformat(value):
    try:
        # Date string ko actual date object mein convert karna
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        # Din ka naam nikalna (e.g., Monday)
        return date_obj.strftime('%A')
    except:
        return value
app.secret_key = "supersecretkey"
import os
app.config['UPLOAD_FOLDER'] = 'static/uploads/students'

# Initialize Database
init_db()

# Register Blueprints
app.register_blueprint(admission_bp)
app.register_blueprint(exams_bp)
app.register_blueprint(fees_bp)
app.register_blueprint(attendance_bp)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)