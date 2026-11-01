import pytest


def test_login_starts_session(app, client, owner):
    anonymous = app.test_client()
    response = anonymous.post("/login", json={"username": "owner", "password": "password123"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == owner[0].id
    assert set(data) == {"id", "username", "csrf_token"}
    with anonymous.session_transaction() as session:
        assert session["user_id"] == owner[0].id
        assert session["csrf_token"] == data["csrf_token"]


@pytest.mark.parametrize("username,password", [("owner", "wrongpass"), ("absent", "password123")])
def test_login_failure_is_generic_and_does_not_authenticate(app, owner, username, password):
    anonymous = app.test_client()
    response = anonymous.post("/login", json={"username": username, "password": password})
    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid username or password."}
    with anonymous.session_transaction() as session:
        assert "user_id" not in session


def test_login_rotates_existing_session(client, owner, csrf):
    response = client.post("/login", json={"username": "other", "password": "password123"}, headers=csrf)
    assert response.status_code == 200
    assert response.get_json()["csrf_token"] != "test-csrf"
    with client.session_transaction() as session:
        assert session["user_id"] == owner[1].id


def test_login_checks_csrf(client, owner):
    assert client.post("/login", json={"username": "owner", "password": "password123"}).status_code == 403
