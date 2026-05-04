# # # # from backend.firebase_service import (
# # # #     add_teacher,
# # # #     get_all_teachers,
# # # #     delete_teacher,
# # # #     add_student,
# # # #     get_all_students,
# # # #     delete_student,
# # # #     create_class,
# # # #     get_all_classes,
# # # #     get_classes_for_teacher,
# # # #     enroll_student_in_class,
# # # #     delete_class,
# # # #     mark_attendance,
# # # #     get_attendance_for_class_date,
# # # #     get_attendance_summary,
# # # #     get_student_encodings_for_class,
# # # #     get_user_by_uid,
# # # #     verify_teacher_login
# # # # )

# # # # from flask import Blueprint, request, jsonify, Response
# # # # from backend.firebase_service import (
# # # #     get_all_students, get_all_classes,
# # # #     get_attendance_for_class_date,
# # # #     get_attendance_summary,
# # # #     get_classes_for_teacher,
# # # #     get_user_by_uid
# # # # )
# # # # from utils.reports import build_daily_csv, build_summary_csv
# # # # from utils.helpers import today_iso, compute_student_stats

# # # # extra_bp = Blueprint("extra", __name__)


# # # # # ─── CSV EXPORT ────────────────────────────────────────────

# # # # @extra_bp.route("/api/export/daily", methods=["GET"])
# # # # def export_daily():
# # # #     """
# # # #     GET /api/export/daily?class_id=XXX&date=2024-09-15
# # # #     Returns a CSV file download.
# # # #     """
# # # #     class_id = request.args.get("class_id")
# # # #     day = request.args.get("date", today_iso())
# # # #     if not class_id:
# # # #         return jsonify({"error": "class_id required"}), 400

# # # #     records = get_attendance_for_class_date(class_id, day)
# # # #     students = {s["uid"]: s for s in get_all_students()}
# # # #     for r in records:
# # # #         info = students.get(r.get("student_uid"), {})
# # # #         r["name"] = info.get("name", "Unknown")
# # # #         r["roll_number"] = info.get("roll_number", "—")

# # # #     cls_list = get_all_classes()
# # # #     cls_info = next((c for c in cls_list if c["class_id"] == class_id), {})
# # # #     class_name = cls_info.get("name", class_id)

# # # #     csv_data = build_daily_csv(records, class_name, day)
# # # #     return Response(
# # # #         csv_data,
# # # #         mimetype="text/csv",
# # # #         headers={"Content-Disposition": f"attachment;filename=attendance_{class_id}_{day}.csv"}
# # # #     )


# # # # @extra_bp.route("/api/export/summary", methods=["GET"])
# # # # def export_summary():
# # # #     """
# # # #     GET /api/export/summary?class_id=XXX
# # # #     Returns full summary CSV.
# # # #     """
# # # #     class_id = request.args.get("class_id")
# # # #     if not class_id:
# # # #         return jsonify({"error": "class_id required"}), 400

# # # #     summary = get_attendance_summary(class_id)
# # # #     cls_list = get_all_classes()
# # # #     cls_info = next((c for c in cls_list if c["class_id"] == class_id), {})
# # # #     class_name = cls_info.get("name", class_id)

# # # #     csv_data = build_summary_csv(summary, class_name)
# # # #     return Response(
# # # #         csv_data,
# # # #         mimetype="text/csv",
# # # #         headers={"Content-Disposition": f"attachment;filename=summary_{class_id}.csv"}
# # # #     )


# # # # # ─── STATS ─────────────────────────────────────────────────

# # # # @extra_bp.route("/api/stats/class/<class_id>", methods=["GET"])
# # # # def class_stats(class_id):
# # # #     """Full stats for a class across all dates."""
# # # #     summary = get_attendance_summary(class_id)
# # # #     total_sessions = len(summary)
# # # #     total_present  = sum(s["present"] for s in summary)
# # # #     total_records  = sum(s["total"] for s in summary)

# # # #     return jsonify({
# # # #         "class_id":       class_id,
# # # #         "total_sessions": total_sessions,
# # # #         "total_present":  total_present,
# # # #         "total_records":  total_records,
# # # #         "overall_rate":   round(total_present / total_records * 100, 1) if total_records else 0,
# # # #         "by_date":        summary
# # # #     })


# # # # @extra_bp.route("/api/stats/student/<student_uid>", methods=["GET"])
# # # # def student_stats(student_uid):
# # # #     """Attendance stats for a single student across all their classes."""
# # # #     student = get_user_by_uid(student_uid)
# # # #     if not student:
# # # #         return jsonify({"error": "Student not found"}), 404

# # # #     class_ids = student.get("class_ids", [])
# # # #     result = []

# # # #     for cid in class_ids:
# # # #         summary = get_attendance_summary(cid)
# # # #         classes = get_all_classes()
# # # #         cls_info = next((c for c in classes if c["class_id"] == cid), {})

