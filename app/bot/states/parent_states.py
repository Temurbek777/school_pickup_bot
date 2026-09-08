from aiogram.fsm.state import State, StatesGroup

class AddChildSG(StatesGroup):
    waiting_for_name = State()
    waiting_for_grade = State()
    confirm = State()

class PickupSG(StatesGroup):
    select_eta = State()
    confirm = State()