from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Tag, TagType
from app.schemas.tags import TagCreate, TagUpdate

async def create_tag(db: AsyncSession, user_id: int, tag: TagCreate) -> Tag:
    # Verify tag_type exists and belongs to user if provided
    if tag.tag_type is not None:
        tag_type = await db.execute(
            select(TagType).filter(
                TagType.id == tag.tag_type,
                TagType.user_id == user_id
            )
        )
        if not tag_type.scalar_one_or_none():
            raise ValueError("Tag type not found or doesn't belong to user")

    db_tag = Tag(
        user_id=user_id,
        name=tag.name,
        color=tag.color,
        tag_type=tag.tag_type
    )
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def get_tag(db: AsyncSession, tag_id: int, user_id: int) -> Optional[Tag]:
    result = await db.execute(
        select(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def get_user_tags(db: AsyncSession, user_id: int) -> List[Tag]:
    result = await db.execute(
        select(Tag).filter(Tag.user_id == user_id)
    )
    return list(result.scalars().all())

async def update_tag(
    db: AsyncSession,
    tag_id: int,
    user_id: int,
    tag_update: TagUpdate
) -> Optional[Tag]:
    db_tag = await get_tag(db, tag_id, user_id)
    if not db_tag:
        return None

    # Verify tag_type exists and belongs to user if it's being updated
    if tag_update.tag_type is not None:
        tag_type = await db.execute(
            select(TagType).filter(
                TagType.id == tag_update.tag_type,
                TagType.user_id == user_id
            )
        )
        if not tag_type.scalar_one_or_none():
            raise ValueError("Tag type not found or doesn't belong to user")

    update_data = tag_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tag, field, value)

    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def delete_tag(db: AsyncSession, tag_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    )
    await db.commit()
    return result.rowcount > 0 