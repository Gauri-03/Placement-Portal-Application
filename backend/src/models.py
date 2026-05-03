from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False)  # admin, company, student
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile = db.relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship("CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_blacklisted": self.is_blacklisted,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    full_name = db.Column(db.String(), nullable=False)
    branch = db.Column(db.String(), nullable=False)   # like CS, ECE, ME
    cgpa = db.Column(db.Float, nullable=False)
    year = db.Column(db.Integer, nullable=False)          # 1, 2, 3, 4
    resume_path = db.Column(db.String(), nullable=True)  

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "full_name": self.full_name,
            "branch": self.branch,
            "cgpa": self.cgpa,
            "year": self.year,
            "resume_path": self.resume_path,
            "is_blacklisted": self.user.is_blacklisted if self.user else None,
        }

    def __repr__(self):
        return f"<StudentProfile {self.full_name}>"

class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    company_name = db.Column(db.String(), nullable=False)
    hr_contact_email = db.Column(db.String(), nullable=True)
    website = db.Column(db.String(), nullable=True)
    description = db.Column(db.Text, nullable=True)

    approval_status = db.Column(db.String(20), default="pending", nullable=False) #pending, approved, rejected

    user = db.relationship("User", back_populates="company_profile")
    placement_drives = db.relationship("PlacementDrive", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "company_name": self.company_name,
            "hr_contact_email": self.hr_contact_email,
            "website": self.website,
            "description": self.description,
            "approval_status": self.approval_status,
            "is_blacklisted": self.user.is_blacklisted if self.user else None,
        }

    def __repr__(self):
        return f"<CompanyProfile {self.company_name}>"


class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company_profiles.id"), nullable=False)

    job_title = db.Column(db.String(), nullable=False)
    job_description = db.Column(db.Text, nullable=True)

    eligible_branches = db.Column(db.String(), nullable=True)  # like CS,ECE,IT
    min_cgpa = db.Column(db.Float, nullable=True)
    eligible_years = db.Column(db.String(), nullable=True)       # 3,4

    application_deadline = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(), default="pending", nullable=False)  #pending, approved, rejected, closed

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    company = db.relationship("CompanyProfile", back_populates="placement_drives")
    applications = db.relationship("Application", back_populates="drive", cascade="all, delete-orphan")

    def get_eligible_branches(self):
        if not self.eligible_branches:
            return []
        return [b.strip() for b in self.eligible_branches.split(",") if b.strip()] #list of eligible barnches

    def get_eligible_years(self):
        if not self.eligible_years:
            return []
        return [int(y.strip()) for y in self.eligible_years.split(",") if y.strip().isdigit()] #list of eligible years as integers

    def is_student_eligible(self, student_profile):

        branches = self.get_eligible_branches()
        if branches and student_profile.branch not in branches:
            return False, f"Your branch ({student_profile.branch}) is not eligible for this drive."

        if self.min_cgpa is not None and student_profile.cgpa < self.min_cgpa:
            return False, f"Minimum CGPA required is {self.min_cgpa}. Your CGPA is {student_profile.cgpa}."

        years = self.get_eligible_years()
        if years and student_profile.year not in years:
            return False, f"Your year ({student_profile.year}) is not eligible for this drive."

        return True, "Eligible" #checks eligibility criteria for student

    def to_dict(self, include_company=True):
        data = {
            "id": self.id,
            "company_id": self.company_id,
            "job_title": self.job_title,
            "job_description": self.job_description,
            "eligible_branches": self.get_eligible_branches(),
            "min_cgpa": self.min_cgpa,
            "eligible_years": self.get_eligible_years(),
            "application_deadline": self.application_deadline.isoformat() if self.application_deadline else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "applicant_count": len(self.applications),
        }
        if include_company and self.company:
            data["company_name"] = self.company.company_name
            data["company_website"] = self.company.website
        return data

    def __repr__(self):
        return f"<PlacementDrive {self.job_title} by company_id={self.company_id}>"


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)

    status = db.Column(db.String(), default="applied", nullable=False) #applied, shortlisted, selected, rejected

    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),)

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    student = db.relationship("StudentProfile", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")

    def to_dict(self, include_student=False, include_drive=True):
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "drive_id": self.drive_id,
            "status": self.status,
            "applied_at": self.applied_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_drive and self.drive:
            data["job_title"] = self.drive.job_title
            data["company_name"] = self.drive.company.company_name if self.drive.company else None
            data["drive_status"] = self.drive.status
        if include_student and self.student:
            data["student_name"] = self.student.full_name
            data["student_email"] = self.student.user.email if self.student.user else None
            data["student_branch"] = self.student.branch
            data["student_cgpa"] = self.student.cgpa
        return data

    def __repr__(self):
        return f"<Application student_id={self.student_id} drive_id={self.drive_id} status={self.status}>"
