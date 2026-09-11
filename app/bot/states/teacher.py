# app/bot/states/teacher.py
from aiogram.fsm.state import State, StatesGroup


class AddTeacherSG(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_grade = State()
    waiting_for_telegram_id = State()

class EditTeacherSG(StatesGroup):
    waiting_for_new_value = State()