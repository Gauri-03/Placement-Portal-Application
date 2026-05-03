from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db, User, PlacementDrive, Application
from src.app import cache
from datetime import datetime, timezone

companyAPI = Blueprint("companyAPI", __name__, url_prefix="/api/company")


def _require_company(): #getting a company
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != "company":
        return None, (jsonify({"error": "Company access required"}), 403)
    if user.is_blacklisted:
        return None, (jsonify({"error": "Your account is blacklisted"}), 403)
    profile = user.company_profile
    if not profile or profile.approval_status != "approved":
        return None, (jsonify({"error": "Your company is not approved yet"}), 403)
    return profile, None


@companyAPI.route("/dashboard", methods=["GET"]) #company dashboard
@jwt_required()
def dashboard():
    company, err = _require_company()
    if err:
        return err

    cache_key = f"company_dashboard_{company.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    drives_data = [drive.to_dict(include_company=False) for drive in drives]

    result = {
        "company": company.to_dict(),
        "drives": drives_data,
    }
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@companyAPI.route("/profile", methods=["GET"]) #company profile get
@jwt_required()
def get_profile():
    company, err = _require_company()
    if err:
        return err
    return jsonify(company.to_dict()), 200


@companyAPI.route("/profile", methods=["PUT"]) #company profile update
@jwt_required()
def update_profile():
    company, err = _require_company()
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "company_name" in data:
        name = data["company_name"].strip()
        if not name:
            return jsonify({"error": "company_name cannot be empty"}), 400
        company.company_name = name
    if "hr_contact_email" in data:
        company.hr_contact_email = data["hr_contact_email"].strip() or None
    if "website" in data:
        company.website = data["website"].strip() or None
    if "description" in data:
        company.description = data["description"].strip() or None

    db.session.commit()
    cache.delete(f"company_dashboard_{company.id}")
    return jsonify({"message": "Profile updated.", "company": company.to_dict()}), 200


@companyAPI.route("/drives", methods=["GET"]) #getting drives
@jwt_required()
def list_drives():
    company, err = _require_company()
    if err:
        return err

    cache_key = f"company_drives_{company.id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(PlacementDrive.created_at.desc()).all()
    result = [d.to_dict(include_company=False) for d in drives]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@companyAPI.route("/drives", methods=["POST"]) #creating a new drive
