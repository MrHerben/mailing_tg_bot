from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from db_manager import DatabaseManager
from states import AdminStates
from reply_keyboards import get_back_keyboard, Buttons
from .common import show_main_menu

def register_admin_handlers(bot: AsyncTeleBot, db: DatabaseManager):
    

    @bot.message_handler(func=lambda msg: msg.text == Buttons.user_count, is_admin=True)
    async def get_user_count(message: Message):
        count = await db.count_users()
        await bot.reply_to(message, f"👥 Всего пользователей в боте: <b>{count}</b>", parse_mode='HTML')


    @bot.message_handler(func=lambda msg: msg.text == Buttons.scheduled_mailings, is_admin=True)
    async def list_scheduled_mailings(message: Message):
        mailings = await db.get_scheduled_mailings()
        if not mailings:
            await bot.reply_to(message, "Нет запланированных рассылок.")
            return
        
        response = "<b>🗓 Запланированные рассылки:</b>\n\n"
        for m_id, creator, s_time, text_preview in mailings:
            response += f"<b>ID:</b> <code>{m_id}</code>\n"
            response += f"<b>Создатель:</b> <code>{creator}</code>\n"
            response += f"<b>Время:</b> {s_time.strftime('%Y-%m-%d %H:%M')}\n"
            response += f"<b>Текст:</b> <i>{text_preview}...</i>\n\n"
        
        await bot.reply_to(message, response, parse_mode='HTML')


    @bot.message_handler(func=lambda msg: msg.text == Buttons.set_role, is_admin=True)
    async def start_set_role(message: Message):
        await bot.set_state(message.from_user.id, AdminStates.set_role, message.chat.id)
        await bot.reply_to(message, 
            "Введите ID пользователя и роль (<code>user</code>, <code>moderator</code>, <code>admin</code>) через пробел.",
            reply_markup=get_back_keyboard(),
            parse_mode='HTML'
        )


    @bot.message_handler(state=AdminStates.set_role)
    async def process_set_role(message: Message):
        parts = message.text.split()
        if len(parts) != 2:
            await bot.reply_to(message, "❗️<b>Ошибка:</b> Неверный формат.\nПожалуйста, введите ID и роль через пробел.")
            return
        
        user_id_str, role = parts
        
        if not user_id_str.isdigit():
            await bot.reply_to(message, f"❗️<b>Ошибка:</b> ID пользователя (<code>{user_id_str}</code>) должен быть числом.", parse_mode='HTML')
            return
        
        user_id = int(user_id_str)
        allowed_roles = ['user', 'moderator', 'admin']
        if role not in allowed_roles:
            await bot.reply_to(message, f"❗️<b>Ошибка:</b> Неверная роль '<code>{role}</code>'.\nДоступные роли: {', '.join(allowed_roles)}.", parse_mode='HTML')
            return
            
        success = await db.set_user_role(user_id, role)
        
        if success:
            await bot.send_message(message.chat.id, f"✅ Роль для пользователя <code>{user_id}</code> успешно изменена на <b>{role}</b>.", parse_mode='HTML')
        else:
            await bot.send_message(message.chat.id, f"⚠️ Не удалось найти пользователя с ID <code>{user_id}</code>. Пользователь должен хотя бы раз запустить бота.", parse_mode='HTML')
            
        await show_main_menu(bot, message, db)