# # # #         student_records = []
# # # #         for day_summary in summary:
# # # #             day = day_summary["date"]
# # # #             records = get_attendance_for_class_date(cid, day)
# # # #             for r in records:
# # # #                 if r.get("student_uid") == student_uid:
# # # #                     r["date"] = day
# # # #                     student_records.append(r)

# # # #         stats = compute_student_stats(student_records)
# # # #         result.append({
# # # #             "class_id":   cid,
# # # #             "class_name": cls_info.get("name", cid),
# # # #             **stats
# # # #         })

# # # #     return jsonify({"student": student, "classes": result})


# # # # # ─── SEARCH ────────────────────────────────────────────────

# # # # @extra_bp.route("/api/search", methods=["GET"])
# # # # def search():
# # # #     """
# # # #     GET /api/search?q=alice
# # # #     Searches students and teachers by name or email.
# # # #     """
# # # #     q = request.args.get("q", "").lower().strip()
# # # #     if not q:
# # # #         return jsonify({"students": [], "teachers": []})

# # # #     students = [
# # # #         s for s in get_all_students()
# # # #         if q in s.get("name", "").lower()
# # # #         or q in s.get("email", "").lower()
# # # #         or q in s.get("roll_number", "").lower()
# # # #     ]
# # # #     teachers = [
# # # #         t for t in []  # get_all_teachers imported lazily to avoid circular
# # # #         if q in t.get("name", "").lower()
# # # #         or q in t.get("email", "").lower()
# # # #     ]

# # # #     return jsonify({"students": students[:20], "teachers": teachers[:20]})


# # # # from flask import Blueprint, request, jsonify, Response
# # # # from backend.firebase_service import *
# # # # from backend.face_engine import encode_face_from_bytes

# # # # extra_bp = Blueprint("extra", __name__)

# # # # # ===== STUDENTS =====

# # # # @extra_bp.route("/api/students", methods=["GET"])
# # # # def get_students_api():
# # # #     return jsonify(get_all_students())


# # # # @extra_bp.route("/api/students", methods=["POST"])
# # # # def add_student_api():
# # # #     name = request.form.get("name")
# # # #     email = request.form.get("email")
# # # #     roll_number = request.form.get("roll_number")

# # # #     file = request.files.get("face_image")

# # # #     if not file:
# # # #         return jsonify({"error": "Image required"}), 400

# # # #     image_bytes = file.read()
# # # #     face_encoding = encode_face_from_bytes(image_bytes)

# # # #     student = add_student(
# # # #         name, email, roll_number,
# # # #         face_encoding,
# # # #         image_bytes,
# # # #         file.filename
# # # #     )

# # # #     return jsonify(student)


# # # # @extra_bp.route("/api/students/<uid>", methods=["DELETE"])
# # # # def delete_student_api(uid):
# # # #     delete_student(uid)
# # # #     return jsonify({"success": True})


# # # # # ===== TEACHERS =====

# # # # @extra_bp.route("/api/teachers", methods=["GET"])
# # # # def get_teachers_api():
# # # #     return jsonify(get_all_teachers())


# # # # @extra_bp.route("/api/teachers", methods=["POST"])
# # # # def add_teacher_api():
# # # #     data = request.json
# # # #     teacher = add_teacher(
# # # #         data["name"],
# # # #         data["email"],
# # # #         data["password"],
# # # #         data["subject"]
# # # #     )
# # # #     return jsonify(teacher)


# # # # @extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
# # # # def delete_teacher_api(uid):
# # # #     delete_teacher(uid)
# # # #     return jsonify({"success": True})


# # # from flask import Blueprint, request, jsonify, Response
# # # from backend.firebase_service import *
# # # from backend.face_engine import encode_face_from_bytes

# # # extra_bp = Blueprint("extra", __name__)

# # # # ===== STUDENTS =====

# # # @extra_bp.route("/api/students", methods=["GET"])
# # # def get_students_api():
# # #     return jsonify(get_all_students())


# # # @extra_bp.route("/api/students", methods=["POST"])
# # # def add_student_api():
# # #     try:
# # #         name = request.form.get("name")
# # #         email = request.form.get("email")
# # #         roll_number = request.form.get("roll_number")

# # #         file = request.files.get("face_image")

# # #         if not file:
# # #             return jsonify({"error": "Image required"}), 400

# # #         image_bytes = file.read()

# # #         # 🔥 Generate encoding
# # #         face_encoding = encode_face_from_bytes(image_bytes)

# # #         # 🔥 CRITICAL FIX (convert numpy → list)
# # #         if face_encoding is not None:
# # #             face_encoding = face_encoding.tolist()