@jwt_required()
def create_drive():
    company, err = _require_company()
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    job_title = data.get("job_title", "").strip()
    application_deadline = data.get("application_deadline")

    if not job_title:
        return jsonify({"error": "job_title is required"}), 400
    if not application_deadline:
        return jsonify({"error": "application_deadline is required"}), 400

    try:
        deadline_dt = datetime.fromisoformat(application_deadline)
    except ValueError:
        return jsonify({"error": "application_deadline must be ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

    eligible_branches = data.get("eligible_branches")
    eligible_years = data.get("eligible_years")
    min_cgpa = data.get("min_cgpa")

    branches_str = None
    if eligible_branches:
        branches_str = ",".join(str(b).strip() for b in eligible_branches if str(b).strip())

    years_str = None
    if eligible_years:
        years_str = ",".join(str(y).strip() for y in eligible_years if str(y).strip())

    if min_cgpa is not None:
        try:
            min_cgpa = float(min_cgpa)
        except (ValueError, TypeError):
            return jsonify({"error": "min_cgpa must be a number"}), 400

    drive = PlacementDrive(
        company_id=company.id,
        job_title=job_title,
        job_description=data.get("job_description", "").strip() or None,
        eligible_branches=branches_str,
        min_cgpa=min_cgpa,
        eligible_years=years_str,
        application_deadline=deadline_dt,
        status="pending",
    )
    db.session.add(drive)
    db.session.commit()

    cache.delete(f"company_drives_{company.id}")
    cache.delete(f"company_dashboard_{company.id}")
    from src.apis.admin import _invalidate_drive_caches
    _invalidate_drive_caches()

    return jsonify({"message": "Drive created. Pending admin approval.", "drive": drive.to_dict(include_company=False)}), 201


@companyAPI.route("/drives/<int:drive_id>", methods=["GET"]) #getting specific drive by id
@jwt_required()
def get_drive(drive_id):
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    return jsonify(drive.to_dict(include_company=False)), 200


@companyAPI.route("/drives/<int:drive_id>", methods=["PUT"]) #updaing drive info
@jwt_required()
def update_drive(drive_id):
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    if drive.status != "pending":
        return jsonify({"error": "Only pending drives can be edited"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "job_title" in data:
        job_title = data["job_title"].strip()
        if not job_title:
            return jsonify({"error": "job_title cannot be empty"}), 400
        drive.job_title = job_title

    if "job_description" in data:
        drive.job_description = data["job_description"].strip() or None

    if "application_deadline" in data:
        try:
            drive.application_deadline = datetime.fromisoformat(data["application_deadline"])
        except ValueError:
            return jsonify({"error": "application_deadline must be ISO format"}), 400

    if "eligible_branches" in data:
        branches = data["eligible_branches"]
        if branches:
            drive.eligible_branches = ",".join(str(b).strip() for b in branches if str(b).strip())
        else:
            drive.eligible_branches = None

    if "eligible_years" in data:
        years = data["eligible_years"]
        if years:
            drive.eligible_years = ",".join(str(y).strip() for y in years if str(y).strip())
        else:
            drive.eligible_years = None

    if "min_cgpa" in data:
        if data["min_cgpa"] is None or data["min_cgpa"] == "":
            drive.min_cgpa = None
        else:
            try:
                drive.min_cgpa = float(data["min_cgpa"])
            except (ValueError, TypeError):
                return jsonify({"error": "min_cgpa must be a number"}), 400

    db.session.commit()

    # Invalidate caches
    cache.delete(f"company_drives_{company.id}")
    cache.delete(f"company_dashboard_{company.id}")

    return jsonify({"message": "Drive updated.", "drive": drive.to_dict(include_company=False)}), 200


@companyAPI.route("/drives/<int:drive_id>/close", methods=["PATCH"]) #closing a dribe
@jwt_required()
def close_drive(drive_id):
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()
    if drive.status != "approved":
        return jsonify({"error": "Only approved drives can be closed"}), 400

    drive.status = "closed"
    db.session.commit()

    # Invalidate caches
    cache.delete(f"company_drives_{company.id}")
    cache.delete(f"company_dashboard_{company.id}")
    from src.apis.admin import _invalidate_drive_caches
    _invalidate_drive_caches(drive.id)

    return jsonify({"message": "Drive closed.", "drive": drive.to_dict(include_company=False)}), 200


@companyAPI.route("/drives/<int:drive_id>/applications", methods=["GET"]) #getting applications according to dirve
@jwt_required()
def drive_applications(drive_id):
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    cache_key = f"company_drive_applications_{drive_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    applications = Application.query.filter_by(drive_id=drive.id).all()
    result = [a.to_dict(include_student=True, include_drive=False) for a in applications]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@companyAPI.route("/applications/<int:app_id>/status", methods=["PATCH"]) #upadting application status 
@jwt_required()
def update_application_status(app_id):
    company, err = _require_company()
    if err:
        return err

    application = Application.query.get_or_404(app_id)

    drive = PlacementDrive.query.filter_by(id=application.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Application not found for your drives"}), 404

    data = request.get_json()
    new_status = data.get("status", "").lower()
    allowed = ("shortlisted", "selected", "rejected")
    if new_status not in allowed:
        return jsonify({"error": f"Status must be one of: {', '.join(allowed)}"}), 400

    application.status = new_status
    application.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Invalidate the applications cache for this drive
    cache.delete(f"company_drive_applications_{drive.id}")

    return jsonify({"message": f"Application status updated to '{new_status}'.", "application": application.to_dict(include_student=True)}), 200
