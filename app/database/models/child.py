from typing import TYPE_CHECKING, List
from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, BigIntPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.parent import Parent
    from app.database.models.pickup import PickupRequest
    from app.database.models.teacher import Teacher


class Child(Base, BigIntPKMixin, TimestampMixin):
    __tablename__ = "children"

    parent_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relationships
    parent: Mapped["Parent"] = relationship("Parent", back_populates="children")
    pickup_requests: Mapped[List["PickupRequest"]] = relationship(
        "PickupRequest", back_populates="child"
    )

    # Foreign key link to Teacher
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    # Optional relationship attribute
    teacher = relationship("Teacher", back_populates="children")

    def __repr__(self) -> str:
        return f"<Child(id={self.id}, full_name='{self.full_name}', grade='{self.grade}')>"