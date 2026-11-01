from extensions import db


def test_anonymous_session_returns_401(client):
    assert client.get("/check_session").status_code == 401


def test_check_session_survives_repeated_requests(client, owner):
    for _ in range(2):
        response = client.get("/check_session")
        assert response.status_code == 200
        assert response.get_json() == {"id": owner[0].id, "username": "owner", "csrf_token": "test-csrf"}


def test_deleted_user_session_is_cleared(client, owner):
    db.session.delete(owner[0])
    db.session.commit()
    assert client.get("/check_session").status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_signup_cookie_is_accepted_on_refresh(client):
    signup = client.post("/signup", json={"username": "alice", "password": "password123"})
    response = client.get("/check_session")
    assert response.status_code == 200
    assert response.get_json() == signup.get_json()
