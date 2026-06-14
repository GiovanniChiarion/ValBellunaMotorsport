from flask import Blueprint, g, jsonify, render_template, request
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)

from app.audit import log_action
from app.auth import admin_required, hash_password, jwt_required, verify_password
from app.database import get_db
from app.forms import (
    LoginForm,
    RegisterForm,
    SelfChangeEmailForm,
    SelfChangePasswordForm,
)
from app.models import AuditLog, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

registration_tokens: set[str] = set()


@auth_bp.route("/login", methods=["GET"])
def login_page():
    form = LoginForm()
    return render_template("login.html", form=form)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"detail": "Email e password richieste"}), 400

    with get_db() as db:
        user = db.query(User).filter(User.email == email, User.attivo == 1).first()

    if not user or not verify_password(password, user.password_hash):
        with get_db() as db:
            log_action(
                db=db,
                action="LOGIN_FAILED",
                entity_type="auth",
                description=f"Login fallito: {email}",
            )
            db.commit()
        return jsonify({"detail": "Email o password non validi"}), 401

    access_token = create_access_token(identity=str(user.id))
    with get_db() as db:
        log_action(
            db=db,
            action="LOGIN",
            entity_type="auth",
            user_id=user.id,
            actor_name=user.nome,
            description=f"Login: {user.nome}",
        )
        db.commit()
    response = jsonify(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
                "ruolo": user.ruolo,
            },
        }
    )
    set_access_cookies(response, access_token)
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    user = getattr(g, "current_user", None)
    with get_db() as db:
        log_action(
            db=db,
            action="LOGOUT",
            entity_type="auth",
            user_id=user.id if user else None,
            actor_name=user.nome if user else None,
            description=f"Logout: {user.nome}" if user else "Logout",
        )
        db.commit()
    response = jsonify({"message": "Logout effettuato"})
    unset_jwt_cookies(response)
    return response


@auth_bp.route("/register", methods=["GET"])
def register_page():
    form = RegisterForm()
    return render_template("register.html", form=form)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or request.form.to_dict()
    token = data.get("token", "")

    if token not in registration_tokens:
        return jsonify({"detail": "Token di registrazione non valido"}), 400

    nome = data.get("nome", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not nome or not email or not password:
        return jsonify({"detail": "Tutti i campi sono obbligatori"}), 400

    if len(password) < 6:
        return jsonify({"detail": "La password deve essere di almeno 6 caratteri"}), 400

    with get_db() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"detail": "Email già registrata"}), 400

        user = User(
            nome=nome,
            email=email,
            password_hash=hash_password(password),
            ruolo="membro",
            attivo=1,
        )
        db.add(user)
        db.flush()
        log_action(
            db=db,
            action="REGISTER",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            actor_name=user.nome,
            description=f"Registrato: {user.nome}",
        )
        db.commit()
        db.refresh(user)
        registration_tokens.discard(token)

    access_token = create_access_token(identity=str(user.id))
    response = jsonify(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
                "ruolo": user.ruolo,
            },
        }
    )
    set_access_cookies(response, access_token)
    return response


@auth_bp.route("/register/token", methods=["GET"])
@admin_required
def generate_registration_token():
    import secrets

    token = secrets.token_urlsafe(32)
    registration_tokens.add(token)
    with get_db() as db:
        log_action(
            db=db,
            action="TOKEN_GENERATE",
            entity_type="auth",
            description=f"Token generato da {g.current_user.nome}",
        )
        db.commit()
    return jsonify({"token": token})


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_me():
    user = g.current_user
    return jsonify(
        {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "ruolo": user.ruolo,
            "attivo": user.attivo,
        }
    )


@auth_bp.route("/settings", methods=["GET"])
@jwt_required
def settings_page():
    pwd_form = SelfChangePasswordForm()
    email_form = SelfChangeEmailForm()
    return render_template("settings.html", pwd_form=pwd_form, email_form=email_form)


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required
def change_own_password():
    user = g.current_user
    data = request.get_json(silent=True) or {}

    if not verify_password(data.get("current_password", ""), user.password_hash):
        return jsonify({"detail": "Password attuale non corretta"}), 400

    new_password = data.get("new_password", "")
    confirm = data.get("new_password_confirm", "")

    if not new_password or len(new_password) < 6:
        return jsonify(
            {"detail": "La nuova password deve essere di almeno 6 caratteri"}
        ), 400

    if new_password != confirm:
        return jsonify({"detail": "Le password non coincidono"}), 400

    with get_db() as db:
        db_user = db.query(User).filter(User.id == user.id).first()
        if not db_user:
            return jsonify({"detail": "Utente non trovato"}), 404
        db_user.password_hash = hash_password(new_password)
        log_action(
            db=db,
            action="PASSWORD_CHANGE",
            entity_type="user",
            entity_id=user.id,
            description=f"Password cambiata: {user.nome}",
        )
        db.commit()

    return jsonify({"message": "Password cambiata con successo"})


