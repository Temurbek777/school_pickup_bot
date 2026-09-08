from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.parent import Parent
from app.database.repositories.base import BaseRepository


class ParentRepository(BaseRepository[Parent]):
    def __init__(self, session: AsyncSession):
        super().__init__(Parent, session)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Parent]:
        stmt = select(Parent).where(Parent.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Parent:
        parent = await self.get_by_telegram_id(telegram_id)
        if parent:
            parent.first_name = first_name
            parent.last_name = last_name
            parent.username = username
            parent.is_active = True
        else:
            parent = Parent(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            self.session.add(parent)
        await self.session.flush()
        await self.session.refresh(parent)
        return parent