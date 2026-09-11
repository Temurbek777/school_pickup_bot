from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models.enums import PickupStatus
from app.database.models.teacher import Teacher


def get_admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Adminlar uchun asosiy Reply tugmalar paneli."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ O'qituvchi qo'shish")],
            [KeyboardButton(text="📋 O'qituvchilar ro'yxati")]
        ],
        resize_keyboard=True
    )


def get_teachers_list_keyboard(teachers: list[Teacher]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in teachers:
        builder.button(
            text=f"🏫 {t.grade} - {t.full_name}",
            callback_data=f"teacher_view_{t.id}"
        )
    builder.adjust(1)
    return builder.as_markup()


def get_teacher_action_keyboard(teacher_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Tahrirlash", callback_data=f"teacher_edit_{teacher_id}")
    builder.button(text="🗑️ O'chirish", callback_data=f"teacher_delete_{teacher_id}")
    builder.button(text="⬅️ Ortga", callback_data="teacher_list_back")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_teacher_edit_fields_keyboard(teacher_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Ismi", callback_data=f"tch_editfield_{teacher_id}_name")
    builder.button(text="🏫 Sinfi", callback_data=f"tch_editfield_{teacher_id}_grade")
    builder.button(text="🆔 Telegram ID", callback_data=f"tch_editfield_{teacher_id}_tgid")
    builder.button(text="⬅️ Bekor qilish", callback_data=f"teacher_view_{teacher_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_admin_card_keyboard(request_id: int, current_status: PickupStatus) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_status == PickupStatus.PENDING:
        builder.button(text="🟡 O'quvchi tayyorlanmoqda", callback_data=f"adm_status_{request_id}_PREPARING")
        builder.button(text="🟢 O'quvchi tayyor", callback_data=f"adm_status_{request_id}_READY")
        builder.button(text="❌ Bekor qilish", callback_data=f"adm_status_{request_id}_CANCELLED")
        builder.adjust(2, 1)
    elif current_status == PickupStatus.PREPARING:
        builder.button(text="🟢 Tayyor", callback_data=f"adm_status_{request_id}_READY")
        builder.button(text="❌ Bekor qilish", callback_data=f"adm_status_{request_id}_CANCELLED")
        builder.adjust(1, 1)
    elif current_status == PickupStatus.READY:
        builder.button(text="🏁 Tugatish", callback_data=f"adm_status_{request_id}_COMPLETED")
        builder.adjust(1)

    return builder.as_markup()