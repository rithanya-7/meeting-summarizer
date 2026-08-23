from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    decisions = Column(Text, nullable=False)
    action_items = Column(Text, nullable=False)
    open_questions = Column(Text, nullable=False)
