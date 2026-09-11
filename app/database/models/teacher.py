from sqlalchemy import BigInteger, Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.models.base import Base  # Adjust import to your Base class location



class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    grade = Column(String(50), nullable=False, unique=True)  # e.g., "4-A"

    # Relationship to children
    children = relationship("Child", back_populates="teacher")