# # #             student = add_student(
# # #                 name,
# # #                 email,
# # #                 roll_number,
# # #                 face_encoding,
# # #                 image_bytes,
# # #                 file.filename
# # #             )

# # #             return jsonify(student)

# # #     except Exception as e:
# # #         print("🔥 ERROR (add_student_api):", e)
# # #         return jsonify({"error": str(e)}), 500


# # # @extra_bp.route("/api/students/<uid>", methods=["DELETE"])
# # # def delete_student_api(uid):
# # #     try:
# # #         delete_student(uid)
# # #         return jsonify({"success": True})
# # #     except Exception as e:
# # #         print("🔥 ERROR (delete_student):", e)
# # #         return jsonify({"error": str(e)}), 500


# # #     # ===== TEACHERS =====

# # # @extra_bp.route("/api/teachers", methods=["GET"])
# # # def get_teachers_api():
# # #     return jsonify(get_all_teachers())


# # # @extra_bp.route("/api/teachers", methods=["POST"])
# # # def add_teacher_api():
# # #     try:
# # #         data = request.json

# # #         teacher = add_teacher(
# # #             data.get("name"),
# # #             data.get("email"),
# # #             data.get("password"),
# # #             data.get("subject")
# # #         )

# # #         return jsonify(teacher)

# # #     except Exception as e:
# # #         print("🔥 ERROR (add_teacher):", e)
# # #         return jsonify({"error": str(e)}), 500


# # # @extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
# # # def delete_teacher_api(uid):
# # #     try:
# # #         delete_teacher(uid)
# # #         return jsonify({"success": True})
# # #     except Exception as e:
# # #         print("🔥 ERROR (delete_teacher):", e)
# # #         return jsonify({"error": str(e)}), 500


# # # from flask import Blueprint, request, jsonify, Response
# # # from backend.firebase_service import *
# # # from backend.face_engine import encode_face_from_bytes

# # # extra_bp = Blueprint("extra", __name__)

# # # # ===== STUDENTS =====

# # # @extra_bp.route("/api/students", methods=["GET"])
# # # def get_students_api():
# # #     return jsonify(get_all_students())


# # # @extra_bp.route("/api/students", methods=["POST"])
# # # def add_student_api():
# # #     try:
# # #         name = request.form.get("name")
# # #         email = request.form.get("email")
# # #         roll_number = request.form.get("roll_number")
# # #         file = request.files.get("face_image")

# # #         if not file:
# # #             return jsonify({"error": "Image required"}), 400

# # #         image_bytes = file.read()

# # #         # 🔥 FIX HERE
# # #         face_encoding = encode_face_from_bytes(image_bytes)

# # #         if face_encoding:
# # #             face_encoding = [f.tolist() for f in face_encoding]
# # #         else:
# # #             face_encoding = None

# # #             student = add_student(
# # #                 name,
# # #                 email,
# # #                 roll_number,
# # #                 face_encoding,
# # #                 image_bytes,
# # #                 file.filename
# # #             )

# # #             return jsonify({"success": True, "student": student})

# # #     except Exception as e:
# # #         print("🔥 ERROR:", str(e))   # VERY IMPORTANT
# # #         return jsonify({"error": str(e)}), 500

# # #     except Exception as e:
# # #         print("ERROR:", e)
# # #         return jsonify({"error": str(e)}), 500


# # # @extra_bp.route("/api/students/<uid>", methods=["DELETE"])
# # # def delete_student_api(uid):
# # #     delete_student(uid)
# # #     return jsonify({"success": True})


# # # # ===== TEACHERS =====

# # # @extra_bp.route("/api/teachers", methods=["GET"])
# # # def get_teachers_api():
# # #     return jsonify(get_all_teachers())


# # # @extra_bp.route("/api/teachers", methods=["POST"])
# # # def add_teacher_api():
# # #     try:
# # #         data = request.json

# # #         teacher = add_teacher(
# # #             data["name"],
# # #             data["email"],
# # #             data["password"],
# # #             data["subject"]
# # #         )

# # #         return jsonify(teacher)

# # #     except Exception as e:
# # #         print("ERROR:", e)
# # #         return jsonify({"error": str(e)}), 500


# # # @extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
# # # def delete_teacher_api(uid):
# # #     delete_teacher(uid)
# # #     return jsonify({"success": True})



# # from flask import Blueprint, jsonify
# # from backend.firebase_service import db
# # extra_bp = Blueprint('extra_bp', __name__)
# # from flask import Blueprint, request, jsonify, Response
# # from backend.firebase_service import *
# # from backend.face_engine import encode_face_from_bytes

# # extra_bp = Blueprint("extra", __name__)

# # # ===== STUDENTS =====

# # @extra_bp.route("/api/students", methods=["POST"])
# # def add_student_api():
# #     try:
# #         name = request.form.get("name")
# #         email = request.form.get("email")
# #         roll_number = request.form.get("roll_number")

