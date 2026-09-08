from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.models import Child

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚗 Boryapman")],
            [KeyboardButton(text="👨‍👩‍👧 Mening farzandlarim")],
            [KeyboardButton(text="ℹ️ Help")]
        ],
        resize_keyboard=True
    )

def get_children_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Farzand qo'shish", callback_data="child_add")
    builder.button(text="👁️ Farzandimni ko'rish", callback_data="child_list")
    builder.button(text="✏️ Tahrirlash", callback_data="child_edit_menu")
    builder.button(text="🗑️ O'chirish", callback_data="child_delete_menu")
    builder.adjust(2, 2)
    return builder.as_markup()


def build_children_select_keyboard(children: list[Child], action_prefix: str) -> InlineKeyboardMarkup:
    """Generates an inline list of children for selection (edit or delete)."""
    builder = InlineKeyboardBuilder()
    for child in children:
        builder.button(
            text=f"👤 {child.full_name} ({child.grade})",
            callback_data=f"{action_prefix}_{child.id}"
        )
    builder.button(text="⬅️ Bekor qilish", callback_data="cancel_child_action")
    builder.adjust(1)
    return builder.as_markup()


def get_eta_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    etas = [5, 10, 15, 20]
    for eta in etas:
        builder.button(text=f"⏱️ {eta} min", callback_data=f"eta_{eta}")
    builder.adjust(2, 2)
    return builder.as_markup()

def get_confirm_pickup_keyboard(eta: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlayman", callback_data=f"confirm_pickup_{eta}")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_pickup")
    builder.adjust(1, 1)
    return builder.as_markup()

