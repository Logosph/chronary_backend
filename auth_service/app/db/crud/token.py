from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.token import Token

async def get_token(db: AsyncSession, token: str) -> Optional[Token]:
    result = await db.execute(
        select(Token).filter(
            Token.token == token,
            Token.is_revoked == False,
            Token.expires_at > datetime.utcnow()
        )
    )
    return result.scalar_one_or_none()

async def create_token(db: AsyncSession, token: str, user_id: int, expires_at: datetime) -> Token:
    db_token = Token(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token

async def revoke_token(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        select(Token).filter(Token.token == token)
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        await db.commit()
        return True
    return False

async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    stmt = (
        update(Token)
        .where(Token.user_id == user_id, Token.is_revoked == False)
        .values(is_revoked=True)
    )
    await db.execute(stmt)
    await db.commit() 