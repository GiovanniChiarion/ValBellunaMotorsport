from datetime import UTC, datetime

from flask import Flask, g, request

from app.audit import log_action
from app.auth import jwt_manager, optional_auth
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import User


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    settings = get_settings()

    app.config["SECRET_KEY"] = settings.secret_key
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.jwt_expire_minutes * 60
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
    app.config["JWT_COOKIE_SECURE"] = not settings.debug
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_CSRF_IN_COOKIES"] = True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_HEADER_TYPE"] = "Bearer"

    if test_config:
        app.config.update(test_config)

    jwt_manager.init_app(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.races import races_bp
    from app.blueprints.participation import participation_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.history import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(races_bp)
    app.register_blueprint(participation_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(history_bp)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": getattr(g, "current_user", None),
            "now": datetime.now(UTC),
        }

    @app.route("/")
    @optional_auth
    def home():
        user = getattr(g, "current_user", None)
        if user is None:
            from flask import redirect, url_for

            return redirect(url_for("auth.login_page"))
        from flask import redirect, url_for

        return redirect(url_for("races.calendar_view"))

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        }

    @app.before_request
    def initialize_db():
        if not hasattr(g, "_db_initialized"):
            Base.metadata.create_all(bind=engine)
            from app.auth import hash_password

            with get_db() as db:
                admin = db.query(User).filter(User.ruolo == "admin").first()
                if not admin:
                    admin = User(
                        nome="Admin",
                        email="admin@valbellunamotorsport.it",
                        password_hash=hash_password("admin123"),
                        ruolo="admin",
                    )
                    db.add(admin)
                    db.flush()
                    log_action(
                        db=db,
                        action="CREATE",
                        entity_type="user",
                        entity_id=admin.id,
                        actor_name="system",
                        description="Admin predefinito creato automaticamente",
                    )
                    db.commit()
                superadmin = db.query(User).filter(User.ruolo == "superadmin").first()
                if not superadmin:
                    superadmin = User(
                        nome="SuperAdmin",
                        email="superadmin@valbellunamotorsport.it",
                        password_hash=hash_password("superadmin123"),
                        ruolo="superadmin",
                    )
                    db.add(superadmin)
                    db.flush()
                    log_action(
                        db=db,
                        action="CREATE",
                        entity_type="user",
                        entity_id=superadmin.id,
                        actor_name="system",
                        description="SuperAdmin predefinito creato automaticamente",
                    )
                    db.commit()
            g._db_initialized = True

    @app.before_request
    def log_page_view():
        if request.method != "GET":
            return
        if request.path == "/health":
            return
        user = getattr(g, "current_user", None)
        if not user:
            return
        if not get_settings().log_page_views:
            return
        with get_db() as db:
            log_action(
                db=db,
                action="VIEW",
                entity_type=request.path.split("/")[1] if request.path.count("/") > 0 else "page",
                description=f"{user.nome} ha visitato {request.path}",
            )
            db.commit()

    return app
