from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.services.pickup_service import PickupService
from app.services.notification_service import NotificationService
from app.bot.states.parent_states import PickupSG
from app.bot.keyboards.parent_kb import get_eta_keyboard, get_confirm_pickup_keyboard, get_main_menu_keyboard
from app.database.repositories.teacher_repo import TeacherRepository
from app.database.repositories.child_repo import ChildRepository
from app.utils.texts import HELP_TEXT

router = Router()

@router.message(F.text == "🚗 Boryapman")
async def start_pickup_flow(message: Message, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    children = await user_service.get_parent_children(message.from_user.id)

    if not children:
        await message.answer(
            "⚠️ Siz hali birorta ham farzandni ro'yxatdan o'tkazmagansiz. Iltmos farzandingizni qo'shing '👨‍👩‍👧 Mening farzandim'.")
        return

    # Store children information in state for batch dispatch
    child_ids = [c.id for c in children]
    await state.update_data(child_ids=child_ids)
    await state.set_state(PickupSG.select_eta)

    names = ",\n ".join([f"<b>{c.full_name}</b> ({c.grade})" for c in children])
    await message.answer(
        f"🚗 Olib ketish uchun so'rov:\n{names}\n\n<b>Yetib kelish vaqtini tanlang:</b>",
        reply_markup=get_eta_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(PickupSG.select_eta, F.data.startswith("eta_"))
async def process_eta_selection(callback: CallbackQuery, state: FSMContext):
    eta = int(callback.data.split("_")[1])
    await state.update_data(eta=eta)
    await state.set_state(PickupSG.confirm)

    await callback.message.edit_text(
        f"⏱️ Siz <b>{eta} daqiqada</b> yetib kelish vaqtini tanladingiz.\nSo'rovni tasdiqlang!",
        reply_markup=get_confirm_pickup_keyboard(eta),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(PickupSG.confirm, F.data.startswith("confirm_pickup_"))
async def execute_batch_pickup(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    child_ids = data.get("child_ids", [])
    eta = int(callback.data.split("_")[2])

    pickup_service = PickupService(session)
    notification_service = NotificationService(bot)

    successful_requests = []
    errors = []

    # Process batch pick-up for all registered children
    for cid in child_ids:
        request, msg = await pickup_service.create_pickup_request(
            telegram_id=callback.from_user.id,
            child_id=cid,
            eta_minutes=eta
        )
        if request:
            message_id = await notification_service.send_group_pickup_card(request)
            await pickup_service.update_message_id(request.id, message_id)
            successful_requests.append(request)
        else:
            errors.append(msg)

    await state.clear()

    if successful_requests:
        summary = "\n".join([f"• <b>{r.child.full_name}</b>" for r in successful_requests])
        await callback.message.edit_text(
            f"✅ <b>Farzandingizni olib ketish so'rovi yuborildi!</b>\n\nFarzand:\n{summary}\n\n⏱️ Taxminiy kelish vaqti: {eta} daqiqa.",
            parse_mode="HTML"
        )

        # ==================== Notify Teachers for Each Child ====================
        teacher_repo = TeacherRepository(session)

        for req in successful_requests:
            # Fetch teacher associated with the child's grade
            teacher = await teacher_repo.get_by_grade(req.child.grade)
            print(req)
            if teacher and teacher.telegram_id:
                print(teacher.telegram_id)
                try:
                    await bot.send_message(
                        chat_id=teacher.telegram_id,
                        text=(
                            f"🔔 <b>O'quvchingizni olgani kelishmoqda!</b>\n\n"
                            f"👤 <b>O'quvchi:</b> {req.child.full_name}\n"
                            f"🏫 <b>Sinf:</b> {req.child.grade}\n"
                            f"⏱️ <b>Kelish vaqti:</b> {eta} daqiqa"
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Teacher notification error ({teacher.telegram_id}): {e}")
            else:
                print("No teacher")

        # await callback.answer("O'qituvchilarga va guruhga xabar yuborildi!", show_alert=True)

    else:
        error_msg = "\n".join(errors)
        await callback.message.edit_text(
            f"⚠️ <b>So'rov yuborishda xatolik yuz berdi:</b>\n{error_msg}",
            parse_mode="HTML"
        )
        await callback.answer()


@router.callback_query(F.data == "cancel_pickup")
async def cancel_pickup_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ So'rov bekor qilindi.")
    await callback.answer()


@router.message(F.text == "ℹ️ Yordam")
async def help_button_handler(message: Message, state: FSMContext):
    await message.answer(
        text=HELP_TEXT,
        parse_mode=ParseMode.HTML
    )
