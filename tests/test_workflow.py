def test_complete_authentication_and_private_notes_workflow(app):
    alice, bob = app.test_client(), app.test_client()
    signup = alice.post("/signup", json={"username": "alice", "password": "password123"})
    assert signup.status_code == 201
    alice_headers = {"X-CSRF-Token": signup.get_json()["csrf_token"], "Content-Type": "application/json"}
    bob_signup = bob.post("/signup", json={"username": "bob", "password": "password456"})
    assert bob_signup.status_code == 201
    bob_headers = {"X-CSRF-Token": bob_signup.get_json()["csrf_token"], "Content-Type": "application/json"}

    created = alice.post("/notes", json={"title": "Finish lab", "content": "Test the complete flow"}, headers=alice_headers)
    assert created.status_code == 201
    note_id = created.get_json()["id"]
    assert alice.get("/notes?per_page=1").get_json()["total"] == 1
    assert alice.get(f"/notes/{note_id}").get_json() == created.get_json()
    assert bob.get("/notes").get_json()["total"] == 0
    assert bob.get(f"/notes/{note_id}").status_code == 404
    assert bob.patch(f"/notes/{note_id}", json={"title": "Stolen"}, headers=bob_headers).status_code == 404
    assert bob.delete(f"/notes/{note_id}", headers=bob_headers).status_code == 404

    assert alice.delete("/logout", headers=alice_headers).status_code == 204
    assert alice.get("/check_session").status_code == 401
    assert alice.get("/notes").status_code == 401
    login = alice.post("/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200
    assert login.get_json()["csrf_token"] != alice_headers["X-CSRF-Token"]
    assert alice.get("/check_session").get_json() == login.get_json()
    assert alice.patch(f"/notes/{note_id}", json={"title": "Done"}, headers=alice_headers).status_code == 403
    alice_headers["X-CSRF-Token"] = login.get_json()["csrf_token"]
    updated = alice.patch(f"/notes/{note_id}", json={"title": "Done"}, headers=alice_headers)
    assert updated.status_code == 200 and updated.get_json()["title"] == "Done"
    assert alice.delete(f"/notes/{note_id}", headers=alice_headers).status_code == 204
    assert alice.get("/notes").get_json()["total"] == 0


def test_credentialed_cors_preflight_and_cookie_response(app, client):
    app.config["FRONTEND_ORIGIN"] = "http://localhost:5173"
    headers = {"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
               "Access-Control-Request-Headers": "Content-Type, X-CSRF-Token"}
    preflight = client.options("/notes", headers=headers)
    assert preflight.status_code == 200
    assert preflight.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert preflight.headers["Access-Control-Allow-Credentials"] == "true"
    assert "X-CSRF-Token" in preflight.headers["Access-Control-Allow-Headers"]
    response = client.post("/signup", json={"username": "alice", "password": "password123"}, headers=headers)
    assert response.status_code == 201
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert response.headers["Cache-Control"] == "no-store"
    rejected = client.get("/notes", headers={"Origin": "https://untrusted.example"})
    assert "Access-Control-Allow-Origin" not in rejected.headers
