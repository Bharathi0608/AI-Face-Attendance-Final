# # # # """
# # # # firebase_service.py
# # # # All Firestore / Storage / Auth operations in one place.
# # # # """

# # # # import os
# # # # import os
# # # # import uuid
# # # # import json
# # # # import numpy as np
# # # # from datetime import datetime, date
# # # # from firebase_admin import auth as fb_auth
# # # # from config.firebase_config import get_firestore, get_storage, get_auth

# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  AUTH
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def create_user(email: str, password: str, display_name: str) -> str:
# # # #     """Create a Firebase Auth user. Returns UID."""
# # # #     auth = get_auth()
# # # #     user = auth.create_user(
# # # #         email=email,
# # # #         password=password,
# # # #         display_name=display_name
# # # #     )
# # # #     return user.uid


# # # # def delete_user(uid: str):
# # # #     auth = get_auth()
# # # #     auth.delete_user(uid)


# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  TEACHERS
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def add_teacher(name: str, email: str, password: str, subject: str) -> dict:
# # # #     """Create Auth user + Firestore doc for a teacher."""
# # # #     db = get_firestore()
# # # #     uid = create_user(email, password, name)
# # # #     data = {
# # # #         "uid": uid,
# # # #         "name": name,
# # # #         "email": email,
# # # #         "subject": subject,
# # # #         "role": "teacher",
# # # #         "class_ids": [],
# # # #         "created_at": datetime.utcnow().isoformat()
# # # #     }
# # # #     db.collection("users").document(uid).set(data)
# # # #     return data


# # # # def get_all_teachers() -> list:
# # # #     db = get_firestore()
# # # #     return [
# # # #         doc.to_dict()
# # # #         for doc in db.collection("users").where("role", "==", "teacher").stream()
# # # #     ]


# # # # def delete_teacher(uid: str):
# # # #     db = get_firestore()
# # # #     # Remove teacher from all assigned classes
# # # #     classes = db.collection("classes").where("teacher_uid", "==", uid).stream()
# # # #     for cls in classes:
# # # #         db.collection("classes").document(cls.id).update({"teacher_uid": None})
# # # #     db.collection("users").document(uid).delete()
# # # #     try:
# # # #         delete_user(uid)
# # # #     except Exception:
# # # #         pass


# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  STUDENTS
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def add_student(name: str, email: str, roll_number: str,
# # # #                 face_encoding: list, image_bytes: bytes,
# # # #                 image_filename: str) -> dict:
# # # #     """Create Firestore doc for a student, upload face image + encoding."""
# # # #     db = get_firestore()
# # # #     bucket = get_storage()
# # # #     uid = str(uuid.uuid4())

# # # # import os
# # # # UPLOAD_FOLDER = "uploads"
# # # # os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # # # file_name = f"{uid}_{image_filename}"
# # # # file_path = os.path.join(UPLOAD_FOLDER, file_name)

# # # # with open(file_path, "wb") as f:
# # # #     f.write(image_bytes)

# # # #     # 👇 IMPORTANT (this is what frontend will use)
# # # #     image_url = f"/uploads/{file_name}"

# # # #     data = {
# # # #         "uid": uid,
# # # #         "name": name,
# # # #         "email": email,
# # # #         "roll_number": roll_number,
# # # #         "role": "student",
# # # #         "face_encoding": face_encoding,   # list of 128 floats
# # # #         "image_url": image_url,
# # # #         "class_ids": [],
# # # #         "created_at": datetime.utcnow().isoformat()
# # # #     }
# # # #     db.collection("users").document(uid).set(data)
# # # #     return data


# # # # def get_all_students() -> list:
# # # #     db = get_firestore()
# # # #     return [
# # # #         doc.to_dict()
# # # #         for doc in db.collection("users").where("role", "==", "student").stream()
# # # #     ]


# # # # def delete_student(uid: str):
# # # #     db = get_firestore()
# # # #     bucket = get_storage()
# # # #     # Delete face image
# # # #     blobs = bucket.list_blobs(prefix=f"faces/{uid}/")
# # # #     for blob in blobs:
# # # #         blob.delete()
# # # #     db.collection("users").document(uid).delete()


# # # # def get_student_encodings_for_class(class_id: str) -> dict:
# # # #     """Returns {student_uid: np.array(encoding)} for all enrolled students."""
# # # #     db = get_firestore()
# # # #     cls_doc = db.collection("classes").document(class_id).get()
# # # #     if not cls_doc.exists:
# # # #         return {}
# # # #     student_ids = cls_doc.to_dict().get("student_ids", [])
# # # #     encodings = {}
# # # #     for sid in student_ids:
# # # #         doc = db.collection("users").document(sid).get()
# # # #         if doc.exists:
# # # #             d = doc.to_dict()
# # # #             enc = d.get("face_encoding")
# # # #             if enc:
# # # #                 encodings[sid] = np.array(enc)
# # # #     return encodings


# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  CLASSES
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def create_class(name: str, teacher_uid: str, schedule: str) -> dict:
# # # #     db = get_firestore()
# # # #     class_id = str(uuid.uuid4())[:8].upper()
# # # #     data = {
# # # #         "class_id": class_id,
# # # #         "name": name,
# # # #         "teacher_uid": teacher_uid,
# # # #         "schedule": schedule,
# # # #         "student_ids": [],
# # # #         "created_at": datetime.utcnow().isoformat()
# # # #     }
# # # #     db.collection("classes").document(class_id).set(data)
# # # #     # Update teacher's class list
# # # #     db.collection("users").document(teacher_uid).update({
# # # #         "class_ids": firestore_array_union(class_id)
# # # #     })
# # # #     return data


# # # # def get_all_classes() -> list:
# # # #     db = get_firestore()
# # # #     return [doc.to_dict() for doc in db.collection("classes").stream()]


# # # # def get_classes_for_teacher(teacher_uid: str) -> list:
# # # #     db = get_firestore()
# # # #     return [
# # # #         doc.to_dict()
# # # #         for doc in db.collection("classes")
# # # #             .where("teacher_uid", "==", teacher_uid).stream()
# # # #     ]


# # # # def enroll_student_in_class(student_uid: str, class_id: str):
# # # #     db = get_firestore()
# # # #     db.collection("classes").document(class_id).update({
# # # #         "student_ids": firestore_array_union(student_uid)
# # # #     })
# # # #     db.collection("users").document(student_uid).update({
# # # #         "class_ids": firestore_array_union(class_id)
# # # #     })


# # # # def delete_class(class_id: str):
# # # #     db = get_firestore()
# # # #     db.collection("classes").document(class_id).delete()


# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  ATTENDANCE
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def mark_attendance(class_id: str, student_uid: str,
# # # #                     status: str, today: str = None):
# # # #     """status = 'present' | 'absent'"""
# # # #     db = get_firestore()
# # # #     today = today or date.today().isoformat()
# # # #     db.collection("attendance") \
# # # #       .document(class_id) \
# # # #       .collection(today) \
# # # #       .document(student_uid) \
# # # #       .set({
# # # #           "status": status,
# # # #           "timestamp": datetime.utcnow().isoformat(),
# # # #           "student_uid": student_uid
# # # #       })


# # # # def get_attendance_for_class_date(class_id: str, day: str = None) -> list:
# # # #     db = get_firestore()
# # # #     day = day or date.today().isoformat()
# # # #     docs = db.collection("attendance") \
# # # #              .document(class_id) \
# # # #              .collection(day) \
# # # #              .stream()
# # # #     return [doc.to_dict() for doc in docs]


# # # # def get_attendance_summary(class_id: str) -> list:
# # # #     """Returns a list of {date, present_count, absent_count}."""
# # # #     db = get_firestore()
# # # #     coll = db.collection("attendance").document(class_id).collections()
# # # #     summary = []
# # # #     for day_coll in coll:
# # # #         records = [d.to_dict() for d in day_coll.stream()]
# # # #         present = sum(1 for r in records if r.get("status") == "present")
# # # #         absent = sum(1 for r in records if r.get("status") == "absent")
# # # #         summary.append({
# # # #             "date": day_coll.id,
# # # #             "present": present,
# # # #             "absent": absent,
# # # #             "total": len(records)
# # # #         })
# # # #     return sorted(summary, key=lambda x: x["date"], reverse=True)


# # # # # ═══════════════════════════════════════════════════════════════
# # # # #  HELPERS
# # # # # ═══════════════════════════════════════════════════════════════

# # # # def firestore_array_union(value):
# # # #     from google.cloud.firestore_v1 import ArrayUnion
# # # #     return ArrayUnion([value])


# # # # def get_user_by_uid(uid: str) -> dict:
# # # #     db = get_firestore()
# # # #     doc = db.collection("users").document(uid).get()
# # # #     return doc.to_dict() if doc.exists else None


# # # # def verify_teacher_login(email: str, password: str) -> dict:
# # # #     """
# # # #     Uses Pyrebase4 (client SDK) for email+password sign-in.
# # # #     Returns user info dict or raises exception.
# # # #     """
# # # #     import pyrebase
# # # #     from config.firebase_config import FIREBASE_CONFIG
# # # #     fb = pyrebase.initialize_app(FIREBASE_CONFIG)
# # # #     fb_auth_client = fb.auth()
# # # #     user = fb_auth_client.sign_in_with_email_and_password(email, password)
# # # #     uid = user["localId"]
# # # #     # Fetch Firestore profile
# # # #     profile = get_user_by_uid(uid)
# # # #     if not profile or profile.get("role") != "teacher":
# # # #         raise PermissionError("Account is not a teacher account.")
# # # #     return profile


# # # """
# # # firebase_service.py
# # # All Firestore / Storage / Auth operations in one place.
# # # """

# # # import os
# # # import uuid
# # # import json
# # # from google_crc32c import value
# # # import numpy as np
# # # from datetime import datetime, date
# # # from firebase_admin import auth as fb_auth
# # # from streamlit import user
# # # from config.firebase_config import get_firestore, get_storage, get_auth

# # # # Ensure uploads folder exists
# # # UPLOAD_FOLDER = "uploads"
# # # os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # # # ═══════════════════════════════════════════════════════════════
# # # #  AUTH
# # # # ═══════════════════════════════════════════════════════════════

# # # def create_user(email: str, password: str, display_name: str) -> str:
# # #     auth = get_auth()
# # #     user = auth.create_user(
# # #         email=email,
# # #         password=password,
# # #         display_name=display_name
# # #     )
# # #     return user.uid


# # # def delete_user(uid: str):
# # #     auth = get_auth()
# # #     auth.delete_user(uid)


# # #     # ═══════════════════════════════════════════════════════════════
# # #     #  TEACHERS
# # #     # ═══════════════════════════════════════════════════════════════

# # # def add_teacher(name: str, email: str, password: str, subject: str) -> dict:
# # #     db = get_firestore()
# # #     uid = create_user(email, password, name)

# # #     data = {
# # #         "uid": uid,
# # #         "name": name,
# # #         "email": email,
# # #         "subject": subject,
# # #         "role": "teacher",
# # #         "class_ids": [],
# # #         "created_at": datetime.utcnow().isoformat()
# # #     }

# # #     db.collection("users").document(uid).set(data)
# # #     return data


# # # def get_all_teachers() -> list:
# # #     db = get_firestore()
# # #     return [
# # # doc.to_dict()
# # # for doc in db.collection("users").where("role", "==", "teacher").stream()
# # # ]


# # # def delete_teacher(uid: str):
# # #     db = get_firestore()
# # #     classes = db.collection("classes").where("teacher_uid", "==", uid).stream()

# # #     for cls in classes:
# # #         db.collection("classes").document(cls.id).update({"teacher_uid": None})

# # #         db.collection("users").document(uid).delete()

# # #         try:
# # #             delete_user(uid)
# # #         except Exception:
# # #             pass


# # #         # ═══════════════════════════════════════════════════════════════
# # #         #  STUDENTS
# # #         # ═══════════════════════════════════════════════════════════════

# # # def add_student(name: str, email: str, roll_number: str,
# # # face_encoding: list, image_bytes: bytes,
# # # image_filename: str) -> dict:

# # #     db = get_firestore()
# # #     uid = str(uuid.uuid4())

# # #     # Save image locally
# # #     file_name = f"{uid}_{image_filename}"
# # #     file_path = os.path.join(UPLOAD_FOLDER, file_name)

# # #     with open(file_path, "wb") as f:
# # #         f.write(image_bytes)

# # #         image_url = f"/uploads/{file_name}"

# # #         data = {
# # #             "uid": uid,
# # #             "name": name,
# # #             "email": email,
# # #             "roll_number": roll_number,
# # #             "role": "student",
# # #             "face_encoding": face_encoding,
# # #             "image_url": image_url,
# # #             "class_ids": [],
# # #             "created_at": datetime.utcnow().isoformat()
# # #         }

# # #         db.collection("users").document(uid).set(data)
# # #         return data


# # # def get_all_students() -> list:
# # #     db = get_firestore()
# # #     return [
# # # doc.to_dict()
# # # for doc in db.collection("users").where("role", "==", "student").stream()
# # # ]


# # # def delete_student(uid: str):
# # #     db = get_firestore()
# # #     db.collection("users").document(uid).delete()


# # #     # ═══════════════════════════════════════════════════════════════
# # #     #  CLASSES
# # #     # ═══════════════════════════════════════════════════════════════

# # # def create_class(name: str, teacher_uid: str, schedule: str) -> dict:
# # #     db = get_firestore()
# # #     class_id = str(uuid.uuid4())[:8].upper()

# # #     data = {
# # #         "class_id": class_id,
# # #         "name": name,
# # #         "teacher_uid": teacher_uid,
# # #         "schedule": schedule,
# # #         "student_ids": [],
# # #         "created_at": datetime.utcnow().isoformat()
# # #     }

# # #     db.collection("classes").document(class_id).set(data)

# # #     db.collection("users").document(teacher_uid).update({
# # #         "class_ids": firestore_array_union(class_id)
# # #     })

# # #     return data


# # # def get_all_classes() -> list:
# # #     db = get_firestore()
# # #     return [doc.to_dict() for doc in db.collection("classes").stream()]


# # # def enroll_student_in_class(student_uid: str, class_id: str):
# # #     db = get_firestore()

# # #     db.collection("classes").document(class_id).update({
# # #         "student_ids": firestore_array_union(student_uid)
# # #     })

# # #     db.collection("users").document(student_uid).update({
# # #         "class_ids": firestore_array_union(class_id)
# # #     })


# # # def delete_class(class_id: str):
# # #     db = get_firestore()
# # #     db.collection("classes").document(class_id).delete()


# # #     # ═══════════════════════════════════════════════════════════════
# # #     #  ATTENDANCE
# # #     # ═══════════════════════════════════════════════════════════════
    
# # #     def get_attendance_summary(class_id: str) -> list:
# # #         db = get_firestore()

# # #     collections = db.collection("attendance").document(class_id).collections()
# # #     summary = []

# # #     for day_coll in collections:
# # #         records = [doc.to_dict() for doc in day_coll.stream()]

# # #         present = sum(1 for r in records if r.get("status") == "present")
# # #         absent = sum(1 for r in records if r.get("status") == "absent")

# # #         summary.append({
# # #             "date": day_coll.id,
# # #             "present": present,
# # #             "absent": absent,
# # #             "total": len(records)
# # #         })

# # #         return sorted(summary, key=lambda x: x["date"], reverse=True)

# # # def get_attendance_for_class_date(class_id: str, day: str = None) -> list:
# # #     db = get_firestore()
# # #     day = day or date.today().isoformat()

# # #     docs = db.collection("attendance") \
# # #     .document(class_id) \
# # #     .collection(day) \
# # #     .stream()

# # #     return [doc.to_dict() for doc in docs]

# # # def mark_attendance(class_id: str, student_uid: str,
# # # status: str, today: str = None):

# # #     db = get_firestore()
# # #     today = today or date.today().isoformat()

# # #     db.collection("attendance") \
# # #     .document(class_id) \
# # #     .collection(today) \
# # #     .document(student_uid) \
# # #     .set({
# # #         "status": status,
# # #         "timestamp": datetime.utcnow().isoformat(),
# # #         "student_uid": student_uid
# # #     })


# # #     # ═══════════════════════════════════════════════════════════════
# # #     #  HELPERS
# # #     # ═══════════════════════════════════════════════════════════════

# # # def firestore_array_union(value):
# # #     from google.cloud.firestore_v1 import ArrayUnion
# # #     return ArrayUnion([value])


# # # def get_user_by_uid(uid: str) -> dict:
# # #     db = get_firestore()
# # #     doc = db.collection("users").document(uid).get()
# # #     return doc.to_dict() if doc.exists else None

# # # def verify_teacher_login(email: str, password: str) -> dict:
# # #     import pyrebase
# # #     from config.firebase_config import FIREBASE_CONFIG

# # #     fb = pyrebase.initialize_app(FIREBASE_CONFIG)
# # #     fb_auth_client = fb.auth()

# # #     user = fb_auth_client.sign_in_with_email_and_password(email, password)
# # #     uid = user["localId"]

# # #     profile = get_user_by_uid(uid)

# # #     if not profile or profile.get("role") != "teacher":
# # #         raise PermissionError("Account is not a teacher account.")

# # #     return profile   # ✅ correct position


# # """
# # firebase_service.py
# # All Firestore / Storage / Auth operations in one place.
# # """

# # import os
# # import uuid
# # from google_crc32c import value
# # import numpy as np
# # from datetime import datetime, date
# # from firebase_admin import auth as fb_auth
# # from config.firebase_config import get_firestore, get_storage, get_auth

# # # Ensure uploads folder exists
# # UPLOAD_FOLDER = "uploads"
# # os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # # ================= AUTH =================

# # def create_user(email: str, password: str, display_name: str) -> str:
# #     auth = get_auth()
# #     user = auth.create_user(
# #         email=email,
# #         password=password,
# #         display_name=display_name
# #     )
# #     return user.uid


# # def delete_user(uid: str):
# #     auth = get_auth()
# #     auth.delete_user(uid)


# #     # ================= TEACHERS =================

# # def add_teacher(name: str, email: str, password: str, subject: str) -> dict:
# #     db = get_firestore()
# #     uid = create_user(email, password, name)

# #     data = {
# #         "uid": uid,
# #         "name": name,
# #         "email": email,
# #         "subject": subject,
# #         "role": "teacher",
# #         "class_ids": [],
# #         "created_at": datetime.utcnow().isoformat()
# #     }

# #     db.collection("users").document(uid).set(data)
# #     return data


# # def get_all_teachers() -> list:
# #     db = get_firestore()
# #     return [
# # doc.to_dict()
# # for doc in db.collection("users").where("role", "==", "teacher").stream()
# # ]


# # def delete_teacher(uid: str):
# #     db = get_firestore()

# #     classes = db.collection("classes").where("teacher_uid", "==", uid).stream()
# #     for cls in classes:
# #         db.collection("classes").document(cls.id).update({"teacher_uid": None})

# #         db.collection("users").document(uid).delete()

# #         try:
# #             delete_user(uid)
# #         except Exception:
# #             pass


# #         # ================= STUDENTS =================

# # def add_student(name: str, email: str, roll_number: str,
# # face_encoding: list, image_bytes: bytes,
# # image_filename: str) -> dict:

# #     db = get_firestore()
# #     uid = str(uuid.uuid4())

# #     file_name = f"{uid}_{image_filename}"
# #     file_path = os.path.join(UPLOAD_FOLDER, file_name)

# #     with open(file_path, "wb") as f:
# #         f.write(image_bytes)

# #         image_url = f"/uploads/{file_name}"

# #         data = {
# #             "uid": uid,
# #             "name": name,
# #             "email": email,
# #             "roll_number": roll_number,
# #             "role": "student",
# #             "face_encoding": face_encoding,
# #             "image_url": image_url,
# #             "class_ids": [],
# #             "created_at": datetime.utcnow().isoformat()
# #         }

# #         db.collection("users").document(uid).set(data)
# #         return data


# # def get_all_students() -> list:
# #     db = get_firestore()
# #     return [
# # doc.to_dict()
# # for doc in db.collection("users").where("role", "==", "student").stream()
# # ]


# # def delete_student(uid: str):
# #     db = get_firestore()
# #     db.collection("users").document(uid).delete()


# #     # ================= CLASSES =================

# # def create_class(name: str, teacher_uid: str, schedule: str) -> dict:
# #     db = get_firestore()
# #     class_id = str(uuid.uuid4())[:8].upper()

# #     data = {
# #         "class_id": class_id,
# #         "name": name,
# #         "teacher_uid": teacher_uid,
# #         "schedule": schedule,
# #         "student_ids": [],
# #         "created_at": datetime.utcnow().isoformat()
# #     }

# #     db.collection("classes").document(class_id).set(data)

# #     db.collection("users").document(teacher_uid).update({
# #         "class_ids": firestore_array_union(class_id)
# #     })

# #     return data


# # def get_all_classes() -> list:
# #     db = get_firestore()
# #     return [doc.to_dict() for doc in db.collection("classes").stream()]


# # def enroll_student_in_class(student_uid: str, class_id: str):
# #     db = get_firestore()

# #     db.collection("classes").document(class_id).update({
# #         "student_ids": firestore_array_union(student_uid)
# #     })

# #     db.collection("users").document(student_uid).update({
# #         "class_ids": firestore_array_union(class_id)
# #     })


# # def delete_class(class_id: str):
# #     db = get_firestore()
# #     db.collection("classes").document(class_id).delete()


# #     # ================= ATTENDANCE =================

# # def mark_attendance(class_id: str, student_uid: str,
# # status: str, today: str = None):

# #     db = get_firestore()
# #     today = today or date.today().isoformat()

# #     db.collection("attendance") \
# #     .document(class_id) \
# #     .collection(today) \
# #     .document(student_uid) \
# #     .set({
# #         "status": status,
# #         "timestamp": datetime.utcnow().isoformat(),
# #         "student_uid": student_uid
# #     })


# # def get_attendance_for_class_date(class_id: str, day: str = None) -> list:
# #     db = get_firestore()
# #     day = day or date.today().isoformat()

# #     docs = db.collection("attendance") \
# #     .document(class_id) \
# #     .collection(day) \
# #     .stream()

# #     return [doc.to_dict() for doc in docs]


# # def get_attendance_summary(class_id: str) -> list:
# #     db = get_firestore()

# #     collections = db.collection("attendance").document(class_id).collections()
# #     summary = []

# #     for day_coll in collections:
# #         records = [doc.to_dict() for doc in day_coll.stream()]

# #         present = sum(1 for r in records if r.get("status") == "present")
# #         absent = sum(1 for r in records if r.get("status") == "absent")

# #         summary.append({
# #             "date": day_coll.id,
# #             "present": present,
# #             "absent": absent,
# #             "total": len(records)
# #         })

# #         return sorted(summary, key=lambda x: x["date"], reverse=True)


# #     # ================= HELPERS =================

# # def firestore_array_union(value):
# #     from google.cloud.firestore_v1 import ArrayUnion
# #     return ArrayUnion([value])


# # def get_user_by_uid(uid: str) -> dict:
# #     db = get_firestore()
# #     doc = db.collection("users").document(uid).get()
# #     return doc.to_dict() if doc.exists else None


# # def verify_teacher_login(email: str, password: str) -> dict:
# #     import pyrebase
# #     from config.firebase_config import FIREBASE_CONFIG

# #     fb = pyrebase.initialize_app(FIREBASE_CONFIG)
# #     fb_auth_client = fb.auth()

# #     user = fb_auth_client.sign_in_with_email_and_password(email, password)
# #     uid = user["localId"]

# #     profile = get_user_by_uid(uid)

# #     if not profile or profile.get("role") != "teacher":
# #         raise PermissionError("Account is not a teacher account.")

# #     return profile


# """
# firebase_service.py
# All Firestore / Auth operations in one place.
# """

# import os
# import uuid
# import numpy as np
# from datetime import datetime, date
# from firebase_admin import auth as fb_auth
# from config.firebase_config import get_firestore, get_auth

# # Ensure uploads folder exists
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # ============================================================
# # AUTH
# # ============================================================

# def create_user(email: str, password: str, display_name: str) -> str:
#     auth = get_auth()
#     user = auth.create_user(
#         email=email,
#         password=password,
#         display_name=display_name
#     )
#     return user.uid


# def delete_user(uid: str):
#     auth = get_auth()
#     auth.delete_user(uid)


#     # ============================================================
#     # TEACHERS
#     # ============================================================

# def add_teacher(name: str, email: str, password: str, subject: str) -> dict:
#     db = get_firestore()
#     uid = create_user(email, password, name)

#     data = {
#         "uid": uid,
#         "name": name,
#         "email": email,
#         "subject": subject,
#         "role": "teacher",
#         "class_ids": [],
#         "created_at": datetime.utcnow().isoformat()
#     }

#     db.collection("users").document(uid).set(data)
#     return data


# def get_all_teachers() -> list:
#     db = get_firestore()
#     return [
# doc.to_dict()
# for doc in db.collection("users").where("role", "==", "teacher").stream()
# ]


# def delete_teacher(uid: str):
#     db = get_firestore()

#     # Remove teacher from classes
#     classes = db.collection("classes").where("teacher_uid", "==", uid).stream()
#     for cls in classes:
#         db.collection("classes").document(cls.id).update({"teacher_uid": None})

#         db.collection("users").document(uid).delete()

#         try:
#             delete_user(uid)
#         except Exception:
#             pass


#         # ============================================================
#         # STUDENTS
#         # ============================================================

# def add_student(name: str, email: str, roll_number: str,
# face_encoding: list, image_bytes: bytes,
# image_filename: str) -> dict:

#     db = get_firestore()
#     uid = str(uuid.uuid4())

#     # Save image locally
#     file_name = f"{uid}_{image_filename}"
#     file_path = os.path.join(UPLOAD_FOLDER, file_name)

#     with open(file_path, "wb") as f:
#         f.write(image_bytes)

#         image_url = f"/uploads/{file_name}"

#         data = {
#             "uid": uid,
#             "name": name,
#             "email": email,
#             "roll_number": roll_number,
#             "role": "student",
#             "face_encoding": face_encoding,
#             "image_url": image_url,
#             "class_ids": [],
#             "created_at": datetime.utcnow().isoformat()
#         }

#         db.collection("users").document(uid).set(data)
#         return data


# def get_all_students() -> list:
#     db = get_firestore()
#     return [
# doc.to_dict()
# for doc in db.collection("users").where("role", "==", "student").stream()
# ]


# def delete_student(uid: str):
#     db = get_firestore()
#     db.collection("users").document(uid).delete()


# def get_student_encodings_for_class(class_id: str) -> dict:
#     db = get_firestore()
#     cls_doc = db.collection("classes").document(class_id).get()

#     if not cls_doc.exists:
#         return {}

#     student_ids = cls_doc.to_dict().get("student_ids", [])
#     encodings = {}

#     for sid in student_ids:
#         doc = db.collection("users").document(sid).get()
#         if doc.exists:
#             data = doc.to_dict()
#             enc = data.get("face_encoding")
#             if enc:
#                 encodings[sid] = np.array(enc)

#                 return encodings


#             # ============================================================
#             # CLASSES
#             # ============================================================

# def create_class(name: str, teacher_uid: str, schedule: str) -> dict:
#     db = get_firestore()
#     class_id = str(uuid.uuid4())[:8].upper()

#     data = {
#         "class_id": class_id,
#         "name": name,
#         "teacher_uid": teacher_uid,
#         "schedule": schedule,
#         "student_ids": [],
#         "created_at": datetime.utcnow().isoformat()
#     }

#     db.collection("classes").document(class_id).set(data)

#     db.collection("users").document(teacher_uid).update({
#         "class_ids": firestore_array_union(class_id)
#     })

#     return data


# def get_all_classes() -> list:
#     db = get_firestore()
#     return [doc.to_dict() for doc in db.collection("classes").stream()]


# def get_classes_for_teacher(teacher_uid: str) -> list:
#     db = get_firestore()
#     return [
# doc.to_dict()
# for doc in db.collection("classes")
# .where("teacher_uid", "==", teacher_uid)
# .stream()
# ]


# def enroll_student_in_class(student_uid: str, class_id: str):
#     db = get_firestore()

#     db.collection("classes").document(class_id).update({
#         "student_ids": firestore_array_union(student_uid)
#     })

#     db.collection("users").document(student_uid).update({
#         "class_ids": firestore_array_union(class_id)
#     })


# def delete_class(class_id: str):
#     db = get_firestore()
#     db.collection("classes").document(class_id).delete()


#     # ============================================================
#     # ATTENDANCE
#     # ============================================================

# def mark_attendance(class_id: str, student_uid: str,
# status: str, today: str = None):

#     db = get_firestore()
#     today = today or date.today().isoformat()

#     db.collection("attendance") \
#     .document(class_id) \
#     .collection(today) \
#     .document(student_uid) \
#     .set({
#         "status": status,
#         "timestamp": datetime.utcnow().isoformat(),
#         "student_uid": student_uid
#     })


# def get_attendance_for_class_date(class_id: str, day: str = None) -> list:
#     db = get_firestore()
#     day = day or date.today().isoformat()

#     docs = db.collection("attendance") \
#     .document(class_id) \
#     .collection(day) \
#     .stream()

#     return [doc.to_dict() for doc in docs]


# def get_attendance_summary(class_id: str) -> list:
#     db = get_firestore()

#     collections = db.collection("attendance").document(class_id).collections()
#     summary = []

#     for day_coll in collections:
#         records = [doc.to_dict() for doc in day_coll.stream()]

#         present = sum(1 for r in records if r.get("status") == "present")
#         absent = sum(1 for r in records if r.get("status") == "absent")

#         summary.append({
#             "date": day_coll.id,
#             "present": present,
#             "absent": absent,
#             "total": len(records)
#         })

#         return sorted(summary, key=lambda x: x["date"], reverse=True)


#     # ============================================================
#     # HELPERS
#     # ============================================================

# def firestore_array_union(value):
#     from google.cloud.firestore_v1 import ArrayUnion
#     return ArrayUnion([value])


# def get_user_by_uid(uid: str) -> dict:
#     db = get_firestore()
#     doc = db.collection("users").document(uid).get()
#     return doc.to_dict() if doc.exists else None


# def verify_teacher_login(email: str, password: str) -> dict:
#     import pyrebase
#     from config.firebase_config import FIREBASE_CONFIG

#     fb = pyrebase.initialize_app(FIREBASE_CONFIG)
#     fb_auth_client = fb.auth()

#     user = fb_auth_client.sign_in_with_email_and_password(email, password)
#     uid = user["localId"]

#     profile = get_user_by_uid(uid)

#     if not profile or profile.get("role") != "teacher":
#         raise PermissionError("Account is not a teacher account.")

#     return profile



import os
import uuid
import numpy as np
from datetime import datetime, date
from firebase_admin import auth as fb_auth
from config.firebase_config import get_firestore, get_auth
from config.firebase_config import get_firestore

db = get_firestore()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= AUTH =================

def create_user(email: str, password: str, display_name: str) -> str:
    auth = get_auth()
    user = auth.create_user(
        email=email,
        password=password,
        display_name=display_name
    )
    return user.uid


def delete_user(uid: str):
    auth = get_auth()
    auth.delete_user(uid)


    # ================= TEACHERS =================

# def add_teacher(name, email, password, subject):
#     db = get_firestore()
#     uid = create_user(email, password, name)

#     data = {
#         "uid": uid,
#         "name": name,
#         "email": email,
#         "subject": subject,
#         "role": "teacher",
#         "class_ids": [],
#         "created_at": datetime.utcnow().isoformat()
#     }

#     db.collection("users").document(uid).set(data)
#     return data

# from datetime import datetime   # (add at top if not present)

# def add_teacher(name, email, password, subject):
#     doc = db.collection("users").document()

#     teacher_data = {
#         "uid": doc.id,
#         "name": name,
#         "email": email,
#         "password": password,   # ✅ THIS IS THE FIX
#         "subject": subject,
#         "role": "teacher",
#         "class_ids": [],
#         "created_at": datetime.now().isoformat()
#     }

#     doc.set(teacher_data)
#     return teacher_data

# def get_all_teachers():
#     db = get_firestore()
#     return [doc.to_dict() for doc in db.collection("users").where("role", "==", "teacher").stream()]


# def delete_teacher(uid):
#     db = get_firestore()
#     db.collection("users").document(uid).delete()
#     try:
#         delete_user(uid)
#     except:
#         pass


#     # ================= STUDENTS =================

# def add_student(name, email, roll_number, face_encoding, image_bytes, filename):
#     db = get_firestore()
#     uid = str(uuid.uuid4())

#     try:
#         file_name = f"{uid}_{filename}"
#         file_path = os.path.join(UPLOAD_FOLDER, file_name)

#         # ✅ Save image safely
#         with open(file_path, "wb") as f:
#             f.write(image_bytes)

#             image_url = f"/uploads/{file_name}"

#             # ❌ DISABLE encoding completely (TEMP FIX)
#             data = {
#                 "uid": uid,
#                 "name": name,
#                 "email": email,
#                 "roll_number": roll_number,
#                 "role": "student",
#                 "face_encoding": None,   # 🔥 IMPORTANT FIX
#                 "image_url": image_url,
#                 "class_ids": [],
#                 "created_at": datetime.utcnow().isoformat()
#             }

#             db.collection("users").document(uid).set(data)

#             return data

#     except Exception as e:
#         print("🔥 FIREBASE ERROR:", e)
#         raise e

# def get_all_students():
#     db = get_firestore()
#     return [doc.to_dict() for doc in db.collection("users").where("role", "==", "student").stream()]


# def delete_student(uid):
#     db = get_firestore()
#     db.collection("users").document(uid).delete()


#     # ================= CLASSES =================

# # def create_class(name, teacher_uid, schedule):
# #     db = get_firestore()
# #     class_id = str(uuid.uuid4())[:8]

# #     data = {
# #         "class_id": class_id,
# #         "name": name,
# #         "teacher_uid": teacher_uid,
# #         "schedule": schedule,
# #         "student_ids": [],
# #         "created_at": datetime.utcnow().isoformat()
# #     }

# def create_class(name, teacher_uid, schedule):
#     db = get_firestore()

#     doc_ref = db.collection("classes").document()

#     data = {
#         "class_id": doc_ref.id,   # 🔥 MUST HAVE
#         "name": name,
#         "teacher_uid": teacher_uid,
#         "schedule": schedule,
#         "student_ids": []
#     }

#     doc_ref.set(data)

#     print("🔥 SAVED CLASS:", data)

#     return data


# def get_all_classes():
#     db = get_firestore()

#     classes = []
#     for doc in db.collection("classes").stream():
#         data = doc.to_dict()
#         data["class_id"] = doc.id   # 🔥 ADD THIS LINE
#         classes.append(data)

#         return classes

# def get_classes_for_teacher(teacher_uid):
#     db = get_firestore()
#     return [doc.to_dict() for doc in db.collection("classes").where("teacher_uid", "==", teacher_uid).stream()]


# def enroll_student_in_class(student_uid, class_id):
#     db = get_firestore()
#     db.collection("classes").document(class_id).update({
#         "student_ids": firestore_array_union(student_uid)
#     })


# def delete_class(class_id):
#     db = get_firestore()
#     db.collection("classes").document(class_id).delete()


#     # ================= ATTENDANCE =================

# def mark_attendance(class_id, student_uid, status, today=None):
#     db = get_firestore()
#     today = today or date.today().isoformat()

#     db.collection("attendance").document(class_id).collection(today).document(student_uid).set({
#         "status": status,
#         "timestamp": datetime.utcnow().isoformat(),
#         "student_uid": student_uid
#     })


# def get_attendance_for_class_date(class_id, day=None):
#     db = get_firestore()
#     day = day or date.today().isoformat()

#     docs = db.collection("attendance").document(class_id).collection(day).stream()
#     return [doc.to_dict() for doc in docs]


# def get_attendance_summary(class_id):
#     db = get_firestore()
#     collections = db.collection("attendance").document(class_id).collections()

#     summary = []

#     for col in collections:
#         records = [d.to_dict() for d in col.stream()]
#         present = sum(1 for r in records if r.get("status") == "present")
#         absent = sum(1 for r in records if r.get("status") == "absent")

#         summary.append({
#             "date": col.id,
#             "present": present,
#             "absent": absent,
#             "total": len(records)
#         })

#         return summary


#     # ================= HELPERS =================

# def firestore_array_union(value):
#     from google.cloud.firestore_v1 import ArrayUnion
#     return ArrayUnion([value])


# def get_user_by_uid(uid):
#     db = get_firestore()
#     doc = db.collection("users").document(uid).get()
#     return doc.to_dict() if doc.exists else None


# def verify_teacher_login(email, password):
#     users = db.collection("users").stream()

#     for u in users:
#         data = u.to_dict()

#         if data.get("role") == "teacher":
#             if data.get("email") == email and data.get("password") == password:
#                 return {
#             "uid": u.id,
#             "name": data.get("name"),
#             "email": data.get("email")
#         }

#         raise PermissionError("Invalid credentials")




from datetime import datetime, date
import uuid, os
from config.firebase_config import get_firestore

db = get_firestore()

UPLOAD_FOLDER = "uploads"


# ================= TEACHERS =================

def add_teacher(name, email, password, subject):
    doc = db.collection("users").document()

    teacher_data = {
        "uid": doc.id,
        "name": name,
        "email": email,
        "password": password,
        "subject": subject,
        "role": "teacher",
        "class_ids": [],
        "created_at": datetime.now().isoformat()
    }

    doc.set(teacher_data)
    return teacher_data


def get_all_teachers():
    teachers = [doc.to_dict() for doc in db.collection("users").where("role", "==", "teacher").stream()]
    classes = [doc.to_dict() for doc in db.collection("classes").stream()]
    
    for t in teachers:
        t["class_ids"] = [c["class_id"] for c in classes if c.get("teacher_uid") == t["uid"]]
    
    return teachers


def delete_teacher(uid):
    db.collection("users").document(uid).delete()


    # ================= STUDENTS =================

def add_student(name, email, roll_number, face_encoding, image_bytes, filename):
    uid = str(uuid.uuid4())

    try:
        file_name = f"{uid}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        image_url = f"/uploads/{file_name}"

        data = {
            "uid": uid,
            "name": name,
            "email": email,
            "roll_number": roll_number,
            "role": "student",
            "face_encoding": face_encoding,
            "image_url": image_url,
            "class_ids": [],
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        db.collection("users").document(uid).set(data)
        return data

    except Exception as e:
        print("🔥 FIREBASE ERROR:", e)
        raise e


def get_all_students():
    students = [doc.to_dict() for doc in db.collection("users").where("role", "==", "student").stream()]
    classes = [doc.to_dict() for doc in db.collection("classes").stream()]
    
    for s in students:
        s["class_ids"] = [c["class_id"] for c in classes if s["uid"] in c.get("student_ids", [])]
    
    return students


def delete_student(uid):
    from google.cloud.firestore_v1 import ArrayRemove
    
    # 1. Remove student from all classes they are enrolled in
    classes = db.collection("classes").where("student_ids", "array_contains", uid).stream()
    for doc in classes:
        db.collection("classes").document(doc.id).update({
            "student_ids": ArrayRemove([uid])
        })
        
    # 2. Delete the student record
    db.collection("users").document(uid).delete()


    # ================= CLASSES =================

def create_class(name, teacher_uid, schedule):
    doc_ref = db.collection("classes").document()

    data = {
        "class_id": doc_ref.id,
        "name": name,
        "teacher_uid": teacher_uid,
        "schedule": schedule,
        "student_ids": [],
        "created_at": datetime.utcnow().isoformat()
    }

    doc_ref.set(data)

    print("🔥 SAVED CLASS:", data)

    return data


def get_all_classes():
    db = get_firestore()

    classes = []
    for doc in db.collection("classes").stream():
        data = doc.to_dict()
        data["class_id"] = doc.id
        classes.append(data)

    return classes   # ✅ OUTSIDE LOOP

def get_classes_for_teacher(teacher_uid):
    return [
doc.to_dict()
for doc in db.collection("classes").where("teacher_uid", "==", teacher_uid).stream()
]


def enroll_student_in_class(student_uid, class_id):
    from google.cloud.firestore_v1 import ArrayUnion

    class_ref = db.collection("classes").document(class_id)
    class_doc = class_ref.get()
    
    if not class_doc.exists:
        raise ValueError("Class not found")
        
    data = class_doc.to_dict()
    if student_uid in data.get("student_ids", []):
        return False, "Student is already enrolled in this class"

    # Add student to class
    class_ref.update({
        "student_ids": ArrayUnion([student_uid])
    })
    
    # Add class to student (for 2-way link)
    db.collection("users").document(student_uid).update({
        "class_ids": ArrayUnion([class_id])
    })
    
    return True, "Enrolled successfully"

def delete_class(class_id):
    db = get_firestore()
    db.collection("classes").document(class_id).delete()


    # ================= ATTENDANCE =================

def mark_attendance(class_id, student_uid, status, today=None):
    db = get_firestore()
    today = today or date.today().isoformat()
    
    # Fetch student details for better console visibility
    student_doc = db.collection("users").document(student_uid).get()
    s_data = student_doc.to_dict() if student_doc.exists else {}

    # Fetch Class Name for the 'Subject' field
    class_doc = db.collection("classes").document(class_id).get()
    c_data = class_doc.to_dict() if class_doc.exists else {}
    subject_name = c_data.get("name", "Unknown Class")

    # Standardizing on student_uid as the document ID for consistency across the app
    doc_id = student_uid

    db.collection("attendance").document(class_id).collection(today).document(doc_id).set({
        "status":       status,
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "student_uid":  student_uid,
        "name":         s_data.get("name", "Unknown"),
        "email":        s_data.get("email", "—"),
        "roll_number":  s_data.get("roll_number", "—"),
        "subject":      subject_name,
        "class_id":     class_id
    }, merge=True)


def get_attendance_for_class_date(class_id, day=None):
    day = day or date.today().isoformat()

    # 1. Get class to see which students are enrolled
    class_doc = db.collection("classes").document(class_id).get()
    if not class_doc.exists:
        return []
    
    enrolled_uids = class_doc.to_dict().get("student_ids", [])
    
    # 2. Get attendance records for this day
    docs = db.collection("attendance").document(class_id).collection(day).stream()
    attendance_map = {doc.id: doc.to_dict() for doc in docs}
    
    # 3. Get all students info
    all_students = {s["uid"]: s for s in get_all_students()}
    
    full_report = []
    for uid in enrolled_uids:
        s_info = all_students.get(uid, {"name": "Unknown", "email": "—", "roll_number": "—"})
        
        # Merge with attendance record if it exists
        record = attendance_map.get(uid, {
            "status": "not_marked",
            "timestamp": None,
            "student_uid": uid
        })
        
        full_report.append({
            "student_uid": uid,
            "name":        s_info.get("name"),
            "roll_number": s_info.get("roll_number"),
            "email":       s_info.get("email"),
            "status":      record.get("status"),
            "timestamp":   record.get("timestamp")
        })
            
    return full_report


def get_attendance_summary(class_id):
    collections = db.collection("attendance").document(class_id).collections()

    summary = []

    for col in collections:
        records = [d.to_dict() for d in col.stream()]

        present = sum(1 for r in records if r.get("status") == "present")
        absent = sum(1 for r in records if r.get("status") == "absent")

        summary.append({
            "date": col.id,
            "present": present,
            "absent": absent,
            "total": len(records)
        })

    return summary   # ✅ FIXED


    # ================= HELPERS =================

def get_user_by_uid(uid):
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def verify_teacher_login(email, password):
    users = db.collection("users").stream()

    for u in users:
        data = u.to_dict()

        if data.get("role") == "teacher":
            if data.get("email") == email and data.get("password") == password:
                return {
            "uid": u.id,
            "name": data.get("name"),
            "email": data.get("email")
        }

    raise PermissionError("Invalid credentials")
    
def get_student_encodings_for_class(class_id):
    db = get_firestore()

    class_doc = db.collection("classes").document(class_id).get()

    if not class_doc.exists:
        return {}

    class_data = class_doc.to_dict()
    student_ids = class_data.get("student_ids", [])

    encodings = {}

    for student_id in student_ids:
        student_doc = db.collection("users").document(student_id).get()

        if student_doc.exists:
            data = student_doc.to_dict()

            encodings[student_id] = data.get("face_encoding", [])
            encodings[student_id] = data["face_encoding"]

    return encodings