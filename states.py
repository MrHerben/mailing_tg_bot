from telebot.asyncio_handler_backends import State, StatesGroup

class MailingStates(StatesGroup):
    get_text = State()            # Шаг 1
    get_media = State()           # Шаг 2
    get_keyboard = State()        # Шаг 3
    get_schedule_time = State()   # Шаг 4
    confirm = State()             # Шаг 5

class AdminStates(StatesGroup):
    set_role = State()