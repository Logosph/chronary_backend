from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.db_vitals import Base
from datetime import datetime

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"))
    subtag_id = Column(Integer, ForeignKey("subtags.id"), nullable=True)
    name = Column(String)
    description = Column(String)
    start = Column(DateTime, default=datetime.utcnow)
    end = Column(DateTime, nullable=True)

    # Relationships
    tag = relationship("Tag", back_populates="activities")
    subtag = relationship("Subtag", back_populates="activities") 