import csv
import io
import os
from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from src.models import db, User, Application
from datetime import datetime, timezone

studentAPI = Blueprint("studentAPI", __name__, url_prefix="/api/student")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _require_student(): #getting student profile
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != "student":
        return None, (jsonify({"error": "Student access required"}), 403)
    if user.is_blacklisted:
        return None, (jsonify({"error": "Your account is blacklisted"}), 403)
    profile = user.student_profile
    if not profile:
        return None, (jsonify({"error": "Student profile not found"}), 404)
    return profile, None


@studentAPI.route("/profile", methods=["GET"])#getting profile
@jwt_required()
def get_profile():
    student, err = _require_student()
    if err:
        return err
    return jsonify(student.to_dict()), 200


@studentAPI.route("/profile", methods=["PUT"]) #updating a profile
@jwt_required()
def update_profile():
    student, err = _require_student()
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "full_name" in data:
        name = data["full_name"].strip()
        if not name:
            return jsonify({"error": "full_name cannot be empty"}), 400
        student.full_name = name

    if "branch" in data:
        branch = data["branch"].strip()
        if not branch:
            return jsonify({"error": "branch cannot be empty"}), 400
        student.branch = branch

    if "cgpa" in data:
        try:
            cgpa = float(data["cgpa"])
        except (ValueError, TypeError):
            return jsonify({"error": "cgpa must be a number"}), 400
        if not (0.0 <= cgpa <= 10.0):
            return jsonify({"error": "CGPA must be between 0.0 and 10.0"}), 400
        student.cgpa = cgpa

    if "year" in data:
        try:
            year = int(data["year"])
        except (ValueError, TypeError):
            return jsonify({"error": "year must be an integer"}), 400
        if year not in (1, 2, 3, 4):
            return jsonify({"error": "Year must be 1, 2, 3, or 4"}), 400
        student.year = year

    db.session.commit()
    return jsonify({"message": "Profile updated.", "profile": student.to_dict()}), 200


@studentAPI.route("/profile/resume", methods=["POST"]) #uploading rsume
@jwt_required()
def upload_resume():
    student, err = _require_student()
    if err:
        return err

    if "resume" not in request.files:
        return jsonify({"error": "No file provided. Use key 'resume'"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Only PDF, DOC, and DOCX files are allowed"}), 400

    filename = secure_filename(f"student_{student.id}_{file.filename}")
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    student.resume_path = f"uploads/resumes/{filename}"
    db.session.commit()

    return jsonify({"message": "Resume uploaded.", "resume_path": student.resume_path}), 200


@studentAPI.route("/profile/resume", methods=["DELETE"]) #deleting a rsume
@jwt_required()
def delete_resume():
    student, err = _require_student()
    if err:
        return err

    if not student.resume_path:
        return jsonify({"error": "No resume to delete"}), 404

    static_folder = os.path.join(current_app.root_path, "static")
    filepath = os.path.join(static_folder, student.resume_path)
    if os.path.exists(filepath):
        os.remove(filepath)

    student.resume_path = None
    db.session.commit()

    return jsonify({"message": "Resume deleted."}), 200


@studentAPI.route("/applications", methods=["GET"]) #getting all student specific applications
@jwt_required()
def my_applications():
    student, err = _require_student()
    if err:
        return err

    applications = Application.query.filter_by(student_id=student.id).order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict(include_drive=True) for a in applications]), 200


# GET /api/student/applications/export
# Directly generates and returns a CSV file for download (no Celery, no email)
@studentAPI.route("/applications/export", methods=["GET"])
@jwt_required()
def export_applications_csv():
    student, err = _require_student()
    if err:
        return err

    applications = Application.query.filter_by(student_id=student.id).order_by(
        Application.applied_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Student ID",
        "Student Name",
        "Company Name",
        "Job Title",
        "Application Status",
        "Applied Date",
        "Last Updated",
    ])

    # Data rows
    for app in applications:
        company_name = ""
        job_title = ""
        if app.drive:
            job_title = app.drive.job_title
            if app.drive.company:
                company_name = app.drive.company.company_name

        writer.writerow([
            student.id,
            student.full_name,
            company_name,
            job_title,
            app.status,
            app.applied_at.strftime("%Y-%m-%d %H:%M UTC") if app.applied_at else "",
            app.updated_at.strftime("%Y-%m-%d %H:%M UTC") if app.updated_at else "",
        ])

    csv_content = output.getvalue()
    output.close()

    filename = f"placement_history_{student.id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
