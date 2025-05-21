from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.db_vitals import Base

class TagType(Base):
    __tablename__ = "tag_types"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    name = Column(String)

    # Relationship with tags
    tags = relationship("Tag", back_populates="tag_type", cascade="all, delete-orphan") 