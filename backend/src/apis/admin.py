from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application
from src.app import cache

adminAPI = Blueprint("adminAPI", __name__, url_prefix="/api/admin")


def _require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return None, (jsonify({"error": "Admin access required"}), 403)
    return user, None 


@adminAPI.route("/dashboard", methods=["GET"]) #admin dashboard
@jwt_required()
def dashboard():
    _, err = _require_admin()
    if err:
        return err

    cached = cache.get("admin_dashboard")
    if cached is not None:
        return jsonify(cached), 200

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()

    result = {
        "total_students": total_students,
        "total_companies": total_companies,
        "total_drives": total_drives,
    }
    cache.set("admin_dashboard", result, timeout=300)
    return jsonify(result), 200



@adminAPI.route("/companies", methods=["GET"]) #list of companies with status and search
@jwt_required()
def list_companies():
    _, err = _require_admin()
    if err:
        return err

    status = request.args.get("status", "")
    search = request.args.get("search", "").strip()

    cache_key = f"admin_companies_{status}_{search}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    query = CompanyProfile.query.join(User)

    if status == "blacklisted":
        query = query.filter(User.is_blacklisted)
    elif status:
        query = query.filter(CompanyProfile.approval_status == status)

    if search:
        query = query.filter(
            db.or_(
                CompanyProfile.company_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    companies = query.all()
    result = [c.to_dict() for c in companies]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@adminAPI.route("/companies/<int:company_id>", methods=["GET"]) #company by uska id
@jwt_required()
def get_company(company_id):
    _, err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    return jsonify(company.to_dict()), 200


@adminAPI.route("/companies/<int:company_id>/approve", methods=["PATCH"]) #approving a company
@jwt_required()
def approve_company(company_id):
    _, err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    _invalidate_company_caches()
    return jsonify({"message": "Company approved.", "company": company.to_dict()}), 200


@adminAPI.route("/companies/<int:company_id>/reject", methods=["PATCH"]) #rejecting a company
@jwt_required()
def reject_company(company_id):
    _, err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    _invalidate_company_caches()
    return jsonify({"message": "Company rejected.", "company": company.to_dict()}), 200


@adminAPI.route("/companies/<int:company_id>/blacklist", methods=["PATCH"]) #blacklisting a company
@jwt_required()
def blacklist_company(company_id):
    _, err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    user = company.user
    user.is_blacklisted = not user.is_blacklisted 

    if user.is_blacklisted:
        if company.approval_status == "pending":
            company.approval_status = "rejected"
    else:
        company.approval_status = "pending"

    db.session.commit()
    _invalidate_company_caches()
    state = "blacklisted" if user.is_blacklisted else "un-blacklisted"
    return jsonify({
        "message": f"Company {state}.",
        "is_blacklisted": user.is_blacklisted,
        "approval_status": company.approval_status,
    }), 200


@adminAPI.route("/students", methods=["GET"]) #list of students with search
@jwt_required()
def list_students():
    _, err = _require_admin()
    if err:
        return err

    search = request.args.get("search", "").strip()

    cache_key = f"admin_students_{search}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    query = StudentProfile.query.join(User)

    if search:
        query = query.filter(
            db.or_(
                StudentProfile.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                StudentProfile.branch.ilike(f"%{search}%"),
            )
        )

    students = query.all()
    result = [s.to_dict() for s in students]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@adminAPI.route("/students/<int:student_id>", methods=["GET"]) #student by id
@jwt_required()
def get_student(student_id):
    _, err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    return jsonify(student.to_dict()), 200


@adminAPI.route("/students/<int:student_id>/blacklist", methods=["PATCH"]) #blacklisting a student
@jwt_required()
def blacklist_student(student_id):
    _, err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    user = student.user
    user.is_blacklisted = not user.is_blacklisted  # toggle
    db.session.commit()
    _invalidate_student_caches()
    state = "blacklisted" if user.is_blacklisted else "un-blacklisted"
    return jsonify({"message": f"Student {state}.", "is_blacklisted": user.is_blacklisted}), 200


@adminAPI.route("/drives", methods=["GET"]) #list of drives with stayus
@jwt_required()
def list_drives():
    _, err = _require_admin()
    if err:
        return err

    status = request.args.get("status", "")

    cache_key = f"admin_drives_{status}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    query = PlacementDrive.query
    if status:
        query = query.filter(PlacementDrive.status == status)

    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    result = [d.to_dict() for d in drives]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@adminAPI.route("/drives/<int:drive_id>/approve", methods=["PATCH"]) #approvinf a drive
@jwt_required()
def approve_drive(drive_id):
    _, err = _require_admin()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    _invalidate_drive_caches(drive_id)
    return jsonify({"message": "Drive approved.", "drive": drive.to_dict()}), 200


@adminAPI.route("/drives/<int:drive_id>/reject", methods=["PATCH"]) #rejecying a drive
@jwt_required()
def reject_drive(drive_id):
    _, err = _require_admin()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "rejected"
    db.session.commit()
    _invalidate_drive_caches(drive_id)
    return jsonify({"message": "Drive rejected.", "drive": drive.to_dict()}), 200


@adminAPI.route("/students/<int:student_id>/applications", methods=["GET"]) #student specific application to a drive
@jwt_required()
def student_applications(student_id):
    _, err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    applications = Application.query.filter_by(student_id=student.id).order_by(Application.applied_at.desc()).all()
    return jsonify({
        "student": student.to_dict(),
        "applications": [a.to_dict(include_drive=True) for a in applications],
    }), 200


@adminAPI.route("/applications", methods=["GET"]) #all applications
@jwt_required()
def list_applications():
    _, err = _require_admin()
    if err:
        return err

    applications = Application.query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict(include_student=True, include_drive=True) for a in applications]), 200


@adminAPI.route("/trigger/daily-reminders", methods=["POST"]) #daily reminders button for demo
@jwt_required()
def trigger_daily_reminders():
    _, err = _require_admin()
    if err:
        return err

    from src.workers.task import send_daily_reminders
    task = send_daily_reminders.delay()
    return jsonify({"message": "Daily reminder task queued.", "task_id": task.id}), 202


@adminAPI.route("/trigger/monthly-report", methods=["POST"]) #monthly report button for demo
@jwt_required()
def trigger_monthly_report():
    _, err = _require_admin()
    if err:
        return err

    from src.workers.task import send_monthly_report
    task = send_monthly_report.delay()
    return jsonify({"message": "Monthly report task queued.", "task_id": task.id}), 202


# ─────────────────────────────────────────────
# Cache invalidation helpers
# ─────────────────────────────────────────────

def _invalidate_drive_caches(drive_id=None):
    """Invalidate all admin drive list caches and the specific drive cache."""
    for status in ("", "pending", "approved", "rejected", "closed"):
        cache.delete(f"admin_drives_{status}")
    cache.delete("admin_dashboard")
    if drive_id:
        cache.delete(f"drive_{drive_id}")
    # Also bust the public drives list (all possible cache keys are pattern-based,
    # so we clear the known static ones and rely on TTL for user-specific keys)
    cache.delete("drives_list")


def _invalidate_company_caches():
    """Invalidate admin company list caches and dashboard."""
    for status in ("", "pending", "approved", "rejected", "blacklisted"):
        cache.delete(f"admin_companies_{status}_")
    cache.delete("admin_dashboard")


def _invalidate_student_caches():
    """Invalidate admin student list caches and dashboard."""
    cache.delete("admin_students_")
    cache.delete("admin_dashboard")
