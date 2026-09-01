"""
Phase 2 authentication + RBAC tests.

Covers (per docs/implementation-plan.md §37 and the Phase 2 task):
successful registration, duplicate email rejection, successful login,
invalid credentials, protected endpoint without/with JWT, and the
role-restricted endpoint with the correct/incorrect role.
"""

from fastapi.testclient import TestClient

AUTH = "/api/auth"
USERS = "/api/users"
PASSWORD = "Str0ngPass!x"


def register(
    client: TestClient,
    email: str = "io@example.com",
    username: str = "io_officer",
    role: str = "INVESTIGATING_OFFICER",
):
    return client.post(
        f"{AUTH}/register",
        json={
            "email": email,
            "username": username,
            "password": PASSWORD,
            "full_name": "Demo User",
            "role": role,
        },
    )


def login(client: TestClient, email: str, password: str = PASSWORD):
    return client.post(f"{AUTH}/login", json={"email": email, "password": password})


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Registration -------------------------------------------------------


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "io@example.com"
    assert data["username"] == "io_officer"
    assert data["role"]["name"] == "INVESTIGATING_OFFICER"
    assert data["is_active"] is True
    # The password hash must never be exposed.
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_rejected(client):
    assert register(client).status_code == 201
    duplicate = register(client, username="different_user")
    assert duplicate.status_code == 409


def test_register_duplicate_username_rejected(client):
    assert register(client).status_code == 201
    duplicate = register(client, email="other@example.com")
    assert duplicate.status_code == 409


def test_register_unknown_role_rejected(client):
    response = register(client, role="SUPERHERO")
    assert response.status_code == 400


# --- Login --------------------------------------------------------------


def test_login_success(client):
    register(client)
    response = login(client, "io@example.com")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "io@example.com"


def test_login_invalid_password(client):
    register(client)
    response = login(client, "io@example.com", password="definitely-wrong")
    assert response.status_code == 401
    # Generic message — does not reveal which part failed.
    assert response.json()["detail"] == "Incorrect email or password."


def test_login_unknown_email_same_generic_error(client):
    response = login(client, "ghost@example.com", password="whatever-pass")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


# --- Protected endpoints -------------------------------------------------


def test_protected_endpoint_without_jwt(client):
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_jwt(client):
    response = client.get(f"{AUTH}/me", headers=auth_headers("not-a-real-token"))
    assert response.status_code == 401


def test_protected_endpoint_with_valid_jwt(client):
    register(client)
    token = login(client, "io@example.com").json()["access_token"]
    response = client.get(f"{AUTH}/me", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "io@example.com"
    assert data["role"]["name"] == "INVESTIGATING_OFFICER"


def test_logout_without_jwt_rejected(client):
    response = client.post(f"{AUTH}/logout")
    assert response.status_code == 401


def test_logout_with_valid_jwt(client):
    register(client)
    token = login(client, "io@example.com").json()["access_token"]
    response = client.post(f"{AUTH}/logout", headers=auth_headers(token))
    assert response.status_code == 200


# --- RBAC (role-restricted endpoint: GET /api/users is ADMIN-only) --------


def test_role_restricted_allows_correct_role(client):
    register(client, email="admin@example.com", username="admin_user", role="ADMIN")
    token = login(client, "admin@example.com").json()["access_token"]
    response = client.get(USERS, headers=auth_headers(token))
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert any(u["username"] == "admin_user" for u in users)


def test_role_restricted_rejects_incorrect_role(client):
    register(client)  # INVESTIGATING_OFFICER
    token = login(client, "io@example.com").json()["access_token"]
    response = client.get(USERS, headers=auth_headers(token))
    assert response.status_code == 403


def test_role_restricted_rejects_unauthenticated(client):
    response = client.get(USERS)
    assert response.status_code == 401
