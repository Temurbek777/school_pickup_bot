from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, Enum as SQLEnum, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, BigIntPKMixin, TimestampMixin
from app.database.models.enums import PickupStatus

if TYPE_CHECKING:
    from app.database.models.child import Child
    from app.database.models.parent import Parent


class PickupRequest(Base, BigIntPKMixin, TimestampMixin):
    __tablename__ = "pickup_requests"

    parent_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("parents.id", ondelete="RESTRICT"), nullable=False
    )
    child_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("children.id", ondelete="RESTRICT"), nullable=False
    )
    eta_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PickupStatus] = mapped_column(
        SQLEnum(PickupStatus, name="pickup_status"),
        default=PickupStatus.PENDING,
        nullable=False,
        index=True,
    )
    admin_group_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )

    # Relationships
    parent: Mapped["Parent"] = relationship("Parent", back_populates="pickup_requests")
    child: Mapped["Child"] = relationship("Child", back_populates="pickup_requests")

    __table_args__ = (
        # Enforces a maximum of 1 active pickup request per child
        Index(
            "idx_active_child_pickup",
            "child_id",
            unique=True,
            postgresql_where=(
                status.in_([
                    PickupStatus.PENDING,
                    PickupStatus.PREPARING,
                    PickupStatus.READY,
                ])
            ),
        ),
    )

    def __repr__(self) -> str:
        return f"<PickupRequest(id={self.id}, child_id={self.child_id}, status={self.status})>"