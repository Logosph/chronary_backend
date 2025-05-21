from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_vitals import get_async_db
from app.db.crud.tags import (
    create_tag,
    get_tag,
    get_user_tags,
    update_tag,
    delete_tag
)
from app.schemas.tags import TagCreate, TagUpdate, TagResponse
from app.routers.tag_types import get_current_user_id

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    tag: TagCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await create_tag(db, current_user_id, tag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[TagResponse])
async def get_tags(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_user_tags(db, current_user_id)

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag_endpoint(
    tag_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    tag = await get_tag(db, tag_id, current_user_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag_endpoint(
    tag_id: int,
    tag_update: TagUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        tag = await update_tag(db, tag_id, current_user_id, tag_update)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        return tag
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_endpoint(
    tag_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    deleted = await delete_tag(db, tag_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        ) 