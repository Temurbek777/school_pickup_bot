from aiogram import Router, F, types, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.bot.states.parent_states import AddChildSG
from app.bot.states.edit_states import EditChildSG
from app.bot.keyboards.parent_kb import get_children_menu_keyboard, get_main_menu_keyboard, build_children_select_keyboard
from app.bot.keyboards.admin_kb import get_admin_main_menu_keyboard
from app.database.repositories.child_repo import ChildRepository

from app.bot.states.teacher import AddTeacherSG
from app.database.repositories.teacher_repo import TeacherRepository

from app.bot.states.teacher import AddTeacherSG, EditTeacherSG
from app.database.repositories.teacher_repo import TeacherRepository
from app.bot.keyboards.admin_kb import (
    get_admin_main_menu_keyboard,
    get_teachers_list_keyboard,
    get_teacher_action_keyboard,
    get_teacher_edit_fields_keyboard
)
from app.utils.helpers import normalize_grade

from app.utils.texts import HELP_TEXT

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Xush kelibsiz!\n"
            "\n\n" + HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(F.text == "/teachers")
async def cmd_teachers(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ustozlar boshqaruvi bo'limi:", reply_markup=get_admin_main_menu_keyboard())


# ==================================== O'QITUVCHI QO'SHISH ====================================

@router.message(F.text == "➕ O'qituvchi qo'shish")
async def start_add_teacher(message: Message, state: FSMContext):
    await state.set_state(AddTeacherSG.waiting_for_full_name)
    await message.answer(
        "O'qituvchining ism-sharifini kiriting (masalan: *Aliyev Ali yoki Mr. Timur*):",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )


@router.message(AddTeacherSG.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AddTeacherSG.waiting_for_grade)
    await message.answer(
        "O'qituvchining biriktirilgan sinfini kiriting (masalan: *4-B* yoki *4B*):",
        parse_mode="Markdown"
    )


@router.message(AddTeacherSG.waiting_for_grade)
async def process_grade(message: Message, state: FSMContext):
    normalized = normalize_grade(message.text)
    await state.update_data(grade=normalized)
    await state.set_state(AddTeacherSG.waiting_for_telegram_id)

    await message.answer(
        f"Kiritilgan sinf standart ko'rinishga keltirildi: *{normalized}*\n\n"
        "O'qituvchining Telegram ID sini kiriting yoki uning xabarini botga forward (uzating) qiling:\n"
        "_(Eslatma: Telegram ID faqat raqamlardan iborat bo'lishi kerak)_",
        parse_mode="Markdown"
    )


@router.message(AddTeacherSG.waiting_for_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    telegram_id = None

    if message.forward_from:
        telegram_id = message.forward_from.id
    elif message.text and message.text.strip().isdigit():
        telegram_id = int(message.text.strip())

    # 1. Telegram ID raqami noto'g'ri bo'lsa
    if not telegram_id:
        await message.answer("⚠️ Bunday telegram ID mavjud emas")
        return

    # 2. Telegram tarmog'ida bunday foydalanuvchi bor-yo'qligini tekshirish
    try:
        await bot.get_chat(telegram_id)
    except TelegramBadRequest:
        await message.answer("⚠️ Bunday telegram ID mavjud emas")
        return
    except Exception:
        # Boshqa xatoliklar yuzaga kelsa ham ID mavjud emas deb hisoblaymiz
        await message.answer("⚠️ Bunday telegram ID mavjud emas")
        return

    # 3. Bazada ushbu Telegram ID bor-yo'qligini tekshirish
    teacher_repo = TeacherRepository(session)
    existing_teacher = await teacher_repo.get_by_telegram_id(telegram_id)

    if existing_teacher:
        await message.answer("⚠️ Bunday Telegram ID bilan o'qituvchi ro'yhatdan o'tgan")
        return

    # Barcha tekshiruvlardan o'tsa saqlaymiz
    data = await state.get_data()
    teacher = await teacher_repo.create_teacher(
        full_name=data["full_name"],
        grade=data["grade"],
        telegram_id=telegram_id
    )

    await state.clear()
    await message.answer(
        f"✅ *O'qituvchi muvaffaqiyatli ro'yxatga olindi!*\n\n"
        f"👤 *Ismi:* {teacher.full_name}\n"
        f"🏫 *Sinfi:* {teacher.grade}\n"
        f"🆔 *Telegram ID:* `{teacher.telegram_id}`",
        reply_markup=get_admin_main_menu_keyboard(),
        parse_mode="Markdown"
    )


# ==================================== RO'YXAT VA KO'RISH ====================================

@router.message(F.text == "📋 O'qituvchilar ro'yxati")
async def list_teachers(message: Message, session: AsyncSession):
    teacher_repo = TeacherRepository(session)
    teachers = await teacher_repo.get_all()

    if not teachers:
        await message.answer("⚠️ Hozircha hech qanday o'qituvchi ro'yxatga olinmagan.")
        return

    await message.answer(
        "📋 **O'qituvchilar ro'yxati:**\nBatafsil ma'lumot ko'rish uchun tanlang:",
        reply_markup=get_teachers_list_keyboard(teachers),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "teacher_list_back")
async def back_to_teachers_list(callback: CallbackQuery, session: AsyncSession):
    teacher_repo = TeacherRepository(session)
    teachers = await teacher_repo.get_all()
    await callback.message.edit_text(
        "📋 **O'qituvchilar ro'yxati:**\nBatafsil ma'lumot ko'rish uchun tanlang:",
        reply_markup=get_teachers_list_keyboard(teachers),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("teacher_view_"))
async def view_teacher_details(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    teacher_id = int(callback.data.split("_")[2])
    teacher_repo = TeacherRepository(session)
    teacher = await teacher_repo.get_by_id(teacher_id)

    if not teacher:
        await callback.answer("O'qituvchi topilmadi!", show_alert=True)
        return

    text = (
        f"👤 *O'qituvchi:* {teacher.full_name}\n"
        f"🏫 *Sinf:* {teacher.grade}\n"
        f"🆔 *Telegram ID:* `{teacher.telegram_id}`"
    )
    await callback.message.edit_text(text, reply_markup=get_teacher_action_keyboard(teacher.id), parse_mode="Markdown")


# ==================================== TAHRIRLASH ====================================

@router.callback_query(F.data.startswith("teacher_edit_"))
async def select_edit_field(callback: CallbackQuery):
    teacher_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        "Qaysi ma'lumotni tahrirlamoqchisiz?",
        reply_markup=get_teacher_edit_fields_keyboard(teacher_id)
    )


@router.callback_query(F.data.startswith("tch_editfield_"))
async def prompt_new_value(callback: CallbackQuery, state: FSMContext):
    _, _, teacher_id_str, field = callback.data.split("_")
    teacher_id = int(teacher_id_str)

    await state.update_data(edit_teacher_id=teacher_id, edit_field=field)
    await state.set_state(EditTeacherSG.waiting_for_new_value)

    field_names = {
        "name": "yangi ism-sharifini",
        "grade": "yangi sinfini (masalan: 4-B)",
        "tgid": "yangi Telegram ID sini"
    }
    await callback.message.answer(f"O'qituvchining {field_names.get(field, 'yangi qiymatini')} kiriting:")
    await callback.answer()


@router.message(EditTeacherSG.waiting_for_new_value)
async def process_edit_value(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    teacher_id = data["edit_teacher_id"]
    field = data["edit_field"]
    raw_val = message.text.strip()

    update_kwargs = {}
    if field == "name":
        update_kwargs["full_name"] = raw_val
    elif field == "grade":
        update_kwargs["grade"] = raw_val  # Repository avtomatik normalize qiladi
    elif field == "tgid":
        if raw_val.isdigit():
            update_kwargs["telegram_id"] = int(raw_val)
        else:
            await message.answer("⚠️ Telegram ID faqat raqamlardan iborat bo'lishi kerak!")
            return

    teacher_repo = TeacherRepository(session)
    updated_teacher = await teacher_repo.update_teacher(teacher_id, **update_kwargs)
    await state.clear()

    if updated_teacher:
        await message.answer(
            f"✅ *Ma'lumot muvaffaqiyatli yangilandi!*\n\n"
            f"👤 *Ismi:* {updated_teacher.full_name}\n"
            f"🏫 *Sinfi:* {updated_teacher.grade}\n"
            f"🆔 *Telegram ID:* `{updated_teacher.telegram_id}`",
            reply_markup=get_admin_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Tahrirlashda xatolik yuz berdi.", reply_markup=get_admin_main_menu_keyboard())


# ==================================== O'CHIRISH ====================================

@router.callback_query(F.data.startswith("teacher_delete_"))
async def delete_teacher(callback: CallbackQuery, session: AsyncSession):
    teacher_id = int(callback.data.split("_")[2])
    teacher_repo = TeacherRepository(session)
    success = await teacher_repo.delete_teacher(teacher_id)

    if success:
        await callback.answer("✅ O'qituvchi o'chirildi!", show_alert=True)
        # Ro'yxatni yangilash
        teachers = await teacher_repo.get_all()
        if teachers:
            await callback.message.edit_text(
                "📋 **O'qituvchilar ro'yxati:**",
                reply_markup=get_teachers_list_keyboard(teachers),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("⚠️ Ro'yxatda boshqa o'qituvchi qolmadi.")
    else:
        await callback.answer("❌ O'chirishda xatolik yuz berdi.", show_alert=True)


@router.message(F.text == "👨‍👩‍👧 Mening farzandim")
async def menu_children(message: Message, session: AsyncSession):
    user_service = UserService(session)
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
async def process_child_grade(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    full_name = data["full_name"]
    grade = message.text.strip()

    user_service = UserService(session)
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
async def show_edit_children_list(callback: CallbackQuery, session: AsyncSession):
    user_service = UserService(session)
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
async def process_edit_grade(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    child_id = data["editing_child_id"]
    full_name = data["full_name"]
    grade = message.text.strip()

    user_service = UserService(session)
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
async def show_delete_children_list(callback: CallbackQuery, session: AsyncSession):
    user_service = UserService(session)
    children = await user_service.get_children_by_telegram_id(callback.from_user.id)

    if not children:
        await callback.message.answer("⚠️ Sizda o'chirish uchun farzandlar mavjud emas.")
        await callback.answer()
        return

    kb = build_children_select_keyboard(children, action_prefix="select_delete")
    await callback.message.answer("🗑️ O'chirmoqchi bo'lgan farzandingizni tanlang:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("select_delete_"))
async def process_delete_child(callback: CallbackQuery, session: AsyncSession):
    child_id = int(callback.data.split("_")[2])

    user_service = UserService(session)
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
async def show_children_list(callback: CallbackQuery, session: AsyncSession):
    user_service = UserService(session)
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