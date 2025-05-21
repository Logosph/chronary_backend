import pytest
from datetime import datetime, timedelta
from app.db.crud.user import create_user, get_user_by_username, get_user_by_email, get_existing_user
from app.db.crud.token import create_token, get_token, revoke_token, revoke_all_user_tokens
from app.schemas.auth import UserCreate

@pytest.mark.asyncio
async def test_create_user(test_db, test_user_data):
    user_in = UserCreate(**test_user_data)
    user = await create_user(test_db, user_in)
    
    assert user.email == test_user_data["email"]
    assert user.username == test_user_data["username"]
    assert user.hashed_password != test_user_data["password"]

@pytest.mark.asyncio
async def test_get_user_by_username(test_db, test_user_data):
    # Create user first
    user_in = UserCreate(**test_user_data)
    created_user = await create_user(test_db, user_in)
    
    # Test getting user by username
    user = await get_user_by_username(test_db, test_user_data["username"])
    assert user is not None
    assert user.id == created_user.id
    
    # Test with non-existent username
    user = await get_user_by_username(test_db, "nonexistent")
    assert user is None

@pytest.mark.asyncio
async def test_get_user_by_email(test_db, test_user_data):
    # Create user first
    user_in = UserCreate(**test_user_data)
    created_user = await create_user(test_db, user_in)
    
    # Test getting user by email
    user = await get_user_by_email(test_db, test_user_data["email"])
    assert user is not None
    assert user.id == created_user.id
    
    # Test with non-existent email
    user = await get_user_by_email(test_db, "nonexistent@example.com")
    assert user is None

@pytest.mark.asyncio
async def test_get_existing_user(test_db, test_user_data):
    # Create user first
    user_in = UserCreate(**test_user_data)
    created_user = await create_user(test_db, user_in)
    
    # Test with existing username
    user = await get_existing_user(test_db, test_user_data["username"], "other@example.com")
    assert user is not None
    assert user.id == created_user.id
    
    # Test with existing email
    user = await get_existing_user(test_db, "otherusername", test_user_data["email"])
    assert user is not None
    assert user.id == created_user.id
    
    # Test with non-existent user
    user = await get_existing_user(test_db, "nonexistent", "nonexistent@example.com")
    assert user is None

@pytest.mark.asyncio
async def test_token_operations(test_db, test_user_data):
    # Create user first
    user_in = UserCreate(**test_user_data)
    user = await create_user(test_db, user_in)
    
    # Create token
    token_str = "test_token"
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    token = await create_token(test_db, token_str, user.id, expires_at)
    
    assert token.token == token_str
    assert token.user_id == user.id
    
    # Get token
    retrieved_token = await get_token(test_db, token_str)
    assert retrieved_token is not None
    assert retrieved_token.id == token.id
    
    # Revoke token
    success = await revoke_token(test_db, token_str)
    assert success is True
    
    # Try to get revoked token
    revoked_token = await get_token(test_db, token_str)
    assert revoked_token is None
    
    # Create another token and test revoke_all_user_tokens
    another_token = await create_token(test_db, "another_token", user.id, expires_at)
    await revoke_all_user_tokens(test_db, user.id)
    
    # Try to get the second token after revoking all
    revoked_token = await get_token(test_db, another_token.token)
    assert revoked_token is None 