from typing import TYPE_CHECKING, List
from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, BigIntPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.child import Child
    from app.database.models.pickup import PickupRequest


class Parent(Base, BigIntPKMixin, TimestampMixin):
    __tablename__ = "parents"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relationships
    children: Mapped[List["Child"]] = relationship(
        "Child", back_populates="parent", cascade="all, delete-orphan"
    )
    pickup_requests: Mapped[List["PickupRequest"]] = relationship(
        "PickupRequest", back_populates="parent"
    )

    def __repr__(self) -> str:
        return f"<Parent(id={self.id}, telegram_id={self.telegram_id}, name='{self.first_name}')>"