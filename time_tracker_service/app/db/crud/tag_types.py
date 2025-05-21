from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import TagType
from app.schemas.tag_types import TagTypeCreate, TagTypeUpdate

async def create_tag_type(db: AsyncSession, user_id: int, tag_type: TagTypeCreate) -> TagType:
    db_tag_type = TagType(
        user_id=user_id,
        name=tag_type.name
    )
    db.add(db_tag_type)
    await db.commit()
    await db.refresh(db_tag_type)
    return db_tag_type

async def get_tag_type(db: AsyncSession, tag_type_id: int, user_id: int) -> Optional[TagType]:
    result = await db.execute(
        select(TagType).filter(
            TagType.id == tag_type_id,
            TagType.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def get_user_tag_types(db: AsyncSession, user_id: int) -> List[TagType]:
    result = await db.execute(
        select(TagType).filter(TagType.user_id == user_id)
    )
    return list(result.scalars().all())

async def update_tag_type(
    db: AsyncSession, 
    tag_type_id: int, 
    user_id: int, 
    tag_type_update: TagTypeUpdate
) -> Optional[TagType]:
    db_tag_type = await get_tag_type(db, tag_type_id, user_id)
    if db_tag_type:
        for field, value in tag_type_update.model_dump().items():
            setattr(db_tag_type, field, value)
        await db.commit()
        await db.refresh(db_tag_type)
    return db_tag_type

async def delete_tag_type(db: AsyncSession, tag_type_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(TagType).filter(
            TagType.id == tag_type_id,
            TagType.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0 