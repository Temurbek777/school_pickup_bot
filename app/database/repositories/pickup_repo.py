from typing import Optional, Sequence
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.pickup import PickupRequest
from app.database.models.enums import PickupStatus
from app.database.repositories.base import BaseRepository


class PickupRepository(BaseRepository[PickupRequest]):
    def __init__(self, session: AsyncSession):
        super().__init__(PickupRequest, session)

    async def get_active_request_by_child(self, child_id: int) -> Optional[PickupRequest]:
        """Check if child already has an active pickup process."""
        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]
        stmt = (
            select(PickupRequest)
            .where(
                PickupRequest.child_id == child_id,
                PickupRequest.status.in_(active_statuses),
            )
            .options(selectinload(PickupRequest.child), selectinload(PickupRequest.parent))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_requests_by_parent(self, parent_id: int) -> Sequence[PickupRequest]:
        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]
        stmt = (
            select(PickupRequest)
            .where(
                PickupRequest.parent_id == parent_id,
                PickupRequest.status.in_(active_statuses),
            )
            .options(selectinload(PickupRequest.child))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_active_requests(self) -> Sequence[PickupRequest]:
        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]
        stmt = (
            select(PickupRequest)
            .where(PickupRequest.status.in_(active_statuses))
            .options(selectinload(PickupRequest.child), selectinload(PickupRequest.parent))
            .order_by(PickupRequest.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_relations(self, request_id: int) -> Optional[PickupRequest]:
        stmt = (
            select(PickupRequest)
            .where(PickupRequest.id == request_id)
            .options(selectinload(PickupRequest.child), selectinload(PickupRequest.parent))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()