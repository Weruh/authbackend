from extensions import db
from models import Note


def test_show_owned_note(client, owner):
    note = Note(title="Private", content="Read me", user_id=owner[0].id)
    db.session.add(note)
    db.session.commit()
    response = client.get(f"/notes/{note.id}")
    assert response.status_code == 200
    assert response.get_json() == note.to_dict()


def test_other_users_note_and_missing_note_return_same_404(client, owner):
    note = Note(title="Secret", content="Hidden", user_id=owner[1].id)
    db.session.add(note)
    db.session.commit()
    foreign = client.get(f"/notes/{note.id}")
    missing = client.get("/notes/9999")
    assert foreign.status_code == missing.status_code == 404
    assert foreign.get_json() == missing.get_json() == {"error": "Note not found."}


def test_show_requires_authentication(client):
    assert client.get("/notes/1").status_code == 401
