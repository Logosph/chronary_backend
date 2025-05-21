from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_vitals import get_async_db
from app.db.crud.activities import (
    create_activity,
    get_activity,
    get_user_activities,
    get_activities_after,
    get_activities_in_range,
    update_activity,
    close_activity,
    delete_activity,
    get_daily_stats,
    get_weekly_stats
)
from app.schemas.activities import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    TimeRange,
    DailyStats,
    WeeklyStats,
    ActivityStats
)
from app.routers.tag_types import get_current_user_id

router = APIRouter(prefix="/activities", tags=["activities"])

@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity_endpoint(
    activity: ActivityCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await create_activity(db, current_user_id, activity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[ActivityResponse])
async def get_activities(
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_user_activities(db, current_user_id)

@router.get("/after/{start_time}", response_model=List[ActivityResponse])
async def get_activities_after_endpoint(
    start_time: datetime,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_activities_after(db, current_user_id, start_time)

@router.get("/range", response_model=List[ActivityResponse])
async def get_activities_in_range_endpoint(
    time_range: TimeRange,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    return await get_activities_in_range(db, current_user_id, time_range.start, time_range.end)

@router.get("/stats", response_model=ActivityStats)
async def get_activity_stats(
    time_range: TimeRange,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        daily = await get_daily_stats(db, current_user_id, time_range.start, time_range.end)
        weekly = await get_weekly_stats(db, current_user_id, time_range.start, time_range.end)
        return {
            "daily": daily,
            "weekly": weekly
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity_endpoint(
    activity_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    activity = await get_activity(db, activity_id, current_user_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    return activity

@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity_endpoint(
    activity_id: int,
    activity_update: ActivityUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        activity = await update_activity(db, activity_id, current_user_id, activity_update)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        return activity
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{activity_id}/close", response_model=ActivityResponse)
async def close_activity_endpoint(
    activity_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        activity = await close_activity(db, activity_id, current_user_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        return activity
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity_endpoint(
    activity_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: int = Depends(get_current_user_id)
):
    deleted = await delete_activity(db, activity_id, current_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        ) 