@auth_bp.route("/change-email", methods=["POST"])
@jwt_required
def change_own_email():
    user = g.current_user
    data = request.get_json(silent=True) or {}

    if not verify_password(data.get("password", ""), user.password_hash):
        return jsonify({"detail": "Password non corretta"}), 400

    new_email = data.get("new_email", "").strip().lower()
    if not new_email:
        return jsonify({"detail": "Email richiesta"}), 400

    with get_db() as db:
        existing = (
            db.query(User).filter(User.email == new_email, User.id != user.id).first()
        )
        if existing:
            return jsonify({"detail": "Email già in uso"}), 400

        db_user = db.query(User).filter(User.id == user.id).first()
        if not db_user:
            return jsonify({"detail": "Utente non trovato"}), 404
        old_email = db_user.email
        db_user.email = new_email
        log_action(
            db=db,
            action="EMAIL_CHANGE",
            entity_type="user",
            entity_id=user.id,
            field="user.email",
            old_value=old_email,
            new_value=new_email,
            description=f"Email cambiata: {user.nome}: {old_email} → {new_email}",
        )
        db.commit()

    return jsonify({"message": "Email cambiata con successo"})


@auth_bp.route("/admin/<int:user_id>/change-password", methods=["POST"])
@admin_required
def admin_change_user_password(user_id):
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password", "")
    confirm = data.get("new_password_confirm", "")

    if not new_password or len(new_password) < 6:
        return jsonify({"detail": "La password deve essere di almeno 6 caratteri"}), 400

    if new_password != confirm:
        return jsonify({"detail": "Le password non coincidono"}), 400

    with get_db() as db:
        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            return jsonify({"detail": "Utente non trovato"}), 404
        target.password_hash = hash_password(new_password)
        log_action(
            db=db,
            action="PASSWORD_CHANGE",
            entity_type="user",
            entity_id=target.id,
            description=f"Password cambiata da {g.current_user.nome} per {target.nome}",
        )
        db.commit()

    return jsonify({"message": "Password cambiata con successo"})


@auth_bp.route("/admin/<int:user_id>/change-email", methods=["POST"])
@admin_required
def admin_change_user_email(user_id):
    data = request.get_json(silent=True) or {}
    new_email = data.get("new_email", "").strip().lower()

    if not new_email:
        return jsonify({"detail": "Email richiesta"}), 400

    with get_db() as db:
        existing = (
            db.query(User).filter(User.email == new_email, User.id != user_id).first()
        )
        if existing:
            return jsonify({"detail": "Email già in uso"}), 400

        target = db.query(User).filter(User.id == user_id).first()
        if not target:
            return jsonify({"detail": "Utente non trovato"}), 404
        old_email = target.email
        target.email = new_email
        log_action(
            db=db,
            action="EMAIL_CHANGE",
            entity_type="user",
            entity_id=target.id,
            field="user.email",
            old_value=old_email,
            new_value=new_email,
            description=f"Email cambiata da {g.current_user.nome} per {target.nome}: {old_email} → {new_email}",
        )
        db.commit()

    return jsonify({"message": "Email cambiata con successo"})


@auth_bp.route("/admin/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"detail": "Utente non trovato"}), 404
        if user.id == g.current_user.id:
            return jsonify({"detail": "Non puoi eliminare te stesso"}), 400
        if user.ruolo == "superadmin":
            return jsonify({"detail": "Non puoi eliminare un superadmin"}), 403

        nome = user.nome
        email = user.email
        log_action(
            db=db,
            action="DELETE",
            entity_type="user",
            entity_id=user.id,
            field="user.deleted",
            new_value=f"{nome} ({email})",
            description=f"Eliminato: {nome} ({email})",
        )
        db.delete(user)
        db.commit()

    return jsonify({"message": f"Utente {nome} eliminato"}), 200


@auth_bp.route("/admin/tokens", methods=["GET"])
@admin_required
def admin_tokens_page():
    return render_template("admin/tokens.html", tokens=list(registration_tokens))
