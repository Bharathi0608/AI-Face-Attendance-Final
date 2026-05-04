import os
import webbrowser
import threading

from flask import Flask, request, jsonify, render_template, session, send_from_directory
from flask_cors import CORS

from backend.routes_extra import extra_bp
from backend.face_engine import run_attendance_scan
from config.firebase_config import get_firestore
db = get_firestore()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "change_this_in_production_xyz")

CORS(app)

# ✅ REGISTER BLUEPRINT (ALL APIs HERE)
app.register_blueprint(extra_bp)

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@1234")


# ================= UI ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


@app.route("/student")
def student():
    return render_template("student.html")


@app.route("/timetable")
def timetable():
    return render_template("timetable.html")


# ================= AUTH =================

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    d = request.json or {}

    if d.get("email") == ADMIN_EMAIL and d.get("password") == ADMIN_PASSWORD:
        session["role"] = "admin"
        return jsonify({"success": True})

    return jsonify({"success": False}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})




@app.route("/api/teacher/login", methods=["POST"])
def teacher_login():
    try:
        data = request.json

        email = data.get("email")
        password = data.get("password")

        # 🔍 search teacher in firestore
        users = db.collection("users").where("email", "==", email).stream()

        for user in users:
            user_data = user.to_dict()

            # ✅ check role + password
            if user_data.get("role") == "teacher" and user_data.get("password") == password:
                return jsonify({
            "success": True,
            "profile": user_data
        })

        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



# ================= ATTENDANCE =================

@app.route("/api/attendance/scan", methods=["POST"])
def scan():
    def run():
        run_attendance_scan()

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"success": True})


# ================= FILE =================

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)


# ================= START =================

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("\n🚀 Server running at http://127.0.0.1:5000\n")

    threading.Timer(1.5, open_browser).start()

    app.run(debug=True, use_reloader=True)