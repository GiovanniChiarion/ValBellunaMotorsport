from functools import wraps

import bcrypt as _bcrypt
from flask import abort, g
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    jwt_required as _jwt_required,
    verify_jwt_in_request,
)

from app.database import get_db
from app.models import User

jwt_manager = JWTManager()


@jwt_manager.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    with get_db() as db:
        user = db.query(User).filter(User.id == int(identity), User.attivo == 1).first()
        g.current_user = user
        return user


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def jwt_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        if g.current_user.ruolo not in ("admin", "superadmin"):
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def superadmin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        if g.current_user.ruolo != "superadmin":
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def optional_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                with get_db() as db:
                    g.current_user = (
                        db.query(User)
                        .filter(User.id == int(identity), User.attivo == 1)
                        .first()
                    )
            else:
                g.current_user = None
        except Exception:
            g.current_user = None
        return fn(*args, **kwargs)

    return wrapper
