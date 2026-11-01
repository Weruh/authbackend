import pytest

from app import create_app
from extensions import db
from models import Note, User


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "BCRYPT_LOG_ROUNDS": 4,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def owner(app, client):
    """Authenticate directly so each endpoint can be tested independently."""
    user = User(username="owner")
    user.password_hash = "password123"
    other = User(username="other")
    other.password_hash = "password123"
    db.session.add_all([user, other])
    db.session.commit()
    with client.session_transaction() as session:
        session["user_id"] = user.id
        session["csrf_token"] = "test-csrf"
    return user, other


@pytest.fixture
def csrf():
    return {"X-CSRF-Token": "test-csrf", "Content-Type": "application/json"}
