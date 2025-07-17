
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from db_manager import DatabaseManager
import config

from reply_keyboards import (
    get_admin_keyboard, 
    get_moderator_keyboard, 
    get_user_keyboard,
    Buttons
)

async def show_main_menu(bot: AsyncTeleBot, message: Message, db: DatabaseManager):
    """
    Отправляет главное меню с клавиатурой в зависимости от роли.
    Удаляет предыдущее состояние, если оно было.
    """
    user_id = message.from_user.id
    
    await bot.delete_state(user_id, message.chat.id)
    
    user_role = await db.get_user_role(user_id)
    
    text = f"Роль: <b>{user_role.capitalize()}</b>\n\nВыберите действие:"
    
    keyboard = None
    if user_role == 'admin':
        keyboard = get_admin_keyboard()
    elif user_role == 'moderator':
        keyboard = get_moderator_keyboard()
    else: # user
        keyboard = get_user_keyboard()
        text = f"👋 Привет, {message.from_user.first_name}!\n\nВаша роль: <b>{user_role}</b>.\nВы будете получать рассылки от администрации и модераторов."

    await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode='HTML')


def register_common_handlers(bot: AsyncTeleBot, db: DatabaseManager):
    @bot.message_handler(commands=['start'])
    async def handle_start(message: Message):
        user = message.from_user
        await db.add_or_update_user(user.id, user.username, user.first_name)
        
        if config.ADMIN_ID and user.id == config.ADMIN_ID:
            current_role = await db.get_user_role(user.id)
            if current_role != 'admin':
                await db.set_user_role(user.id, 'admin')
                await bot.send_message(message.chat.id, "✨ Вам автоматически присвоены права Администратора из-за конфига!")

        await show_main_menu(bot, message, db)

    @bot.message_handler(func=lambda message: message.text == Buttons.my_role)
    async def handle_my_role(message: Message):
        await show_main_menu(bot, message, db)