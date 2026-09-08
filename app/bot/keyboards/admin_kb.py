from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models.enums import PickupStatus


def get_admin_card_keyboard(request_id: int, current_status: PickupStatus) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_status == PickupStatus.PENDING:
        builder.button(text="🟡 Mark Preparing", callback_data=f"adm_status_{request_id}_PREPARING")
        builder.button(text="🟢 Mark Ready", callback_data=f"adm_status_{request_id}_READY")
        builder.button(text="❌ Cancel", callback_data=f"adm_status_{request_id}_CANCELLED")
        builder.adjust(2, 1)
    elif current_status == PickupStatus.PREPARING:
        builder.button(text="🟢 Mark Ready", callback_data=f"adm_status_{request_id}_READY")
        builder.button(text="❌ Cancel", callback_data=f"adm_status_{request_id}_CANCELLED")
        builder.adjust(1, 1)
    elif current_status == PickupStatus.READY:
        builder.button(text="🏁 Mark Completed", callback_data=f"adm_status_{request_id}_COMPLETED")
        builder.adjust(1)

    return builder.as_markup()