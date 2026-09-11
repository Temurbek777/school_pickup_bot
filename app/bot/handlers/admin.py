from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.pickup_service import PickupService
from app.services.notification_service import NotificationService
from app.database.models.enums import PickupStatus

router = Router()


@router.callback_query(F.data.startswith("adm_status_"))
async def process_admin_status_change(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split("_")
    request_id = int(parts[2])
    new_status = PickupStatus(parts[3])

    pickup_service = PickupService(session)
    notification_service = NotificationService(bot)

    updated_request, msg = await pickup_service.update_status(request_id, new_status)

    if updated_request:
        await notification_service.update_group_pickup_card(updated_request)
        await notification_service.notify_parent_status_change(updated_request)
        await callback.answer(f"Status updated to {new_status.value}")
    else:
        await callback.answer(f"Error: {msg}", show_alert=True)