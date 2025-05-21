from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.auth import UserCreate, UserResponse, Token as TokenSchema
from app.utils.auth import verify_password, create_token, verify_token
from app.db.db_vitals import get_async_db
from app.db.crud import (
    get_user_by_id,
    get_user_by_username,
    get_existing_user,
    create_user,
    create_token as create_db_token,
    revoke_token,
    revoke_all_user_tokens
)
from app.config.settings import settings

router = APIRouter(prefix="", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
    
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    user = await get_user_by_id(db, int(user_id))
    if not user:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    # Check if user exists
    if await get_existing_user(db, user_data.username, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    user = await create_user(db, user_data)
    
    # TODO: Send verification email
    return user

@router.post("/login", response_model=TokenSchema)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    # Find user
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_token(str(user.id), "access")
    refresh_token = create_token(str(user.id), "refresh")
    
    # Save refresh token in database
    await create_db_token(
        db,
        refresh_token,
        user.id,
        datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenSchema)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_async_db)
):
    # Verify refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Revoke old refresh token
    if not await revoke_token(db, refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired"
        )
    
    # Create new tokens
    user_id = payload.get("sub")
    new_access_token = create_token(user_id, "access")
    new_refresh_token = create_token(user_id, "refresh")
    
    # Save new refresh token
    await create_db_token(
        db,
        new_refresh_token,
        int(user_id),
        datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    # Revoke all refresh tokens for user
    await revoke_all_user_tokens(db, current_user.id)
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user 