from typing import Optional
from pydantic import BaseModel, Field

class TagBase(BaseModel):
    name: str
    color: str
    tag_type: Optional[int] = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    tag_type: Optional[int] = None

class TagInDB(TagBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class TagResponse(TagInDB):
    pass 