# # app/bot/handlers/admin_teacher.py
# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
# from aiogram.fsm.context import FSMContext
# from sqlalchemy.ext.asyncio import AsyncSession
#
from app.bot.states.teacher import AddTeacherSG, EditTeacherSG
from app.database.repositories.teacher_repo import TeacherRepository
from app.bot.keyboards.admin_kb import (
    get_admin_main_menu_keyboard,
    get_teachers_list_keyboard,
    get_teacher_action_keyboard,
    get_teacher_edit_fields_keyboard
)
from app.utils.helpers import normalize_grade
#
# router = Router()


# @router.message(F.text == "/teachers")
# async def cmd_teachers(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("Ustozlar boshqaruvi bo'limi:", reply_markup=get_admin_main_menu_keyboard())
#
#
# # ==================================== O'QITUVCHI QO'SHISH ====================================
#
# # 1. Ro'yxatdan o'tkazishni boshlash
# @router.message(F.text == "➕ O'qituvchi qo'shish")
# async def start_add_teacher(message: Message, state: FSMContext):
#     await state.set_state(AddTeacherSG.waiting_for_full_name)
#     await message.answer(
#         "O'qituvchining to'liq ism-sharifini kiriting (masalan: *Alisher Navoiy*):",
#         reply_markup=ReplyKeyboardRemove(),
#         parse_mode="Markdown"
#     )
#
#
# # 2. Ismni qabul qilish -> Sinfni so'rash
# @router.message(AddTeacherSG.waiting_for_full_name)
# async def process_full_name(message: Message, state: FSMContext):
#     await state.update_data(full_name=message.text.strip())
#     await state.set_state(AddTeacherSG.waiting_for_grade)
#     await message.answer(
#         "O'qituvchining biriktirilgan sinfini kiriting (masalan: *4-B* yoki *4B*):",
#         parse_mode="Markdown"
#     )
#
#
# # 3. Sinfni qabul qilish -> Telegram ID ni so'rash
# @router.message(AddTeacherSG.waiting_for_grade)
# async def process_grade(message: Message, state: FSMContext):
#     normalized = normalize_grade(message.text)
#     await state.update_data(grade=normalized)
#     await state.set_state(AddTeacherSG.waiting_for_telegram_id)
#
#     await message.answer(
#         f"Kiritilgan sinf standart ko'rinishga keltirildi: *{normalized}*\n\n"
#         "O'qituvchining Telegram ID sini kiriting yoki uning xabarini botga forward (uzating) qiling:\n"
#         "_(Eslatma: Telegram ID faqat raqamlardan iborat bo'lishi kerak)_",
#         parse_mode="Markdown"
#     )
#
#
# # 4. Telegram ID ni qabul qilish -> Bazaga saqlash
# @router.message(AddTeacherSG.waiting_for_telegram_id)
# async def process_telegram_id(message: Message, state: FSMContext, session: AsyncSession):
#     telegram_id = None
#
#     if message.forward_from:
#         telegram_id = message.forward_from.id
#     elif message.text and message.text.strip().isdigit():
#         telegram_id = int(message.text.strip())
#
#     # Agar Telegram ID to'g'ri kiritilmagan bo'lsa
#     if not telegram_id:
#         await message.answer(
#             "⚠️ **Xatolik!** Iltimos, faqat to'g'ri Telegram ID raqamini kiriting yoki o'qituvchining xabarini botga forward qiling."
#         )
#         return
#
#     data = await state.get_data()
#     teacher_repo = TeacherRepository(session)
#     teacher = await teacher_repo.create_teacher(
#         full_name=data["full_name"],
#         grade=data["grade"],
#         telegram_id=telegram_id
#     )
#
#     await state.clear()
#     await message.answer(
#         f"✅ *O'qituvchi muvaffaqiyatli ro'yxatga olindi!*\n\n"
#         f"👤 *Ismi:* {teacher.full_name}\n"
#         f"🏫 *Sinfi:* {teacher.grade}\n"
#         f"🆔 *Telegram ID:* `{teacher.telegram_id}`",
#         reply_markup=get_admin_main_menu_keyboard(),
#         parse_mode="Markdown"
#     )
#
#
# # ==================================== RO'YXAT VA KO'RISH ====================================
#
# @router.message(F.text == "📋 O'qituvchilar ro'yxati")
# async def list_teachers(message: Message, session: AsyncSession):
#     teacher_repo = TeacherRepository(session)
#     teachers = await teacher_repo.get_all()
#
#     if not teachers:
#         await message.answer("⚠️ Hozircha hech qanday o'qituvchi ro'yxatga olinmagan.")
#         return
#
#     await message.answer(
#         "📋 **O'qituvchilar ro'yxati:**\nBatafsil ma'lumot ko'rish uchun tanlang:",
#         reply_markup=get_teachers_list_keyboard(teachers),
#         parse_mode="Markdown"
#     )
#
#
# @router.callback_query(F.data == "teacher_list_back")
# async def back_to_teachers_list(callback: CallbackQuery, session: AsyncSession):
#     teacher_repo = TeacherRepository(session)
#     teachers = await teacher_repo.get_all()
#     await callback.message.edit_text(
#         "📋 **O'qituvchilar ro'yxati:**\nBatafsil ma'lumot ko'rish uchun tanlang:",
#         reply_markup=get_teachers_list_keyboard(teachers),
#         parse_mode="Markdown"
#     )
#
#
# @router.callback_query(F.data.startswith("teacher_view_"))
# async def view_teacher_details(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
#     await state.clear()
#     teacher_id = int(callback.data.split("_")[2])
#     teacher_repo = TeacherRepository(session)
#     teacher = await teacher_repo.get_by_id(teacher_id)
#
#     if not teacher:
#         await callback.answer("O'qituvchi topilmadi!", show_alert=True)
#         return
#
#     text = (
#         f"👤 *O'qituvchi:* {teacher.full_name}\n"
#         f"🏫 *Sinf:* {teacher.grade}\n"
#         f"🆔 *Telegram ID:* `{teacher.telegram_id}`"
#     )
#     await callback.message.edit_text(text, reply_markup=get_teacher_action_keyboard(teacher.id), parse_mode="Markdown")
#
#
# # ==================================== TAHRIRLASH ====================================
#
# @router.callback_query(F.data.startswith("teacher_edit_"))
# async def select_edit_field(callback: CallbackQuery):
#     teacher_id = int(callback.data.split("_")[2])
#     await callback.message.edit_text(
#         "Qaysi ma'lumotni tahrirlamoqchisiz?",
#         reply_markup=get_teacher_edit_fields_keyboard(teacher_id)
#     )
#
#
# @router.callback_query(F.data.startswith("tch_editfield_"))
# async def prompt_new_value(callback: CallbackQuery, state: FSMContext):
#     _, _, teacher_id_str, field = callback.data.split("_")
#     teacher_id = int(teacher_id_str)
#
#     await state.update_data(edit_teacher_id=teacher_id, edit_field=field)
#     await state.set_state(EditTeacherSG.waiting_for_new_value)
#
#     field_names = {
#         "name": "yangi ism-sharifini",
#         "grade": "yangi sinfini (masalan: 4-B)",
#         "tgid": "yangi Telegram ID sini"
#     }
#     await callback.message.answer(f"O'qituvchining {field_names.get(field, 'yangi qiymatini')} kiriting:")
#     await callback.answer()
#
#
# @router.message(EditTeacherSG.waiting_for_new_value)
# async def process_edit_value(message: Message, state: FSMContext, session: AsyncSession):
#     data = await state.get_data()
#     teacher_id = data["edit_teacher_id"]
#     field = data["edit_field"]
#     raw_val = message.text.strip()
#
#     update_kwargs = {}
#     if field == "name":
#         update_kwargs["full_name"] = raw_val
#     elif field == "grade":
#         update_kwargs["grade"] = raw_val  # Repository avtomatik normalize qiladi
#     elif field == "tgid":
#         if raw_val.isdigit():
#             update_kwargs["telegram_id"] = int(raw_val)
#         else:
#             await message.answer("⚠️ Telegram ID faqat raqamlardan iborat bo'lishi kerak!")
#             return
#
#     teacher_repo = TeacherRepository(session)
#     updated_teacher = await teacher_repo.update_teacher(teacher_id, **update_kwargs)
#     await state.clear()
#
#     if updated_teacher:
#         await message.answer(
#             f"✅ *Ma'lumot muvaffaqiyatli yangilandi!*\n\n"
#             f"👤 *Ismi:* {updated_teacher.full_name}\n"
#             f"🏫 *Sinfi:* {updated_teacher.grade}\n"
#             f"🆔 *Telegram ID:* `{updated_teacher.telegram_id}`",
#             reply_markup=get_admin_main_menu_keyboard(),
#             parse_mode="Markdown"
#         )
#     else:
#         await message.answer("❌ Tahrirlashda xatolik yuz berdi.", reply_markup=get_admin_main_menu_keyboard())
#
#
# # ==================================== O'CHIRISH ====================================
#
# @router.callback_query(F.data.startswith("teacher_delete_"))
# async def delete_teacher(callback: CallbackQuery, session: AsyncSession):
#     teacher_id = int(callback.data.split("_")[2])
#     teacher_repo = TeacherRepository(session)
#     success = await teacher_repo.delete_teacher(teacher_id)
#
#     if success:
#         await callback.answer("✅ O'qituvchi o'chirildi!", show_alert=True)
#         # Ro'yxatni yangilash
#         teachers = await teacher_repo.get_all()
#         if teachers:
#             await callback.message.edit_text(
#                 "📋 **O'qituvchilar ro'yxati:**",
#                 reply_markup=get_teachers_list_keyboard(teachers),
#                 parse_mode="Markdown"
#             )
#         else:
#             await callback.message.edit_text("⚠️ Ro'yxatda boshqa o'qituvchi qolmadi.")
#     else:
#         await callback.answer("❌ O'chirishda xatolik yuz berdi.", show_alert=True)