# #         file = request.files.get("face_image")

# #         if not file:
# #             return jsonify({"error": "Image required"}), 400

# #         image_bytes = file.read()

# #         # ❌ DISABLE encoding (TEMP)
# #         face_encoding = None

# #         student = add_student(
# #             name,
# #             email,
# #             roll_number,
# #             face_encoding,
# #             image_bytes,
# #             file.filename
# #         )

# #         return jsonify({"success": True, "student": student})

# #     except Exception as e:
# #         print("🔥 ROUTE ERROR:", e)
# #         return jsonify({"error": str(e)}), 500

# # @extra_bp.route("/api/students/<uid>", methods=["DELETE"])
# # def delete_student_api(uid):
# #     delete_student(uid)
# #     return jsonify({"success": True})


# # # ===== TEACHERS =====

# # @extra_bp.route("/api/teachers", methods=["GET"])
# # def get_teachers_api():
# #     return jsonify(get_all_teachers())


# # @extra_bp.route("/api/teachers", methods=["POST"])
# # def add_teacher_api():
# #     try:
# #         data = request.json

# #         teacher = add_teacher(
# #             data["name"],
# #             data["email"],
# #             data["password"],
# #             data["subject"]
# #         )

# #         return jsonify(teacher)

# #     except Exception as e:
# #         print("ERROR:", e)
# #         return jsonify({"error": str(e)}), 500


# # @extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
# # def delete_teacher_api(uid):
# #     delete_teacher(uid)
# #     return jsonify({"success": True})

# # # ===== CLASSES =====

# # @extra_bp.route("/api/classes", methods=["GET"])
# # def get_classes_api():
# #     return jsonify(get_all_classes())


# # @extra_bp.route("/api/classes", methods=["POST"])
# # def create_class_api():
# #     try:
# #         data = request.json

# #         name = data.get("name")
# #         teacher_uid = data.get("teacher_uid")
# #         schedule = data.get("schedule")

# #         if not name or not teacher_uid:
# #             return jsonify({"success": False, "message": "Missing fields"}), 400

# #         new_class = create_class(name, teacher_uid, schedule)

# #         return jsonify({"success": True, "class": new_class})

# #     except Exception as e:
# #         print("ERROR:", e)
# #         return jsonify({"success": False, "message": str(e)}), 500
    
    
# # @extra_bp.route('/api/classes/<class_id>', methods=['DELETE'])
# # def delete_class(class_id):
# #     try:
# #         db.collection('classes').document(class_id).delete()
# #         return jsonify({"success": True})
# #     except Exception as e:
# #         return jsonify({"success": False, "message": str(e)})



# from flask import Blueprint, request, jsonify
# from backend.firebase_service import *
# from backend.face_engine import encode_face_from_bytes

# extra_bp = Blueprint("extra", __name__)

# # ===== STUDENTS =====

# @extra_bp.route("/api/students", methods=["POST"])
# def add_student_api():
#     try:
#         name = request.form.get("name")
#         email = request.form.get("email")
#         roll_number = request.form.get("roll_number")

#         file = request.files.get("face_image")

#         if not file:
#             return jsonify({"error": "Image required"}), 400

#         image_bytes = file.read()

#         student = add_student(
#             name,
#             email,
#             roll_number,
#             face_encoding=None,
#             image_bytes=image_bytes,
#             image_filename=file.filename
#         )

#         return jsonify({"success": True, "student": student})

#     except Exception as e:
#         print("🔥 ROUTE ERROR:", e)
#         return jsonify({"error": str(e)}), 500


# @extra_bp.route("/api/students/<uid>", methods=["DELETE"])
# def delete_student_api(uid):
#     delete_student(uid)
#     return jsonify({"success": True})


# # ===== TEACHERS =====

# @extra_bp.route("/api/teachers", methods=["GET"])
# def get_teachers_api():
#     return jsonify(get_all_teachers())


# @extra_bp.route("/api/teachers", methods=["POST"])
# def add_teacher_api():
#     try:
#         data = request.json

#         teacher = add_teacher(
#             data["name"],
#             data["email"],
#             data["password"],
#             data["subject"]
#         )

#         return jsonify({"success": True, "teacher": teacher})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
# def delete_teacher_api(uid):
#     delete_teacher(uid)
#     return jsonify({"success": True})


# # ===== CLASSES =====

# @extra_bp.route("/api/classes", methods=["GET"])
# def get_classes_api():
#     return jsonify(get_all_classes())


# @extra_bp.route("/api/classes", methods=["POST"])
# def create_class_api():
#     try:
#         data = request.json

#         name = data.get("name")
#         teacher_uid = data.get("teacher_uid")
#         schedule = data.get("schedule")

