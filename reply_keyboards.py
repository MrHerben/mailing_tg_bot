from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

class Buttons:
    # Главное меню
    user_count = "📊 Кол-во пользователей"
    scheduled_mailings = "🗓 Запланированные рассылки"
    set_role = "👤 Назначить роль"
    create_mailing = "✍️ Создать рассылку"
    my_role = "ℹ️ Моя роль"
    
    # Кнопки навигации
    back = "⬅️ Назад"
    cancel = "❌ Отмена"

    # Кнопки диалога
    skip_media = "➡️ Без медиа"
    skip_keyboard = "➡️ Без кнопок"
    send_now = "🚀 Отправить сейчас"

    # Кнопки подтверждения
    confirm_send = "✅ Отправить"
    edit_mailing = "✏️ Редактировать"

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton(Buttons.create_mailing), KeyboardButton(Buttons.set_role),
        KeyboardButton(Buttons.user_count), KeyboardButton(Buttons.scheduled_mailings),
        KeyboardButton(Buttons.my_role)
    ]
    markup.add(*buttons)
    return markup

def get_moderator_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [KeyboardButton(Buttons.create_mailing), KeyboardButton(Buttons.my_role)]
    markup.add(*buttons)
    return markup
    
def get_user_keyboard():
    return ReplyKeyboardRemove()

def get_back_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton(Buttons.back))
    return markup

def get_cancel_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton(Buttons.cancel))
    return markup

def get_skip_media_or_back_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(Buttons.skip_media), KeyboardButton(Buttons.back))
    return markup

def get_skip_keyboard_or_back_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(Buttons.skip_keyboard), KeyboardButton(Buttons.back))
    return markup
    
def get_send_now_or_back_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton(Buttons.send_now), KeyboardButton(Buttons.back))
    return markup
    
def get_confirmation_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton(Buttons.confirm_send),
        KeyboardButton(Buttons.back),
        KeyboardButton(Buttons.cancel)
    )
    return markup