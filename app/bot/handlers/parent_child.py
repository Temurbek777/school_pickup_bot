from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.bot.states.parent_states import AddChildSG
from app.bot.states.edit_states import EditChildSG
from app.bot.keyboards.parent_kb import get_children_menu_keyboard, get_main_menu_keyboard, build_children_select_keyboard
from app.database.repositories.child_repo import ChildRepository

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Xush kelibsiz!\n"
            "Ushbu bot orqali farzandlaringizni maktabdan olib ketish haqida mas'ullarga xabar berishingiz mumkin.",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "👨‍👩‍👧 Mening farzandlarim")
async def menu_children(message: Message, db: AsyncSession):
    user_service = UserService(db)
    children = await user_service.get_parent_children(message.from_user.id)

    if not children:
        text = "⚠️Siz hali birorta ham farzandni ro'yxatdan o'tkazmagansiz. Qaytadan ro'yxatdan o'ting."
    else:
        child_list = "\n".join([f"• <b>{c.full_name}</b> — Sinf: {c.grade}" for c in children])
        text = f"<b>Ro'yhatdan o'tgan farzand:</b>\n\n{child_list}"

    await message.answer(text, reply_markup=get_children_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "child_add")
async def start_add_child(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddChildSG.waiting_for_name)
    await callback.message.answer("Farzandingizning Familiyasi va Ismini kiriting (masalan: Sardorov Ali):")
    await callback.answer()


@router.message(AddChildSG.waiting_for_name)
async def process_child_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AddChildSG.waiting_for_grade)
    await message.answer("Farzandingizning sinfini kiriting (masalan: 4-A, 4A):")


@router.message(AddChildSG.waiting_for_grade)
async def process_child_grade(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    full_name = data["full_name"]
    grade = message.text.strip()

    user_service = UserService(db)
    child = await user_service.add_child(
        telegram_id=message.from_user.id,
        full_name=full_name,
        grade=grade
    )
    await state.clear()

    if child:
        await message.answer(
            f"✅ <b>{child.full_name}</b> ({child.grade}) sinf muvaffaqiyatli qo'shildi!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Farzand qo'shishda xatolik. Iltmos boshqatdan urinib ko'ring")


# Cancel action handler
@router.callback_query(F.data == "cancel_child_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.answer()


# =====================================================================
# EDIT CHILD FLOW
# =====================================================================

@router.callback_query(F.data == "child_edit_menu")
async def show_edit_children_list(callback: CallbackQuery, db: AsyncSession):
    user_service = UserService(db)
    children = await user_service.get_children_by_telegram_id(callback.from_user.id)

    if not children:
        await callback.message.answer("⚠️ Sizda tahrirlash uchun farzandlar mavjud emas.")
        await callback.answer()
        return

    kb = build_children_select_keyboard(children, action_prefix="select_edit")
    await callback.message.answer("✏️ Tahrirlamoqchi bo'lgan farzandingizni tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("select_edit_"))
async def start_edit_child(callback: CallbackQuery, state: FSMContext):
    child_id = int(callback.data.split("_")[2])
    await state.update_data(editing_child_id=child_id)
    await state.set_state(EditChildSG.waiting_for_name)

    await callback.message.answer("Yangi Familiya va Ismni kiriting (masalan: Sardorov Ali):")
    await callback.answer()


@router.message(EditChildSG.waiting_for_name)
async def process_edit_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(EditChildSG.waiting_for_grade)
    await message.answer("Yangi sinfni kiriting (masalan: 4-A, 4A):")


@router.message(EditChildSG.waiting_for_grade)
async def process_edit_grade(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    child_id = data["editing_child_id"]
    full_name = data["full_name"]
    grade = message.text.strip()

    user_service = UserService(db)
    updated_child = await user_service.update_child(
        child_id=child_id,
        full_name=full_name,
        grade=grade
    )
    await state.clear()

    if updated_child:
        await message.answer(
            f"✅ Ma'lumotlar yangilandi:\n<b>{updated_child.full_name}</b> ({updated_child.grade})",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Tahrirlashda xatolik yuz berdi. Boshqatdan urinib ko'ring.")


# =====================================================================
# DELETE CHILD FLOW
# =====================================================================

@router.callback_query(F.data == "child_delete_menu")
async def show_delete_children_list(callback: CallbackQuery, db: AsyncSession):
    user_service = UserService(db)
    children = await user_service.get_children_by_telegram_id(callback.from_user.id)

    if not children:
        await callback.message.answer("⚠️ Sizda o'chirish uchun farzandlar mavjud emas.")
        await callback.answer()
        return

    kb = build_children_select_keyboard(children, action_prefix="select_delete")
    await callback.message.answer("🗑️ O'chirmoqchi bo'lgan farzandingizni tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("select_delete_"))
async def process_delete_child(callback: CallbackQuery, db: AsyncSession):
    child_id = int(callback.data.split("_")[2])

    user_service = UserService(db)
    success = await user_service.delete_child(child_id=child_id)

    if success:
        await callback.message.edit_text("✅ Farzand ma'lumotlari muvaffaqiyatli o'chirildi.")
    else:
        await callback.message.answer("❌ O'chirishda xatolik yuz berdi. Boshqatdan urinib ko'ring.")

    await callback.answer()


#==========================================================================================
# LIST CHILDREN
# =====================================================================
@router.callback_query(F.data == "child_list")
async def show_children_list(callback: CallbackQuery, db: AsyncSession):
    user_service = UserService(db)
    children = await user_service.get_children_by_telegram_id(callback.from_user.id)

    if not children:
        await callback.message.answer(
            "⚠️ <b>Sizda hali birorta ham farzand biriktirilmagan.</b>\n\n"
            "Farzand qo'shish uchun <b>➕ Farzand qo'shish</b> tugmasini bosing.",
            reply_markup=get_children_menu_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Build formatted text list of all children
    response_text = "<b>👶 Mening farzandlarim ro'yxati:</b>\n\n"
    for idx, child in enumerate(children, start=1):
        response_text += f"{idx}. 👤 <b>{child.full_name}</b> — 🏫 <i>{child.grade} sinf</i>\n"

    response_text += f"\nJami: <b>{len(children)} ta</b> farzand"

    await callback.message.answer(
        response_text,
        reply_markup=get_children_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()