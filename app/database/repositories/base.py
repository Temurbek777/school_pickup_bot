from typing import Generic, Type, TypeVar, Optional, List, Sequence
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id_val)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete_by_id(self, id_val: int) -> bool:
        stmt = delete(self.model).where(self.model.id == id_val)
        result = await self.session.execute(stmt)
        return result.rowcount > 0