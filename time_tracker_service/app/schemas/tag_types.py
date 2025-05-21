from pydantic import BaseModel

class TagTypeBase(BaseModel):
    name: str

class TagTypeCreate(TagTypeBase):
    pass

class TagTypeUpdate(TagTypeBase):
    pass

class TagTypeInDB(TagTypeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class TagTypeResponse(TagTypeInDB):
    pass 