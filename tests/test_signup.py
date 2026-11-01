import pytest

from extensions import db
from models import User


def test_signup_hashes_password_and_starts_session(client):
    response = client.post("/signup", json={"username": "alice", "password": "password123"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "alice"
    assert data["csrf_token"]
    assert "password" not in data and "password_hash" not in data
    user = db.session.get(User, data["id"])
    assert user.authenticate("password123")
    with client.session_transaction() as session:
        assert session["user_id"] == user.id
        assert session["csrf_token"] == data["csrf_token"]
        assert session.permanent
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie


def test_duplicate_signup_does_not_create_second_user(app, client):
    payload = {"username": "alice", "password": "password123"}
    assert client.post("/signup", json=payload).status_code == 201
    anonymous = app.test_client()
    assert anonymous.post("/signup", json=payload).status_code == 409
    assert db.session.query(User).count() == 1


@pytest.mark.parametrize("payload", [
    {}, [], {"username": "ab", "password": "password123"},
    {"username": "alice", "password": "short"},
    {"username": "alice", "password": "é" * 37},
    {"username": "alice", "password": "password123", "id": 20},
    {"username": None, "password": "password123"},
])
def test_invalid_signup_rejected(client, payload):
    assert client.post("/signup", json=payload).status_code in (400, 422)
    assert db.session.query(User).count() == 0


def test_signup_rejects_form_and_foreign_origin(client):
    assert client.post("/signup", data={"username": "alice"}).status_code == 415
    response = client.post("/signup", json={"username": "alice", "password": "password123"},
                           headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403
    assert db.session.query(User).count() == 0
