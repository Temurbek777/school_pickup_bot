from aiogram import Bot
from app.core.config import settings
from app.database.models.pickup import PickupRequest
from app.database.models.enums import PickupStatus
from app.bot.keyboards.admin_kb import get_admin_card_keyboard


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    def format_pickup_card(self, request: PickupRequest) -> str:
        status_badges = {
            PickupStatus.PENDING: "🚨 PENDING",
            PickupStatus.PREPARING: "🟡 PREPARING",
            PickupStatus.READY: "🟢 READY AT GATE",
            PickupStatus.COMPLETED: "🏁 COMPLETED",
            PickupStatus.CANCELLED: "❌ CANCELLED"
        }

        status_str = status_badges.get(request.status, str(request.status.value))
        parent_name = f"{request.parent.first_name} {request.parent.last_name or ''}".strip()
        time_str = request.created_at.strftime("%H:%M")

        return (
            f"<b>{status_str} Yangi Bildirishnoma!</b>\n\n"
            f"👦 <b>O'quvchi:</b> {request.child.full_name}\n"
            f"🎓 <b>Sinf:</b> {request.child.grade}\n"
            f"👨‍👩‍👧 <b>Ota ona:</b> {parent_name}\n"
            f"⏱️ <b>Kelish vaqti:</b> ~{request.eta_minutes} min\n\n"
            f"<i>Iltmos o'quvchini ogohlantiring!.</i>"
        )

    async def send_group_pickup_card(self, request: PickupRequest) -> int:
        text = self.format_pickup_card(request)
        kb = get_admin_card_keyboard(request.id, request.status)
        msg = await self.bot.send_message(
            chat_id=settings.ADMIN_GROUP_ID,
            text=text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        return msg.message_id

    async def update_group_pickup_card(self, request: PickupRequest):
        if not request.admin_group_message_id:
            return
        text = self.format_pickup_card(request)
        kb = None if request.status in [PickupStatus.COMPLETED, PickupStatus.CANCELLED] else get_admin_card_keyboard(
            request.id, request.status)

        try:
            await self.bot.edit_message_text(
                chat_id=settings.ADMIN_GROUP_ID,
                message_id=request.admin_group_message_id,
                text=text,
                reply_markup=kb,
                parse_mode="HTML"
            )
        except Exception:
            pass  # Fallback if message is unmodified or expired

    async def notify_parent_status_change(self, request: PickupRequest):
        if request.status == PickupStatus.READY:
            text = f"🟢 <b>{request.child.full_name}</b> ketishga tayyor!"
            await self.bot.send_message(chat_id=request.parent.telegram_id, text=text, parse_mode="HTML")
        elif request.status == PickupStatus.CANCELLED:
            text = f"❌ <b>{request.child.full_name}</b> uchun so'rov maktab tomonidan bekor qilindi."
            await self.bot.send_message(chat_id=request.parent.telegram_id, text=text, parse_mode="HTML")