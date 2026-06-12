import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET"] = "test-jwt-secret"
os.environ["DEBUG"] = "true"

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token

from app import create_app
from app.database import Base, engine, get_db
from app.models import User


@pytest.fixture
def app() -> Flask:
    app = create_app({"TESTING": True})
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        yield app
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def db():
    with get_db() as session:
        yield session


def _create_user(
    email="test@example.com",
    nome="Test User",
    password_hash=None,
    ruolo="membro",
    attivo=1,
):
    from app.auth import hash_password

    with get_db() as db:
        user = User(
            nome=nome,
            email=email,
            password_hash=password_hash or hash_password("password123"),
            ruolo=ruolo,
            attivo=attivo,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture
def admin_user():
    return _create_user(email="admin@test.com", nome="Admin", ruolo="admin")


@pytest.fixture
def superadmin_user():
    return _create_user(
        email="superadmin@test.com", nome="SuperAdmin", ruolo="superadmin"
    )


@pytest.fixture
def normal_user():
    return _create_user(email="user@test.com", nome="User")


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(identity=str(admin_user.id))


@pytest.fixture
def superadmin_token(superadmin_user):
    return create_access_token(identity=str(superadmin_user.id))


@pytest.fixture
def user_token(normal_user):
    return create_access_token(identity=str(normal_user.id))


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
