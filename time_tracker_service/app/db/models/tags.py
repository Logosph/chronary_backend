from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.db_vitals import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    name = Column(String)
    color = Column(String)
    tag_type = Column(Integer, ForeignKey("tag_types.id"))

    # Relationships
    tag_type_rel = relationship("TagType", back_populates="tags")
    subtags = relationship("Subtag", back_populates="tag", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="tag", cascade="all, delete-orphan") 