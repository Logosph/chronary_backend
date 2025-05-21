from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_vitals import get_async_db
from app.db.crud.tag_types import (
    create_tag_type,
    get_tag_type,
    get_user_tag_types,
    update_tag_type,
    delete_tag_type
)
from app.schemas.tag_types import TagTypeCreate, TagTypeUpdate, TagTypeResponse
from app.utils.auth import verify_token
from app.config.settings import settings

router = APIRouter(prefix="/tag-types", tags=["tag-types"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
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
    
    return int(user_id)

@router.post("", response_model=TagTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_tag_type_endpoint(
    tag_type: TagTypeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await create_tag_type(db, current_user_id, tag_type)

@router.get("", response_model=List[TagTypeResponse])
async def get_tag_types(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_user_tag_types(db, current_user_id)

@router.get("/{tag_type_id}", response_model=TagTypeResponse)
async def get_tag_type_endpoint(
    tag_type_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    tag_type = await get_tag_type(db, tag_type_id, current_user_id)
    if not tag_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag type not found"
        )
    return tag_type

@router.put("/{tag_type_id}", response_model=TagTypeResponse)
async def update_tag_type_endpoint(
    tag_type_id: int,
    tag_type_update: TagTypeUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    tag_type = await update_tag_type(db, tag_type_id, current_user_id, tag_type_update)
    if not tag_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag type not found"
        )
    return tag_type

@router.delete("/{tag_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_type_endpoint(
    tag_type_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    deleted = await delete_tag_type(db, tag_type_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag type not found"
        ) 