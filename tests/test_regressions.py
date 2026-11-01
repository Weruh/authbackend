"""Boundary cases found during the completion review."""
import pytest

from extensions import db
from models import Note, User


@pytest.mark.parametrize("endpoint", ["/signup", "/login"])
@pytest.mark.parametrize("credentials", [
    {"username": "alice\n", "password": "password123"},
    {"username": "alice", "password": "\ud800password"},
    {"username": "alice", "password": "é" * 37},
])
def test_invalid_credentials_return_field_errors(client, endpoint, credentials):
    response = client.post(endpoint, json=credentials)
    assert response.status_code == 422
    assert "errors" in response.get_json()
    assert db.session.query(User).count() == 0


@pytest.mark.parametrize("field", ["title", "content"])
@pytest.mark.parametrize("method", ["post", "patch"])
def test_invalid_unicode_never_reaches_database(client, owner, csrf, field, method):
    note = Note(title="Original", content="Keep this", user_id=owner[0].id)
    db.session.add(note)
    db.session.commit()
    payload = {"title": "New", "content": "New content", field: "\udfff"}
    path = "/notes" if method == "post" else f"/notes/{note.id}"
    response = getattr(client, method)(path, json=payload, headers=csrf)
    assert response.status_code == 422
    assert field in response.get_json()["errors"]
    db.session.refresh(note)
    assert (note.title, note.content) == ("Original", "Keep this")
    assert db.session.query(Note).count() == 1
    # A rejected request must not poison subsequent writes.
    assert client.post("/notes", json={"title": "Valid", "content": "Still works"}, headers=csrf).status_code == 201


def test_unicode_password_byte_boundary_and_note_round_trip(client):
    signup = client.post("/signup", json={"username": "unicode_user", "password": "é" * 36})
    assert signup.status_code == 201
    csrf = {"X-CSRF-Token": signup.json["csrf_token"], "Content-Type": "application/json"}
    payload = {"title": "日本語", "content": "Café — a thought 🌍"}
    note = client.post("/notes", json=payload, headers=csrf)
    assert note.status_code == 201
    assert client.get(note.headers["Location"]).json["content"] == payload["content"]
    assert client.delete("/logout", headers=csrf).status_code == 204
    assert client.post("/login", json={"username": "unicode_user", "password": "é" * 36}).status_code == 200


@pytest.mark.parametrize("session_data", [
    {"user_id": 1},
    {"user_id": "invalid", "csrf_token": "token"},
    {"user_id": True, "csrf_token": "token"},
    {"user_id": 1, "csrf_token": 42},
    {"user_id": 1, "csrf_token": "\ud800"},
])
def test_incomplete_session_is_cleared(client, owner, session_data):
    with client.session_transaction() as session:
        session.clear()
        session.update(session_data)
    assert client.get("/check_session").status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


@pytest.mark.parametrize("token", [42, "\ud800", ""])
def test_invalid_session_csrf_token_rejects_writes(client, owner, csrf, token):
    with client.session_transaction() as session:
        session["csrf_token"] = token
    response = client.post("/notes", json={"title": "Test", "content": "Private"}, headers=csrf)
    assert response.status_code == 403
    assert db.session.query(Note).count() == 0


def test_method_errors_preserve_allow_header(client):
    response = client.put("/login", json={})
    assert response.status_code == 405
    assert "POST" in response.headers["Allow"]
    assert "error" in response.json


def test_cors_varies_for_all_origins_and_exposes_location(app, client):
    origin = "http://localhost:5173"
    app.config["FRONTEND_ORIGIN"] = origin
    for headers in ({}, {"Origin": origin}, {"Origin": "https://untrusted.example"}):
        response = client.get("/check_session", headers=headers)
        assert "Origin" in response.vary
    signup = client.post("/signup", json={"username": "alice", "password": "password123"}, headers={"Origin": origin})
    response = client.post("/notes", json={"title": "Test", "content": "Private"}, headers={
        "Origin": origin, "X-CSRF-Token": signup.json["csrf_token"],
    })
    assert response.status_code == 201
    assert response.headers["Access-Control-Expose-Headers"] == "Location"
    assert client.get(response.headers["Location"]).status_code == 200
