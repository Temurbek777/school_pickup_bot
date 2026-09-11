from typing import Optional, Sequence
from datetime import datetime, time
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
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

    async def get_active_request_today(self, child_id: int) -> PickupRequest | None:
        """Faqat BUGUNGi faol so'rovni olish"""
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)

        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]

        stmt = select(PickupRequest).where(
            and_(
                PickupRequest.child_id == child_id,
                PickupRequest.status.in_(active_statuses),
                PickupRequest.created_at >= today_start,
                PickupRequest.created_at <= today_end
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def expire_old_unhandled_requests(self, child_id: int):
        """Kechadan yoki o'tgan kunlardan qolib ketgan so'rovlarni EXPIRED qilish"""
        today_start = datetime.combine(datetime.now().date(), time.min)
        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]

        stmt = (
            update(PickupRequest)
            .where(
                and_(
                    PickupRequest.child_id == child_id,
                    PickupRequest.status.in_(active_statuses),
                    PickupRequest.created_at < today_start  # Bugungi kundan oldingi so'rovlar
                )
            )
            .values(status=PickupStatus.EXPIRED)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_active_request_today_by_child(self, child_id: int) -> Optional[PickupRequest]:
        """Faqat BUGUN yaratilgan va hali faol bo'lgan so'rovni qaytaradi."""
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)

        active_statuses = [PickupStatus.PENDING, PickupStatus.PREPARING, PickupStatus.READY]

        stmt = select(PickupRequest).where(
            and_(
                PickupRequest.child_id == child_id,
                PickupRequest.status.in_(active_statuses),
                PickupRequest.created_at >= today_start,
                PickupRequest.created_at <= today_end
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()