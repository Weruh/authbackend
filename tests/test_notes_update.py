import pytest

from extensions import db
from models import Note


@pytest.fixture
def note(owner):
    record = Note(title="Original", content="Keep content", user_id=owner[0].id)
    db.session.add(record)
    db.session.commit()
    return record


def test_patch_supports_partial_updates(client, note, csrf):
    response = client.patch(f"/notes/{note.id}", json={"title": " Updated "}, headers=csrf)
    assert response.status_code == 200
    assert response.get_json()["title"] == "Updated"
    assert response.get_json()["content"] == "Keep content"
    response = client.patch(f"/notes/{note.id}", json={"content": "New content"}, headers=csrf)
    assert response.get_json()["title"] == "Updated"
    assert response.get_json()["content"] == "New content"


@pytest.mark.parametrize("payload", [{}, {"title": " "}, {"content": None}, {"user_id": 2}, {"id": 7}])
def test_invalid_update_does_not_change_record(client, note, csrf, payload):
    assert client.patch(f"/notes/{note.id}", json=payload, headers=csrf).status_code in (400, 422)
    db.session.refresh(note)
    assert note.title == "Original" and note.content == "Keep content"


def test_patch_cannot_modify_other_users_note(app, client, owner, csrf):
    note = Note(title="Secret", content="Private", user_id=owner[1].id)
    db.session.add(note)
    db.session.commit()
    payload = {"title": "Changed"}
    foreign = client.patch(f"/notes/{note.id}", json=payload, headers=csrf)
    missing = client.patch("/notes/9999", json=payload, headers=csrf)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.get_json() == missing.get_json()
    assert app.test_client().patch(f"/notes/{note.id}", json=payload).status_code == 401
    assert client.patch(f"/notes/{note.id}", json=payload).status_code == 403
    db.session.refresh(note)
    assert note.title == "Secret"
