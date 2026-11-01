import pytest

from extensions import db
from models import Note


def test_notes_requires_authentication(client):
    assert client.get("/notes").status_code == 401


def test_notes_paginates_only_owned_records(client, owner):
    user, other = owner
    for i in range(12):
        db.session.add(Note(title=f"Note {i}", content="Private", user_id=user.id))
    db.session.add(Note(title="Other secret", content="Hidden", user_id=other.id))
    db.session.commit()
    first = client.get("/notes").get_json()
    assert first["total"] == 12 and first["pages"] == 2
    assert len(first["notes"]) == 10 and first["has_next"] and not first["has_prev"]
    assert all(n["user_id"] == user.id for n in first["notes"])
    second = client.get("/notes?page=2").get_json()
    assert len(second["notes"]) == 2 and not second["has_next"] and second["has_prev"]
    assert not ({n["id"] for n in first["notes"]} & {n["id"] for n in second["notes"]})
    assert client.get("/notes?per_page=5").get_json()["pages"] == 3
    assert client.get("/notes?page=99").get_json()["notes"] == []


def test_empty_notes_returns_empty_page(client, owner):
    data = client.get("/notes").get_json()
    assert data["notes"] == [] and data["total"] == 0 and data["pages"] == 0


@pytest.mark.parametrize("query", ["page=0", "page=-1", "page=abc", "per_page=101", "per_page=0", "page=1.5", "page=" , "page=99999999999"])
def test_invalid_pagination_returns_400(client, owner, query):
    assert client.get("/notes?" + query).status_code == 400
