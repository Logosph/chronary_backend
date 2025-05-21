from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, delete, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Activity, Tag, Subtag, TagType
from app.schemas.activities import ActivityCreate, ActivityUpdate

async def verify_tag_and_subtag(db: AsyncSession, user_id: int, tag_id: int, subtag_id: Optional[int] = None) -> bool:
    # Verify tag exists and belongs to user
    tag = await db.execute(
        select(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    )
    if not tag.scalar_one_or_none():
        raise ValueError("Tag not found or doesn't belong to user")

    # If subtag is provided, verify it belongs to the tag
    if subtag_id is not None:
        subtag = await db.execute(
            select(Subtag).filter(
                Subtag.id == subtag_id,
                Subtag.tag_id == tag_id
            )
        )
        if not subtag.scalar_one_or_none():
            raise ValueError("Subtag not found or doesn't belong to the specified tag")
    
    return True

async def create_activity(db: AsyncSession, user_id: int, activity: ActivityCreate) -> Activity:
    # Verify tag and subtag
    await verify_tag_and_subtag(db, user_id, activity.tag_id, activity.subtag_id)

    db_activity = Activity(
        user_id=user_id,
        tag_id=activity.tag_id,
        subtag_id=activity.subtag_id,
        name=activity.name,
        description=activity.description,
        start=datetime.utcnow()
    )
    db.add(db_activity)
    await db.commit()
    await db.refresh(db_activity)
    return db_activity

async def get_activity(db: AsyncSession, activity_id: int, user_id: int) -> Optional[Activity]:
    result = await db.execute(
        select(Activity).filter(
            Activity.id == activity_id,
            Activity.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def get_user_activities(db: AsyncSession, user_id: int) -> List[Activity]:
    result = await db.execute(
        select(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.start.desc())
    )
    return list(result.scalars().all())

async def get_activities_after(db: AsyncSession, user_id: int, start_time: datetime) -> List[Activity]:
    result = await db.execute(
        select(Activity)
        .filter(
            Activity.user_id == user_id,
            Activity.start >= start_time
        )
        .order_by(Activity.start.desc())
    )
    return list(result.scalars().all())

async def get_activities_in_range(
    db: AsyncSession, 
    user_id: int, 
    start_time: datetime,
    end_time: datetime
) -> List[Activity]:
    result = await db.execute(
        select(Activity)
        .filter(
            Activity.user_id == user_id,
            Activity.start >= start_time,
            Activity.start <= end_time
        )
        .order_by(Activity.start.desc())
    )
    return list(result.scalars().all())

async def update_activity(
    db: AsyncSession,
    activity_id: int,
    user_id: int,
    activity_update: ActivityUpdate
) -> Optional[Activity]:
    db_activity = await get_activity(db, activity_id, user_id)
    if not db_activity:
        return None

    # If updating tag or subtag, verify they exist and are related
    if activity_update.tag_id is not None:
        new_tag_id = activity_update.tag_id
        new_subtag_id = activity_update.subtag_id if activity_update.subtag_id is not None else db_activity.subtag_id
        await verify_tag_and_subtag(db, user_id, new_tag_id, new_subtag_id)

    update_data = activity_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_activity, field, value)

    await db.commit()
    await db.refresh(db_activity)
    return db_activity

async def close_activity(db: AsyncSession, activity_id: int, user_id: int) -> Optional[Activity]:
    db_activity = await get_activity(db, activity_id, user_id)
    if not db_activity:
        return None

    if db_activity.end is not None:
        raise ValueError("Activity is already closed")

    db_activity.end = datetime.utcnow()
    await db.commit()
    await db.refresh(db_activity)
    return db_activity

async def delete_activity(db: AsyncSession, activity_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(Activity).filter(
            Activity.id == activity_id,
            Activity.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0

def calculate_duration_minutes(start: datetime, end: Optional[datetime], current_time: datetime) -> float:
    end_time = end if end is not None else current_time
    duration = end_time - start
    return duration.total_seconds() / 60

async def get_daily_stats(
    db: AsyncSession,
    user_id: int,
    start_time: datetime,
    end_time: datetime
) -> dict:
    # Get all relevant activities
    activities = await get_activities_in_range(db, user_id, start_time, end_time)
    current_time = datetime.utcnow()
    
    # Group activities by date and tag/subtag/tag_type
    daily_stats = {}
    for activity in activities:
        date = activity.start.date()
        if date not in daily_stats:
            daily_stats[date] = {
                'tags': {},
                'subtags': {},
                'tag_types': {}
            }
        
        duration = calculate_duration_minutes(activity.start, activity.end, current_time)
        
        # Aggregate by tag
        if activity.tag_id not in daily_stats[date]['tags']:
            daily_stats[date]['tags'][activity.tag_id] = {
                'duration': 0,
                'name': activity.tag.name
            }
        daily_stats[date]['tags'][activity.tag_id]['duration'] += duration
        
        # Aggregate by subtag if exists
        if activity.subtag_id:
            if activity.subtag_id not in daily_stats[date]['subtags']:
                daily_stats[date]['subtags'][activity.subtag_id] = {
                    'duration': 0,
                    'name': activity.subtag.name,
                    'tag_id': activity.tag_id
                }
            daily_stats[date]['subtags'][activity.subtag_id]['duration'] += duration
        
        # Aggregate by tag type if exists
        if activity.tag.tag_type:
            if activity.tag.tag_type not in daily_stats[date]['tag_types']:
                daily_stats[date]['tag_types'][activity.tag.tag_type] = {
                    'duration': 0,
                    'name': activity.tag.tag_type_rel.name
                }
            daily_stats[date]['tag_types'][activity.tag.tag_type]['duration'] += duration
    
    # Calculate averages
    result = {
        'by_tags': [],
        'by_subtags': [],
        'by_tag_types': []
    }
    
    # Process tags
    tag_totals = {}
    for date_stats in daily_stats.values():
        for tag_id, tag_data in date_stats['tags'].items():
            if tag_id not in tag_totals:
                tag_totals[tag_id] = {'total': 0, 'days': 0, 'name': tag_data['name']}
            tag_totals[tag_id]['total'] += tag_data['duration']
            tag_totals[tag_id]['days'] += 1
    
    for tag_id, data in tag_totals.items():
        result['by_tags'].append({
            'tag_id': tag_id,
            'tag_name': data['name'],
            'average_duration_minutes': data['total'] / data['days']
        })
    
    # Process subtags
    subtag_totals = {}
    for date_stats in daily_stats.values():
        for subtag_id, subtag_data in date_stats['subtags'].items():
            if subtag_id not in subtag_totals:
                subtag_totals[subtag_id] = {
                    'total': 0, 
                    'days': 0, 
                    'name': subtag_data['name'],
                    'tag_id': subtag_data['tag_id']
                }
            subtag_totals[subtag_id]['total'] += subtag_data['duration']
            subtag_totals[subtag_id]['days'] += 1
    
    for subtag_id, data in subtag_totals.items():
        result['by_subtags'].append({
            'subtag_id': subtag_id,
            'subtag_name': data['name'],
            'tag_id': data['tag_id'],
            'average_duration_minutes': data['total'] / data['days']
        })
    
    # Process tag types
    tag_type_totals = {}
    for date_stats in daily_stats.values():
        for tag_type_id, tag_type_data in date_stats['tag_types'].items():
            if tag_type_id not in tag_type_totals:
                tag_type_totals[tag_type_id] = {'total': 0, 'days': 0, 'name': tag_type_data['name']}
            tag_type_totals[tag_type_id]['total'] += tag_type_data['duration']
            tag_type_totals[tag_type_id]['days'] += 1
    
    for tag_type_id, data in tag_type_totals.items():
        result['by_tag_types'].append({
            'tag_type_id': tag_type_id,
            'tag_type_name': data['name'],
            'average_duration_minutes': data['total'] / data['days']
        })
    
    return result

async def get_weekly_stats(
    db: AsyncSession,
    user_id: int,
    start_time: datetime,
    end_time: datetime
) -> dict:
    # Adjust start_time to Monday of its week
    start_week = start_time - timedelta(days=start_time.weekday())
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Adjust end_time to Sunday of its week
    days_to_sunday = 6 - end_time.weekday()
    end_week = end_time + timedelta(days=days_to_sunday)
    end_week = end_week.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    if start_week >= end_week:
        raise ValueError("The time range must include at least one full week (Monday to Sunday)")
    
    # Get all activities for the adjusted time range
    activities = await get_activities_in_range(db, user_id, start_week, end_week)
    current_time = datetime.utcnow()
    
    # Group activities by week and tag/subtag/tag_type
    weekly_stats = {}
    for activity in activities:
        # Calculate the Monday of the activity's week
        week_start = activity.start - timedelta(days=activity.start.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if week_start not in weekly_stats:
            weekly_stats[week_start] = {
                'tags': {},
                'subtags': {},
                'tag_types': {}
            }
        
        duration = calculate_duration_minutes(activity.start, activity.end, current_time)
        
        # Aggregate by tag
        if activity.tag_id not in weekly_stats[week_start]['tags']:
            weekly_stats[week_start]['tags'][activity.tag_id] = {
                'duration': 0,
                'name': activity.tag.name
            }
        weekly_stats[week_start]['tags'][activity.tag_id]['duration'] += duration
        
        # Aggregate by subtag if exists
        if activity.subtag_id:
            if activity.subtag_id not in weekly_stats[week_start]['subtags']:
                weekly_stats[week_start]['subtags'][activity.subtag_id] = {
                    'duration': 0,
                    'name': activity.subtag.name,
                    'tag_id': activity.tag_id
                }
            weekly_stats[week_start]['subtags'][activity.subtag_id]['duration'] += duration
        
        # Aggregate by tag type if exists
        if activity.tag.tag_type:
            if activity.tag.tag_type not in weekly_stats[week_start]['tag_types']:
                weekly_stats[week_start]['tag_types'][activity.tag.tag_type] = {
                    'duration': 0,
                    'name': activity.tag.tag_type_rel.name
                }
            weekly_stats[week_start]['tag_types'][activity.tag.tag_type]['duration'] += duration
    
    # Calculate averages
    result = {
        'by_tags': [],
        'by_subtags': [],
        'by_tag_types': []
    }
    
    # Process tags
    tag_totals = {}
    for week_stats in weekly_stats.values():
        for tag_id, tag_data in week_stats['tags'].items():
            if tag_id not in tag_totals:
                tag_totals[tag_id] = {'total': 0, 'weeks': 0, 'name': tag_data['name']}
            tag_totals[tag_id]['total'] += tag_data['duration']
            tag_totals[tag_id]['weeks'] += 1
    
    for tag_id, data in tag_totals.items():
        result['by_tags'].append({
            'tag_id': tag_id,
            'tag_name': data['name'],
            'average_duration_minutes': data['total'] / data['weeks']
        })
    
    # Process subtags
    subtag_totals = {}
    for week_stats in weekly_stats.values():
        for subtag_id, subtag_data in week_stats['subtags'].items():
            if subtag_id not in subtag_totals:
                subtag_totals[subtag_id] = {
                    'total': 0, 
                    'weeks': 0, 
                    'name': subtag_data['name'],
                    'tag_id': subtag_data['tag_id']
                }
            subtag_totals[subtag_id]['total'] += subtag_data['duration']
            subtag_totals[subtag_id]['weeks'] += 1
    
    for subtag_id, data in subtag_totals.items():
        result['by_subtags'].append({
            'subtag_id': subtag_id,
            'subtag_name': data['name'],
            'tag_id': data['tag_id'],
            'average_duration_minutes': data['total'] / data['weeks']
        })
    
    # Process tag types
    tag_type_totals = {}
    for week_stats in weekly_stats.values():
        for tag_type_id, tag_type_data in week_stats['tag_types'].items():
            if tag_type_id not in tag_type_totals:
                tag_type_totals[tag_type_id] = {'total': 0, 'weeks': 0, 'name': tag_type_data['name']}
            tag_type_totals[tag_type_id]['total'] += tag_type_data['duration']
            tag_type_totals[tag_type_id]['weeks'] += 1
    
    for tag_type_id, data in tag_type_totals.items():
        result['by_tag_types'].append({
            'tag_type_id': tag_type_id,
            'tag_type_name': data['name'],
            'average_duration_minutes': data['total'] / data['weeks']
        })
    
    return result 