from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_vitals import get_async_db
from app.db.crud.subtags import (
    create_subtag,
    get_subtag,
    get_tag_subtags,
    update_subtag,
    delete_subtag
)
from app.schemas.subtags import SubtagCreate, SubtagUpdate, SubtagResponse
from app.routers.tag_types import get_current_user_id

router = APIRouter(prefix="/subtags", tags=["subtags"])

@router.post("", response_model=SubtagResponse, status_code=status.HTTP_201_CREATED)
async def create_subtag_endpoint(
    subtag: SubtagCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await create_subtag(db, current_user_id, subtag)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/by-tag/{tag_id}", response_model=List[SubtagResponse])
async def get_subtags_by_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_tag_subtags(db, tag_id, current_user_id)

@router.get("/{subtag_id}", response_model=SubtagResponse)
async def get_subtag_endpoint(
    subtag_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    subtag = await get_subtag(db, subtag_id, current_user_id)
    if not subtag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtag not found"
        )
    return subtag

@router.put("/{subtag_id}", response_model=SubtagResponse)
async def update_subtag_endpoint(
    subtag_id: int,
    subtag_update: SubtagUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    subtag = await update_subtag(db, subtag_id, current_user_id, subtag_update)
    if not subtag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtag not found"
        )
    return subtag

@router.delete("/{subtag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtag_endpoint(
    subtag_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    deleted = await delete_subtag(db, subtag_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtag not found"
        ) 