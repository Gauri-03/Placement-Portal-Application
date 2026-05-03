from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models import db, User, StudentProfile, CompanyProfile

authAPI = Blueprint("authAPI", __name__, url_prefix="/api/auth")


@authAPI.route("/register/student", methods=["POST"]) #register student
def register_student():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    branch = data.get("branch", "").strip()
    cgpa = data.get("cgpa")
    year = data.get("year")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not full_name or not branch or cgpa is None or year is None:
        return jsonify({"error": "full_name, branch, cgpa, and year are required"}), 400

    try:
        cgpa = float(cgpa)
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({"error": "cgpa must be a number and year must be an integer"}), 400

    if not (0.0 <= cgpa <= 10.0):
        return jsonify({"error": "CGPA must be between 0.0 and 10.0"}), 400
    if year not in (1, 2, 3, 4):
        return jsonify({"error": "Year must be 1, 2, 3, or 4"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, role="student")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = StudentProfile(
        user_id=user.id,
        full_name=full_name,
        branch=branch,
        cgpa=cgpa,
        year=year,
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify({"message": "Student registered successfully."}), 201


@authAPI.route("/register/company", methods=["POST"]) #register company
def register_company():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    company_name = data.get("company_name", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not company_name:
        return jsonify({"error": "company_name is required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, role="company")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        hr_contact_email=data.get("hr_contact_email", "").strip() or None,
        website=data.get("website", "").strip() or None,
        description=data.get("description", "").strip() or None,
        approval_status="pending",
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify({"message": "Company registered successfully. Pending admin approval."}), 201


@authAPI.route("/login", methods=["POST"]) #login
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if user.is_blacklisted:
        return jsonify({"error": "Your account has been blacklisted. Contact admin."}), 403

    if user.role == "company":
        profile = user.company_profile
        if profile and profile.approval_status == "pending":
            return jsonify({"error": "Your company registration is pending admin approval."}), 403
        if profile and profile.approval_status == "rejected":
            return jsonify({"error": "Your company registration was rejected."}), 403

    token = create_access_token(identity=str(user.id))

    profile_data = None
    if user.role == "student" and user.student_profile:
        profile_data = user.student_profile.to_dict()
    elif user.role == "company" and user.company_profile:
        profile_data = user.company_profile.to_dict()

    return jsonify({
        "access_token": token,
        "user": user.to_dict(),
        "profile": profile_data,
    }), 200


@authAPI.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    profile_data = None
    if user.role == "student" and user.student_profile:
        profile_data = user.student_profile.to_dict()
    elif user.role == "company" and user.company_profile:
        profile_data = user.company_profile.to_dict()

    return jsonify({
        "user": user.to_dict(),
        "profile": profile_data,
    }), 200
