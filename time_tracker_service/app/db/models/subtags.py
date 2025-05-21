from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.db_vitals import Base

class Subtag(Base):
    __tablename__ = "subtags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey("tags.id"))
    name = Column(String)

    # Relationships
    tag = relationship("Tag", back_populates="subtags")
    activities = relationship("Activity", back_populates="subtag", cascade="all, delete-orphan") 