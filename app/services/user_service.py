from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.parent import Parent
from app.database.models.child import Child
from app.database.repositories.parent_repo import ParentRepository
from app.database.repositories.child_repo import ChildRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.parent_repo = ParentRepository(session)
        self.child_repo = ChildRepository(session)

    async def register_or_update_parent(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Parent:
        return await self.parent_repo.create_or_update(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )

    async def add_child(self, telegram_id: int, full_name: str, grade: str) -> Optional[Child]:
        parent = await self.parent_repo.get_by_telegram_id(telegram_id)
        if not parent:
            return None
        return await self.child_repo.create(
            parent_id=parent.id,
            full_name=full_name,
            grade=grade.strip().upper(),
        )

    async def get_parent_children(self, telegram_id: int) -> Sequence[Child]:
        parent = await self.parent_repo.get_by_telegram_id(telegram_id)
        if not parent:
            return []
        return await self.child_repo.get_by_parent_id(parent.id)

    async def remove_child(self, telegram_id: int, child_id: int) -> bool:
        parent = await self.parent_repo.get_by_telegram_id(telegram_id)
        if not parent:
            return False
        child = await self.child_repo.get_child_for_parent(child_id, parent.id)
        if not child:
            return False
        return await self.child_repo.soft_delete(child_id)

    async def get_children_by_telegram_id(self, telegram_id: int) -> list[Child]:
        """Fetches all children associated with a parent's Telegram ID."""
        stmt = (
            select(Child)
            .join(Parent, Child.parent_id == Parent.id)
            .where(Parent.telegram_id == telegram_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_child_by_id(self, child_id: int) -> Child | None:
        """Fetches a single child record by child primary key ID."""
        stmt = select(Child).where(Child.id == child_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_child(self, child_id: int, full_name: str, grade: str) -> Child | None:
        """Updates the full name and grade/class of an existing child."""
        child = await self.get_child_by_id(child_id)
        if not child:
            return None

        child.full_name = full_name
        child.grade = grade

        await self.session.commit()
        await self.session.refresh(child)
        return child

    async def delete_child(self, child_id: int) -> bool:
        """Deletes a child record and handles associated foreign key dependencies safely."""
        child = await self.get_child_by_id(child_id)
        if not child:
            return False

        # OPTION A: If you want to delete dependent pickup_requests first to prevent IntegrityError
        # (Make sure to import your PickupRequest model or use an appropriate delete query)
        from sqlalchemy import delete
        from app.database.models.pickup import PickupRequest  # Adjust import path as needed

        await self.session.execute(delete(PickupRequest).where(PickupRequest.child_id == child_id))

        # Now safe to delete the child
        await self.session.delete(child)
        await self.session.commit()
        return True