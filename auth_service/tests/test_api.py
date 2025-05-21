import pytest
from httpx import AsyncClient
from app.config.settings import settings

API_PREFIX = settings.API_V1_STR

@pytest.mark.asyncio
async def test_register(async_client: AsyncClient, test_user_data):
    response = await async_client.post(
        f"{API_PREFIX}/auth/register",
        json=test_user_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "id" in data
    assert "password" not in data

@pytest.mark.asyncio
async def test_register_existing_user(async_client: AsyncClient, test_user_data):
    # Register user first time
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    
    # Try to register again with same data
    response = await async_client.post(
        f"{API_PREFIX}/auth/register",
        json=test_user_data
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login(async_client: AsyncClient, test_user_data):
    # Register user first
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    
    # Login
    response = await async_client.post(
        f"{API_PREFIX}/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_credentials(async_client: AsyncClient, test_user_data):
    # Register user first
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    
    # Try to login with wrong password
    response = await async_client.post(
        f"{API_PREFIX}/auth/login",
        data={
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, test_user_data):
    # Register and login user first
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    login_response = await async_client.post(
        f"{API_PREFIX}/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new tokens
    response = await async_client.post(
        f"{API_PREFIX}/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # Should get new refresh token

@pytest.mark.asyncio
async def test_me_endpoint(async_client: AsyncClient, test_user_data):
    # Register and login user first
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    login_response = await async_client.post(
        f"{API_PREFIX}/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Get user info
    response = await async_client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]

@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, test_user_data):
    # Register and login user first
    await async_client.post(f"{API_PREFIX}/auth/register", json=test_user_data)
    login_response = await async_client.post(
        f"{API_PREFIX}/auth/login",
        data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Logout
    response = await async_client.post(
        f"{API_PREFIX}/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Try to use the same access token
    response = await async_client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401 