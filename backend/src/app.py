import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_cors import CORS

from src.models import db, bcrypt

jwt = JWTManager()
cache = Cache()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'launchpad.db')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-change-in-prod")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 86400  

    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.environ.get("REDIS_CACHE_URL", "redis://localhost:6379/1")
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300  

    app.config["CELERY_BROKER_URL"] = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    app.config["CELERY_RESULT_BACKEND"] = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads", "resumes")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  
    app.config["ALLOWED_EXTENSIONS"] = {"pdf", "doc", "docx"}

    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "localhost")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 1025))
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USERNAME"] = None
    app.config["MAIL_PASSWORD"] = None
    app.config["MAIL_DEFAULT_SENDER"] = "noreply@launchpad.com"
    app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", "admin@launchpad.com")


    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})


    from src.apis.auth import authAPI
    from src.apis.admin import adminAPI
    from src.apis.company import companyAPI
    from src.apis.student import studentAPI
    from src.apis.placement_drive import driveAPI
    from src.apis.application import applicationAPI

    app.register_blueprint(authAPI)
    app.register_blueprint(adminAPI)
    app.register_blueprint(companyAPI)
    app.register_blueprint(studentAPI)
    app.register_blueprint(driveAPI)
    app.register_blueprint(applicationAPI)

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    from src.models import User

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@launchpad.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

    existing = User.query.filter_by(role="admin").first()
    if not existing:
        admin = User(email=admin_email, role="admin")
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"[LaunchPad] Admin user created: {admin_email}")
    else:
        print(f"[LaunchPad] Admin user already exists: {existing.email}")
