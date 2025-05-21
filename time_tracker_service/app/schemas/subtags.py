from pydantic import BaseModel

class SubtagBase(BaseModel):
    name: str
    tag_id: int

class SubtagCreate(SubtagBase):
    pass

class SubtagUpdate(BaseModel):
    name: str

class SubtagInDB(SubtagBase):
    id: int

    class Config:
        from_attributes = True

class SubtagResponse(SubtagInDB):
    pass 