#         if not name or not teacher_uid:
#             return jsonify({"success": False, "message": "Missing fields"}), 400

#         new_class = create_class(name, teacher_uid, schedule)

#         return jsonify({"success": True, "class": new_class})

#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500


#     # ✅ DELETE CLASS (FIXED — uses firebase_service function)

# @extra_bp.route("/api/classes/<class_id>", methods=["DELETE"])
# def delete_class_api(class_id):
#     try:
#         delete_class(class_id)   # ✅ USE FUNCTION (not db directly)
#         return jsonify({"success": True})
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)})


from flask import Blueprint, request, jsonify
import cv2
import numpy as np
import face_recognition
from backend.firebase_service import *

from config.firebase_config import get_firestore

db = get_firestore()
from flask import Blueprint, request, jsonify
from backend.firebase_service import (
    add_student, delete_student,
    add_teacher, delete_teacher, get_all_teachers,
    create_class, get_all_classes, delete_class,
    get_all_students
)

extra_bp = Blueprint("extra", __name__)

# ================= STUDENTS =================

@extra_bp.route("/api/students", methods=["GET"])
def get_students():
    return jsonify(get_all_students())


@extra_bp.route("/api/students", methods=["POST"])
def add_student_api():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        roll_number = request.form.get("roll_number")

        file = request.files.get("face_image")

        if not file:
            return jsonify({"success": False, "message": "Image required"}), 400

        image_bytes = file.read()
        filename = file.filename
        # Calculate face encoding
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"success": False, "message": "Failed to decode image. Please try a different photo."}), 400

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        encodings = face_recognition.face_encodings(rgb_img)
        if not encodings:
            return jsonify({"success": False, "message": "No face found in the image. Please use a clearer photo."}), 400
            
        face_encoding = encodings[0].tolist()

        student = add_student(
            name=name,
            email=email,
            roll_number=roll_number,
            face_encoding=face_encoding,
            image_bytes=image_bytes,
            filename=filename
        )

        return jsonify({"success": True, "student": student})

    except Exception as e:
        print("🔥 STUDENT ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500


@extra_bp.route("/api/students/<uid>", methods=["DELETE"])
def delete_student_api(uid):
    delete_student(uid)
    return jsonify({"success": True})


# ================= TEACHERS =================

@extra_bp.route("/api/teachers", methods=["GET"])
def get_teachers_api():
    return jsonify(get_all_teachers())


@extra_bp.route("/api/teachers", methods=["POST"])
def add_teacher_api():
    try:
        data = request.json

        teacher = add_teacher(
            data["name"],
            data["email"],
            data["password"],
            data["subject"]
        )

        return jsonify({"success": True, "teacher": teacher})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@extra_bp.route("/api/teachers/<uid>", methods=["DELETE"])
def delete_teacher_api(uid):
    delete_teacher(uid)
    return jsonify({"success": True})


# ================= CLASSES =================

# @extra_bp.route("/api/classes", methods=["GET"])
# def get_classes_api():
#     return jsonify(get_all_classes())

from backend.firebase_service import get_all_classes

@extra_bp.route('/api/classes', methods=['GET'])
def get_classes():
    try:
        classes = get_all_classes()
        print("🔥 ALL CLASSES:", classes)   # debug
        return jsonify(classes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@extra_bp.route("/api/classes", methods=["POST"])
def create_class_api():
    try:
        data = request.json
        name = data.get("name")
        teacher_uid = data.get("teacher_uid")
        schedule = data.get("schedule")

        if not name or not teacher_uid:
            return jsonify({"success": False, "message": "Missing fields"}), 400

        new_class = create_class(name, teacher_uid, schedule)
        return jsonify({"success": True, "class": new_class})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ✅ ADD THIS NEW FUNCTION BELOW
# ═════════════════════════════════════════════════════════════════════════════
#  TIMETABLE CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════
TIMETABLE = {
    "Kannada": [
        {"day": "Monday",    "time": "09:15 - 10:15"},
        {"day": "Tuesday",   "time": "11:30 - 12:30"},
        {"day": "Thursday",  "time": "09:15 - 10:15"},
        {"day": "Friday",    "time": "11:30 - 12:30"}
    ],
    "Maths": [
        {"day": "Tuesday",   "time": "09:15 - 10:15"},
        {"day": "Wednesday", "time": "11:30 - 12:30"},
        {"day": "Friday",    "time": "09:15 - 10:15"},
        {"day": "Saturday",  "time": "11:30 - 12:30"}
    ],
    "Hindi": [
        {"day": "Wednesday", "time": "09:15 - 10:15"},
        {"day": "Monday",    "time": "11:30 - 12:30"},
        {"day": "Saturday",  "time": "09:15 - 10:15"},
        {"day": "Thursday",  "time": "11:30 - 12:30"}
    ],
    "English": [
        {"day": "Monday",    "time": "10:15 - 11:15"},
        {"day": "Tuesday",   "time": "12:30 - 01:30"},
        {"day": "Thursday",  "time": "10:15 - 11:15"},
        {"day": "Friday",    "time": "12:30 - 01:30"}
    ],
    "Social Science": [
        {"day": "Tuesday",   "time": "10:15 - 11:15"},
        {"day": "Wednesday", "time": "12:30 - 01:30"},
        {"day": "Friday",    "time": "10:15 - 11:15"},
        {"day": "Saturday",  "time": "12:30 - 01:30"}
    ],
    "Science": [
        {"day": "Wednesday", "time": "10:15 - 11:15"},
        {"day": "Monday",    "time": "12:30 - 01:30"},
        {"day": "Saturday",  "time": "10:15 - 11:15"},
        {"day": "Thursday",  "time": "12:30 - 01:30"}
    ]
}

@extra_bp.route("/api/teachers/<teacher_uid>/classes", methods=["GET"])
def get_classes_for_teacher(teacher_uid):
    """
    Returns classes assigned to a teacher.
    If the teacher has a subject, it returns the 4 slots from the timetable.
    """
    try:
        # 1. Get teacher profile
        teacher_doc = db.collection("users").document(teacher_uid).get()
        if not teacher_doc.exists:
            return jsonify([])
        
        teacher_data = teacher_doc.to_dict()
        subject = teacher_data.get("subject")
        
        # 2. Find any existing classes created by admin for this teacher
        existing_classes = []
        classes_ref = db.collection("classes").where("teacher_uid", "==", teacher_uid).stream()
        for doc in classes_ref:
            d = doc.to_dict()
            d["id"] = doc.id
            existing_classes.append(d)
            
        # 3. If teacher has a subject, map the timetable slots
        # We merge existing class data with timetable schedules
        teacher_classes = []
        
        if subject in TIMETABLE:
            slots = TIMETABLE[subject]
            
            # If admin hasn't created a class object yet, we show virtual ones
            # or use the first class found for this subject
            base_class = existing_classes[0] if existing_classes else {
                "class_id": "TBD",
                "name": subject,
                "teacher_uid": teacher_uid,
                "student_ids": []
            }
            
            for slot in slots:
                session_class = base_class.copy()
                session_class["schedule"] = f"{slot['day']} {slot['time']}"
                # Generate a unique virtual ID if needed, but keeping class_id for records
                teacher_classes.append(session_class)
        else:
            # Fallback to whatever is in the DB
            teacher_classes = existing_classes

        return jsonify(teacher_classes)

    except Exception as e:
        print("🔥 GET TEACHER CLASSES ERROR:", e)
        return jsonify({"error": str(e)}), 500


@extra_bp.route("/api/teachers/<teacher_uid>/attendance", methods=["GET"])
def get_teacher_attendance(teacher_uid):
    try:
        class_id = request.args.get("class_id")
        day      = request.args.get("date")
        
        if not class_id or class_id == "TBD":
            return jsonify([])
            
        from backend.firebase_service import get_attendance_for_class_date, mark_attendance
        records = get_attendance_for_class_date(class_id, day)
        
        # 🔥 PROACTIVE FIREBASE SYNC & MIGRATION:
        from datetime import date, datetime
        today = date.today().isoformat()
        target_day = day or today

        from config.firebase_config import get_firestore
        db_conn = get_firestore()

        for r in records:
            # We call mark_attendance to ensure the new format (USN_Name) 
            # and 'subject' field exist. We only do this if needed or for not_marked.
            if r.get("status") == "not_marked" or "subject" not in r:
                mark_attendance(class_id, r["student_uid"], r["status"], target_day)
        
        # 🔥 SESSION SUMMARY SYNC:
        present_count = len([r for r in records if r.get("status") == "present"])
        absent_count  = len([r for r in records if r.get("status") == "absent"])
        total_count   = len(records)
        
        from config.firebase_config import get_firestore
        db_conn = get_firestore()
        db_conn.collection("attendance").document(class_id).collection(target_day).document("--summary--").set({
            "present":      present_count,
            "absent":       absent_count,
            "total":        total_count,
            "attendance_rate": f"{round(present_count/total_count*100) if total_count > 0 else 0}%",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        })

        return jsonify(records)

    except Exception as e:
        print("🔥 TEACHER ATTENDANCE ERROR:", e)
        return jsonify({"error": str(e)}), 500




@extra_bp.route('/api/classes/<class_id>', methods=['DELETE'])
def delete_class_api(class_id):
    try:
        from backend.firebase_service import delete_class

        delete_class(class_id)   # ✅ ONLY THIS

        return jsonify({"success": True})

    except Exception as e:
        print("❌ DELETE ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500

    
# @extra_bp.route("/api/classes/<class_id>/enroll", methods=["POST"])
# def enroll_student(class_id):
#     try:
#         data = request.json
#         student_id = data.get("student_id")

#         if not student_id:
#             return jsonify({"error": "student_id required"}), 400

#         # Get class
#         class_ref = db.collection("classes").document(class_id)
#         class_doc = class_ref.get()

#         if not class_doc.exists:
#             return jsonify({"error": "Class not found"}), 404

#         class_data = class_doc.to_dict()

#         # Update class -> add student
#         student_ids = class_data.get("student_ids", [])
#         if student_id not in student_ids:
#             student_ids.append(student_id)

#             class_ref.update({
#                 "student_ids": student_ids
#             })

#             # Update student -> add class
#             student_ref = db.collection("users").document(student_id)
#             student_doc = student_ref.get()

#             if student_doc.exists:
#                 student_data = student_doc.to_dict()
#                 class_ids = student_data.get("class_ids", [])

#                 if class_id not in class_ids:
#                     class_ids.append(class_id)

#                     student_ref.update({
#                         "class_ids": class_ids
#                     })

#                     return jsonify({"success": True})

#     except Exception as e:
#         print("🔥 ENROLL ERROR:", e)   # 👈 ADD THIS LINE
#         return jsonify({"error": str(e)}), 500

# from flask import request, jsonify
# from backend.firebase_service import get_firestore

@extra_bp.route('/api/classes/<class_id>/enroll', methods=['POST'])
def enroll_student(class_id):
    try:
        data = request.json
        student_uid = data.get("student_uid")

        if not student_uid:
            return jsonify({"success": False, "message": "Student ID missing"}), 400

        success, message = enroll_student_in_class(student_uid, class_id)
        
        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    except Exception as e:
        print("🔥 ENROLL ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500




from flask import request, jsonify
from backend.firebase_service import create_class

# @extra_bp.route('/api/classes', methods=['POST'])
# def add_class():
#     try:
#         data = request.get_json()

#         print("📥 Incoming:", data)

#         result = create_class(
#             data.get('name'),
#             data.get('teacher_uid'),
#             data.get('schedule')
#         )

#         print("✅ Saved:", result)

#         return jsonify({
#             "success": True,
#             "class": result
#         })

#     except Exception as e:
#         print("❌ ERROR:", e)
#         return jsonify({"success": False, "message": str(e)}), 500
    


@extra_bp.route('/api/attendance/scan', methods=['POST'])
def start_attendance_scan():
    try:
        data = request.get_json()
        class_id = data.get("class_id")

        from scripts.run_attendance_scan import start_attendance

        print("🔥 API CALLED - starting scan")

        # ✅ WAIT for webcam scan to finish
        result = start_attendance(class_id)

        return jsonify(result)

    except Exception as e:
        print("SCAN ERROR:", e)
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  BROWSER WEBCAM SCAN  — receives a single JPEG frame (base64) from the
#  browser, runs face_recognition, marks the matching student as present.
# ─────────────────────────────────────────────────────────────────────────────
@extra_bp.route('/api/attendance/scan-frame', methods=['POST'])
def scan_frame():
    """
    POST /api/attendance/scan-frame
    Body JSON: { "class_id": "...", "frame": "data:image/jpeg;base64,..." }

    Returns:
      { "matched": true, "student_uid": "...", "name": "...", "roll_number": "..." }
      { "matched": false }
      { "error": "..." }
    """
    try:
        import base64, io
        import numpy as np
        import face_recognition

        data        = request.get_json(force=True)
        class_id    = data.get("class_id")
        student_uid = data.get("student_uid") # Optional specific student
        frame_b64   = data.get("frame", "")

        if not class_id or not frame_b64:
            return jsonify({"error": "class_id and frame are required"}), 400

        # ── strip data-URL prefix if present ──────────────────────────────
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",", 1)[1]

        img_bytes = base64.b64decode(frame_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)

        # Decode JPEG → RGB array
        import cv2
        bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if bgr is None:
            return jsonify({"error": "Could not decode image"}), 400
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # ── Detect faces in the frame ──────────────────────────────────────
        locations = face_recognition.face_locations(rgb)
        if not locations:
            return jsonify({"matched": False, "reason": "no_face"})

        frame_encodings = face_recognition.face_encodings(rgb, locations)
        if not frame_encodings:
            return jsonify({"matched": False, "reason": "no_face"})

        frame_enc = frame_encodings[0]

        # ── Load enrolled students' encodings from Firestore ───────────────
        db_conn = get_firestore()
        
        if student_uid:
            # Verify ONLY the selected student
            student_ids = [student_uid]
        else:
            # Fallback: check all students in class (original logic)
            cls_doc = db_conn.collection("classes").document(class_id).get()
            if not cls_doc.exists:
                return jsonify({"error": "Class not found"}), 404
            student_ids = cls_doc.to_dict().get("student_ids", [])

        if not student_ids:
            return jsonify({"matched": False, "reason": "no_students"})

        # ── Advanced Strict Verification ──────────────────────────────────
        TOLERANCE = 0.52  # Balanced threshold for reliability & security
        
        # 1. Check ALL students in class to find the absolute best match
        cls_doc = db_conn.collection("classes").document(class_id).get()
        class_student_ids = cls_doc.to_dict().get("student_ids", []) if cls_doc.exists else []
        
        if student_uid and student_uid not in class_student_ids:
            class_student_ids.append(student_uid)

        abs_best_uid = None
        abs_best_dist = 1.0
        abs_best_data = {}
        
        for sid in class_student_ids:
            u_doc = db_conn.collection("users").document(sid).get()
            if not u_doc.exists: continue
            u_data = u_doc.to_dict()
            u_enc = u_data.get("face_encoding")
            if not u_enc: continue
            
            d = face_recognition.face_distance([np.array(u_enc)], frame_enc)[0]
            if d < abs_best_dist:
                abs_best_dist = d
                abs_best_uid = sid
                abs_best_data = u_data

        # ── Verification Logic ────────────────────────────────────────────
        is_legit = False
        if abs_best_uid and abs_best_dist <= TOLERANCE:
            if student_uid:
                # If a specific student was selected, they MUST be the best match
                if abs_best_uid == student_uid:
                    is_legit = True
                else:
                    print(f"❌ REJECTED: Face matches {abs_best_data.get('name')} (Dist: {abs_best_dist:.4f}) better than target student.")
            else:
                is_legit = True

        if is_legit:
            print(f"✅ VERIFIED MATCH: {abs_best_data.get('name')} (Dist: {abs_best_dist:.4f})")
            
            # ── Mark present in Firestore using standard service function ──
            from backend.firebase_service import mark_attendance
            from datetime import date
            target_date = data.get("date") or date.today().isoformat()
            
            mark_attendance(class_id, abs_best_uid, "present", target_date)

            return jsonify({
                "matched":     True,
                "student_uid": abs_best_uid,
                "name":        abs_best_data.get("name") or "Unknown",
                "email":       abs_best_data.get("email") or "—",
                "roll_number": abs_best_data.get("roll_number") or "—",
                "distance":    round(float(abs_best_dist), 4)
            })
        else:
            if abs_best_uid:
                print(f"⌛ No Match: Best match was {abs_best_data.get('name')} but Dist ({abs_best_dist:.4f}) > TOLERANCE ({TOLERANCE})")
            return jsonify({"matched": False, "reason": "no_match", "dist": round(abs_best_dist, 4)})

    except Exception as e:
        print("🔥 SCAN-FRAME ERROR:", e)
        return jsonify({"error": str(e)}), 500


@extra_bp.route("/api/attendance", methods=["GET"])
def get_attendance_api():
    try:
        class_id = request.args.get("class_id")
        day      = request.args.get("date")
        
        if not class_id:
            return jsonify({"error": "class_id required"}), 400
            
        from backend.firebase_service import get_attendance_for_class_date
        records = get_attendance_for_class_date(class_id, day)
        return jsonify(records)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= EXTRA UTILS =================

@extra_bp.route("/api/classes/<class_id>/students", methods=["GET"])
def get_class_students(class_id):
    try:
        from backend.firebase_service import get_all_students
        
        cls_doc = db.collection("classes").document(class_id).get()
        if not cls_doc.exists:
            return jsonify({"error": "Class not found"}), 404
            
        student_ids = cls_doc.to_dict().get("student_ids", [])
        all_students = get_all_students()
        
        class_students = [s for s in all_students if s["uid"] in student_ids]
        
        # 🔥 AUTO-INITIALIZE for Firebase Console:
        # If any of these students don't have a record for today, create a 'not_marked' entry.
        from backend.firebase_service import mark_attendance
        from datetime import date
        today = date.today().isoformat()
        
        # We check records for this class/today
        db_conn = get_firestore()
        existing_docs = db_conn.collection("attendance").document(class_id).collection(today).stream()
        existing_uids = [doc.id for doc in existing_docs]
        
        for s in class_students:
            if s["uid"] not in existing_uids:
                mark_attendance(class_id, s["uid"], "not_marked", today)
        
        return jsonify(class_students)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@extra_bp.route("/api/attendance/mark-absent", methods=["POST"])
def mark_absent_api():
    try:
        data = request.json
        class_id = data.get("class_id")
        student_uid = data.get("student_uid")
        
        if not class_id or not student_uid:
            return jsonify({"error": "class_id and student_uid required"}), 400
            
        from backend.firebase_service import mark_attendance
        mark_attendance(class_id, student_uid, "absent")
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500