from typing import Tuple, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.pickup import PickupRequest
from app.database.models.enums import PickupStatus
from app.database.repositories.parent_repo import ParentRepository
from app.database.repositories.child_repo import ChildRepository
from app.database.repositories.pickup_repo import PickupRepository


class PickupService:
    # State transitions table
    ALLOWED_TRANSITIONS = {
        PickupStatus.PENDING: [PickupStatus.PREPARING, PickupStatus.READY, PickupStatus.CANCELLED],
        PickupStatus.PREPARING: [PickupStatus.READY, PickupStatus.CANCELLED],
        PickupStatus.READY: [PickupStatus.COMPLETED, PickupStatus.CANCELLED],
        PickupStatus.COMPLETED: [],
        PickupStatus.CANCELLED: [],
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.parent_repo = ParentRepository(session)
        self.child_repo = ChildRepository(session)
        self.pickup_repo = PickupRepository(session)

    async def create_pickup_request(
            self, telegram_id: int, child_id: int, eta_minutes: int
    ) -> Tuple[Optional[PickupRequest], str]:
        """Creates a pickup request if child has no active pending/preparing/ready requests."""
        parent = await self.parent_repo.get_by_telegram_id(telegram_id)
        if not parent:
            return None, "User not registered."

        child = await self.child_repo.get_child_for_parent(child_id, parent.id)
        if not child:
            return None, "Child record not found."

        # Anti-spam: Check active requests
        existing = await self.pickup_repo.get_active_request_by_child(child.id)
        if existing:
            return None, f"{child.full_name} uchun so'rov yuborilgan ({existing.status.value})."

        request = await self.pickup_repo.create(
            parent_id=parent.id,
            child_id=child.id,
            eta_minutes=eta_minutes,
            status=PickupStatus.PENDING,
        )

        # Load relationships for notification rendering
        full_request = await self.pickup_repo.get_with_relations(request.id)
        return full_request, "Success"

    async def update_status(
            self, request_id: int, new_status: PickupStatus
    ) -> Tuple[Optional[PickupRequest], str]:
        request = await self.pickup_repo.get_with_relations(request_id)
        if not request:
            return None, "Pickup request not found."

        if new_status not in self.ALLOWED_TRANSITIONS.get(request.status, []):
            return None, f"Cannot transition from {request.status.value} to {new_status.value}."

        request.status = new_status
        await self.session.flush()
        return request, "Success"

    async def update_message_id(self, request_id: int, message_id: int) -> None:
        request = await self.pickup_repo.get_by_id(request_id)
        if request:
            request.admin_group_message_id = message_id
            await self.session.flush()

    async def get_active_parent_requests(self, telegram_id: int) -> Sequence[PickupRequest]:
        parent = await self.parent_repo.get_by_telegram_id(telegram_id)
        if not parent:
            return []
        return await self.pickup_repo.get_active_requests_by_parent(parent.id)