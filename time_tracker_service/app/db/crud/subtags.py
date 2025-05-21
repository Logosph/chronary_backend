from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Subtag, Tag
from app.schemas.subtags import SubtagCreate, SubtagUpdate

async def create_subtag(db: AsyncSession, user_id: int, subtag: SubtagCreate) -> Subtag:
    # Verify tag exists and belongs to user
    tag = await db.execute(
        select(Tag).filter(
            Tag.id == subtag.tag_id,
            Tag.user_id == user_id
        )
    )
    if not tag.scalar_one_or_none():
        raise ValueError("Tag not found or doesn't belong to user")

    db_subtag = Subtag(
        name=subtag.name,
        tag_id=subtag.tag_id
    )
    db.add(db_subtag)
    await db.commit()
    await db.refresh(db_subtag)
    return db_subtag

async def get_subtag(db: AsyncSession, subtag_id: int, user_id: int) -> Optional[Subtag]:
    result = await db.execute(
        select(Subtag)
        .join(Tag)
        .filter(
            Subtag.id == subtag_id,
            Tag.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

async def get_tag_subtags(db: AsyncSession, tag_id: int, user_id: int) -> List[Subtag]:
    result = await db.execute(
        select(Subtag)
        .join(Tag)
        .filter(
            Subtag.tag_id == tag_id,
            Tag.user_id == user_id
        )
    )
    return list(result.scalars().all())

async def update_subtag(
    db: AsyncSession,
    subtag_id: int,
    user_id: int,
    subtag_update: SubtagUpdate
) -> Optional[Subtag]:
    db_subtag = await get_subtag(db, subtag_id, user_id)
    if not db_subtag:
        return None

    db_subtag.name = subtag_update.name
    await db.commit()
    await db.refresh(db_subtag)
    return db_subtag

async def delete_subtag(db: AsyncSession, subtag_id: int, user_id: int) -> bool:
    # First verify the subtag belongs to the user's tag
    db_subtag = await get_subtag(db, subtag_id, user_id)
    if not db_subtag:
        return False

    await db.execute(
        delete(Subtag).filter(Subtag.id == subtag_id)
    )
    await db.commit()
    return True 