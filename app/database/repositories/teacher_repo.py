# app/database/repositories/teacher_repo.py
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.models.teacher import Teacher
from app.utils.helpers import normalize_grade


class TeacherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Teacher | None:
        """Telegram ID bo'yicha o'qituvchini qidirish"""
        stmt = select(Teacher).where(Teacher.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_teacher(self, full_name: str, grade: str, telegram_id: int) -> Teacher:
        normalized = normalize_grade(grade)
        teacher = Teacher(
            full_name=full_name,
            grade=normalized,
            telegram_id=telegram_id,
        )
        self.session.add(teacher)
        await self.session.commit()
        await self.session.refresh(teacher)
        return teacher

    async def get_by_grade(self, grade: str) -> Teacher | None:
        normalized = normalize_grade(grade)
        stmt = select(Teacher).where(Teacher.grade == normalized)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, teacher_id: int) -> Teacher | None:
        stmt = select(Teacher).where(Teacher.id == teacher_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[Teacher]:
        stmt = select(Teacher).order_by(Teacher.grade)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_teacher(self, teacher_id: int, **kwargs) -> Teacher | None:
        teacher = await self.get_by_id(teacher_id)
        if not teacher:
            return None

        for key, value in kwargs.items():
            if key == "grade" and value:
                value = normalize_grade(value)
            setattr(teacher, key, value)

        await self.session.commit()
        await self.session.refresh(teacher)
        return teacher

    async def delete_teacher(self, teacher_id: int) -> bool:
        stmt = delete(Teacher).where(Teacher.id == teacher_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0