import pytest

from extensions import db
from models import Note


def test_create_note_assigns_session_owner(client, owner, csrf):
    response = client.post("/notes", json={"title": " My note ", "content": " My content "}, headers=csrf)
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "My note" and data["content"] == "My content"
    assert data["user_id"] == owner[0].id
    assert data["created_at"] and data["updated_at"]
    assert response.headers["Location"] == f'/notes/{data["id"]}'
    assert db.session.get(Note, data["id"]).user_id == owner[0].id


@pytest.mark.parametrize("payload", [
    {"title": "Title"}, {"content": "Content"}, {"title": " ", "content": "Content"},
    {"title": "Title", "content": None}, {"title": "T" * 121, "content": "Content"},
    {"title": "Title", "content": "C" * 10001},
    {"title": "Title", "content": "Content", "user_id": 2},
])
def test_invalid_note_or_owner_override_rejected(client, owner, csrf, payload):
    assert client.post("/notes", json=payload, headers=csrf).status_code == 422
    assert db.session.query(Note).count() == 0


def test_create_requires_authentication_and_csrf(app, client, owner):
    payload = {"title": "Title", "content": "Content"}
    assert app.test_client().post("/notes", json=payload).status_code == 401
    assert client.post("/notes", json=payload).status_code == 403
    assert db.session.query(Note).count() == 0
