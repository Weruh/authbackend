from extensions import db
from models import Note


def test_delete_removes_owned_note(client, owner, csrf):
    note = Note(title="Remove", content="Delete me", user_id=owner[0].id)
    db.session.add(note)
    db.session.commit()
    note_id = note.id
    response = client.delete(f"/notes/{note_id}", headers=csrf)
    assert response.status_code == 204 and response.data == b""
    assert db.session.get(Note, note_id) is None
    assert client.get(f"/notes/{note_id}").status_code == 404
    assert client.delete(f"/notes/{note_id}", headers=csrf).status_code == 404


def test_delete_cannot_remove_other_users_note(client, owner, csrf):
    note = Note(title="Secret", content="Private", user_id=owner[1].id)
    db.session.add(note)
    db.session.commit()
    foreign = client.delete(f"/notes/{note.id}", headers=csrf)
    missing = client.delete("/notes/9999", headers=csrf)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.get_json() == missing.get_json()
    assert db.session.get(Note, note.id) is not None


def test_delete_requires_authentication_and_csrf(app, client, owner):
    note = Note(title="Keep", content="Private", user_id=owner[0].id)
    db.session.add(note)
    db.session.commit()
    headers = {"Content-Type": "application/json"}
    assert app.test_client().delete(f"/notes/{note.id}", headers=headers).status_code == 401
    assert client.delete(f"/notes/{note.id}", headers=headers).status_code == 403
    assert db.session.get(Note, note.id) is not None
