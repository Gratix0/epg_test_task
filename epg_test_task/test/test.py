import pytest
from fastapi.testclient import TestClient
from epg_test_task.src.main import app


# В идеале создать отдельную тестовую базу данных для проврок

client = TestClient(app)

@pytest.mark.asyncio
async def test_add_user():
    response = client.post(
        "/api/clients/create",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword",
            "gender": "male",
            "longitude": 12.34,
            "latitude": 56.78,
            "avatar": None
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "john.doe@example.com"

@pytest.mark.asyncio
async def test_login():
    response = client.post(
        "/api/clients/login",
        json={
            "email": "john.doe@example.com",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_match_user():
    # Сначала авторизуем пользователя
    login_response = client.post(
        "/api/clients/login",
        json={"email": "john.doe@example.com", "password": "securepassword"}
    )
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/clients/1/match",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_users():
    response = client.get("/api/clients/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

