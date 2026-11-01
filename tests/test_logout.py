def test_logout_clears_session_and_stays_logged_out(client, owner, csrf):
    response = client.delete("/logout", headers=csrf)
    assert response.status_code == 204
    assert response.data == b""
    with client.session_transaction() as session:
        assert "user_id" not in session and "csrf_token" not in session
    assert client.get("/check_session").status_code == 401
    assert client.get("/check_session").status_code == 401


def test_logout_requires_authentication(client):
    assert client.delete("/logout", headers={"Content-Type": "application/json"}).status_code == 401


def test_logout_rejects_missing_or_invalid_csrf(client, owner):
    for headers in ({"Content-Type": "application/json"},
                    {"Content-Type": "application/json", "X-CSRF-Token": "invalid"}):
        assert client.delete("/logout", headers=headers).status_code == 403
    assert client.get("/check_session").status_code == 200
