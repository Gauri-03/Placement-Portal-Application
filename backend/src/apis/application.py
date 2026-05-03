from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from src.models import db, User, Application, PlacementDrive

applicationAPI = Blueprint("applicationAPI", __name__, url_prefix="/api/applications")


def _get_student(user_id): #gets a student
    user = User.query.get(user_id)
    if not user or user.role != "student":
        return None, (jsonify({"error": "Student access required"}), 403)
    if user.is_blacklisted:
        return None, (jsonify({"error": "Your account is blacklisted"}), 403)
    profile = user.student_profile
    if not profile:
        return None, (jsonify({"error": "Student profile not found"}), 404)
    return profile, None


@applicationAPI.route("", methods=["POST"]) #application to a drive
@jwt_required()
def apply():
    user_id = int(get_jwt_identity())
    student, err = _get_student(user_id)
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    drive_id = data.get("drive_id")
    if not drive_id:
        return jsonify({"error": "drive_id is required"}), 400

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found"}), 404

    if drive.status != "approved":
        return jsonify({"error": "This drive is not open for applications"}), 400

    now = datetime.now(timezone.utc)
    deadline = drive.application_deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now > deadline:
        return jsonify({"error": "Application deadline has passed"}), 400

    eligible, reason = drive.is_student_eligible(student)
    if not eligible:
        return jsonify({"error": reason}), 403

    existing = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing:
        return jsonify({"error": "You have already applied to this drive"}), 409

    application = Application(
        student_id=student.id,
        drive_id=drive.id,
        status="applied",
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({"message": "Application submitted successfully.", "application": application.to_dict()}), 201


@applicationAPI.route("/<int:app_id>", methods=["GET"]) #getting an application by id
@jwt_required()
def get_application(app_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    application = Application.query.get_or_404(app_id)

    if user.role == "student":
        if not user.student_profile or application.student_id != user.student_profile.id:
            return jsonify({"error": "Access denied"}), 403

    return jsonify(application.to_dict(include_student=True, include_drive=True)), 200


@applicationAPI.route("/export", methods=["POST"]) #exporting application as csv
@jwt_required()
def export_applications():
    user_id = int(get_jwt_identity())
    student, err = _get_student(user_id)
    if err:
        return err

    from src.workers.task import export_applications_csv
    student_email = student.user.email if student.user else None
    if not student_email:
        return jsonify({"error": "Student email not found"}), 400

    task = export_applications_csv.delay(student.id, student_email)
    return jsonify({
        "message": "Your placement history export has been queued. You will receive an email shortly.",
        "task_id": task.id,
    }), 202
