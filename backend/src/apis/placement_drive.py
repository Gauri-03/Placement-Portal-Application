from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db, User, PlacementDrive
from src.app import cache

driveAPI = Blueprint("driveAPI", __name__, url_prefix="/api/drives")


@driveAPI.route("", methods=["GET"]) #getting list of drives
@jwt_required()
def list_drives():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    search = request.args.get("search", "").strip()
    branch_filter = request.args.get("branch", "").strip()
    year_filter = request.args.get("year", "").strip()
    min_cgpa_filter = request.args.get("min_cgpa", "").strip()

    # Cache key is per-user + filters (eligibility annotation is user-specific)
    cache_key = f"drives_list_{user_id}_{search}_{branch_filter}_{year_filter}_{min_cgpa_filter}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    query = PlacementDrive.query.filter_by(status="approved")

    if search:
        from src.models import CompanyProfile as CP
        query = query.join(PlacementDrive.company).filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.job_description.ilike(f"%{search}%"),
                CP.company_name.ilike(f"%{search}%"),
            )
        )

    drives = query.order_by(PlacementDrive.created_at.desc()).all()

    result = []
    for drive in drives:
        d = drive.to_dict()

        if user.role == "student" and user.student_profile:
            eligible, reason = drive.is_student_eligible(user.student_profile)
            d["is_eligible"] = eligible
            d["eligibility_reason"] = reason if not eligible else None
        else:
            d["is_eligible"] = None
            d["eligibility_reason"] = None

        if branch_filter:
            branches = drive.get_eligible_branches()
            if branches and branch_filter not in branches:
                continue
        if year_filter:
            try:
                year_int = int(year_filter)
                years = drive.get_eligible_years()
                if years and year_int not in years:
                    continue
            except ValueError:
                pass
        if min_cgpa_filter:
            try:
                cgpa_val = float(min_cgpa_filter)
                if drive.min_cgpa is not None and drive.min_cgpa > cgpa_val:
                    continue
            except ValueError:
                pass

        result.append(d)

    cache.set(cache_key, result, timeout=300)
    return jsonify(result), 200


@driveAPI.route("/<int:drive_id>", methods=["GET"]) # geting drive by id
@jwt_required()
def get_drive(drive_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    cache_key = f"drive_{drive_id}_{user_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    drive = PlacementDrive.query.get_or_404(drive_id)

    if user.role == "student" and drive.status != "approved":
        return jsonify({"error": "Drive not found"}), 404

    d = drive.to_dict()

    if user.role == "student" and user.student_profile:
        eligible, reason = drive.is_student_eligible(user.student_profile)
        d["is_eligible"] = eligible
        d["eligibility_reason"] = reason if not eligible else None

    cache.set(cache_key, d, timeout=300)
    return jsonify(d), 200
