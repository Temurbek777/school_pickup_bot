from aiogram.fsm.state import State, StatesGroup


class EditChildSG(StatesGroup):
    waiting_for_name = State()
    waiting_for_grade = State()