from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.child import Child
from app.database.repositories.base import BaseRepository


class ChildRepository(BaseRepository[Child]):
    def __init__(self, session: AsyncSession):
        super().__init__(Child, session)

    async def get_by_parent_id(self, parent_id: int, active_only: bool = True) -> Sequence[Child]:
        stmt = select(Child).where(Child.parent_id == parent_id)
        if active_only:
            stmt = stmt.where(Child.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_child_for_parent(self, child_id: int, parent_id: int) -> Optional[Child]:
        stmt = select(Child).where(Child.id == child_id, Child.parent_id == parent_id, Child.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, child_id: int) -> bool:
        child = await self.get_by_id(child_id)
        if child:
            child.is_active = False
            await self.session.flush()
            return True
        return False

    @staticmethod
    async def get_child_by_id(db: AsyncSession, child_id: int) -> Child | None:
        result = await db.execute(select(Child).where(Child.id == child_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_child(db: AsyncSession, child_id: int, full_name: str, grade_class: str) -> Child | None:
        child = await ChildRepository.get_child_by_id(db, child_id)
        if child:
            child.full_name = full_name
            child.grade_class = grade_class
            await db.commit()
            await db.refresh(child)
        return child

    @staticmethod
    async def delete_child(db: AsyncSession, child_id: int) -> bool:
        child = await ChildRepository.get_child_by_id(db, child_id)
        if child:
            await db.delete(child)
            await db.commit()
            return True
        return False