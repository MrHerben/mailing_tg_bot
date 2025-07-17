import asyncio
from datetime import datetime
import html
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from db_manager import DatabaseManager
from mailing_system import MailingSystem
from states import MailingStates
from keyboards import build_keyboard_from_json, parse_keyboard_from_text
from reply_keyboards import *
from .common import show_main_menu

# --- Вспомогательная функция для отправки превью ---
async def send_preview(bot: AsyncTeleBot, message: Message):
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        text = data.get('text')
        if text: # Возвращаем экранированный HTML текст в просто HTML текст, иначе бот пришлёт без стилей
            text = html.unescape(text)


        media_file_id = data.get('media_file_id')
        media_type = data.get('media_type')
        keyboard_json = data.get('keyboard')
        
        markup = build_keyboard_from_json(keyboard_json)

        await bot.send_message(message.chat.id, "--- ПРЕВЬЮ ---", reply_markup=get_confirmation_keyboard())

        try:
            if media_file_id:
                if media_type == 'photo': await bot.send_photo(message.chat.id, media_file_id, caption=text, parse_mode='HTML', reply_markup=markup)
                elif media_type == 'video': await bot.send_video(message.chat.id, media_file_id, caption=text, parse_mode='HTML', reply_markup=markup)
                elif media_type == 'animation': await bot.send_animation(message.chat.id, media_file_id, caption=text, parse_mode='HTML', reply_markup=markup)
            elif text:
                await bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
            
            await bot.send_message(message.chat.id, "<b>Шаг 5/5: Подтверждение</b>\n\nВсе верно?", parse_mode='HTML', reply_markup=get_confirmation_keyboard())
        except Exception as e:
            await bot.send_message(message.chat.id, f"❗️ Ошибка при формировании превью: {e}\n\nПохоже, в HTML-разметке есть ошибка.")

# --- Основные обработчики ---
def register_moderator_handlers(bot: AsyncTeleBot, db: DatabaseManager, ms: MailingSystem):
    
    @bot.message_handler(func=lambda msg: msg.text == Buttons.cancel, state='*')
    async def cancel_dialog(message: Message):
        await bot.delete_state(message.from_user.id, message.chat.id)
        await show_main_menu(bot, message, db)

    @bot.message_handler(func=lambda msg: msg.text == Buttons.create_mailing, is_moderator=True)
    async def start_mailing(message: Message):
        await bot.delete_state(message.from_user.id, message.chat.id) 
        await bot.set_state(message.from_user.id, MailingStates.get_text, message.chat.id)
        await bot.reply_to(message, "<b>Шаг 1/5: Текст</b>\n\nОтправьте текст для рассылки. Поддерживаются HTML-теги для форматирования", reply_markup=get_cancel_keyboard(), parse_mode='HTML')

    @bot.message_handler(state=MailingStates.get_text, content_types=['text'])
    async def get_text(message: Message):
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['text'] = message.html_text
        await bot.set_state(message.from_user.id, MailingStates.get_media, message.chat.id)
        await bot.send_message(message.chat.id, "<b>Шаг 2/5: Медиа</b>\n\nОтправьте фото, видео или GIF. Если медиа не нужно, нажмите 'Без медиа'", reply_markup=get_skip_media_or_back_keyboard(), parse_mode='HTML')

    @bot.message_handler(state=MailingStates.get_media, content_types=['photo', 'video', 'animation', 'text'])
    async def get_media(message: Message):
        if message.text == Buttons.back:
            await bot.set_state(message.from_user.id, MailingStates.get_text, message.chat.id)
            await bot.reply_to(message, "<b>Шаг 1/5: Текст</b>\n\nОтправьте текст для рассылки. Поддерживаются HTML-теги для форматирования", reply_markup=get_cancel_keyboard(), parse_mode='HTML')
            return

        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if message.text == Buttons.skip_media: data['media_file_id'], data['media_type'] = None, None
            elif message.photo: data['media_file_id'], data['media_type'] = message.photo[-1].file_id, 'photo'
            elif message.video: data['media_file_id'], data['media_type'] = message.video.file_id, 'video'
            elif message.animation: data['media_file_id'], data['media_type'] = message.animation.file_id, 'animation'
            else:
                await bot.send_message(message.chat.id, "Пожалуйста, отправьте медиафайл или нажмите кнопку.")
                return
        
        await bot.set_state(message.from_user.id, MailingStates.get_keyboard, message.chat.id)
        await bot.reply_to(message, "<b>Шаг 3/5: Inline-кнопки</b>\n\nОтправьте разметку или нажмите 'Без кнопок'.\n"
                                     "Формат: <code>[Текст кнопки](url.com)</code>", reply_markup=get_skip_keyboard_or_back_keyboard(), parse_mode='HTML')

    @bot.message_handler(state=MailingStates.get_keyboard, content_types=['text'])
    async def get_mailing_keyboard(message: Message):
        if message.text == Buttons.back:
            await bot.set_state(message.from_user.id, MailingStates.get_media, message.chat.id)
            await bot.reply_to(message, "<b>Шаг 2/5: Медиа</b>\n\nОтправьте фото, видео или GIF. Если медиа не нужно, нажмите 'Без медиа'", reply_markup=get_skip_media_or_back_keyboard(), parse_mode='HTML')
            return
            
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if message.text == Buttons.skip_keyboard: data['keyboard'] = None
            else:
                keyboard_json = parse_keyboard_from_text(message.text)
                if not keyboard_json:
                    await bot.send_message(message.chat.id, "Неверный формат. Попробуйте снова или нажмите 'Без кнопок'.")
                    return
                data['keyboard'] = keyboard_json
            if not data.get('text') and not data.get('media_file_id'):
                await bot.send_message(message.chat.id, "❗️ Ошибка: Нельзя создать пустую рассылку.")
                await show_main_menu(bot, message, db)
                return
        
        await bot.set_state(message.from_user.id, MailingStates.get_schedule_time, message.chat.id)
        await bot.send_message(message.chat.id, "<b>Шаг 4/5: Время отправки</b>\n\nНажмите 'Отправить сейчас' или укажите дату (ГГГГ-ММ-ДД ЧЧ:ММ).", parse_mode='HTML', reply_markup=get_send_now_or_back_keyboard())

    @bot.message_handler(state=MailingStates.get_schedule_time, content_types=['text'])
    async def get_schedule_time(message: Message):
        if message.text == Buttons.back:
            await bot.set_state(message.from_user.id, MailingStates.get_keyboard, message.chat.id)
            await bot.reply_to(message, "<b>Шаг 3/5: Inline-кнопки</b>\n\nОтправьте разметку или нажмите 'Без кнопок'.\n"
                                         "Формат: <code>[Текст кнопки](url.com)</code>", reply_markup=get_skip_keyboard_or_back_keyboard(), parse_mode='HTML')
            return

        try:
            schedule_time = datetime.now() if message.text == Buttons.send_now else datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        except ValueError:
            await bot.send_message(message.chat.id, "Неверный формат даты. Попробуйте снова.")
            return

        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['schedule_time'] = schedule_time
        
        await bot.set_state(message.from_user.id, MailingStates.confirm, message.chat.id)
        await send_preview(bot, message)

    @bot.message_handler(state=MailingStates.confirm, content_types=['text'])
    async def confirm_mailing(message: Message):
        if message.text == Buttons.back:
            await bot.set_state(message.from_user.id, MailingStates.get_schedule_time, message.chat.id)
            await bot.reply_to(
                message, 
                "<b>Шаг 4/5: Время отправки</b>\n\nНажмите 'Отправить сейчас' или укажите дату (ГГГГ-ММ-ДД ЧЧ:ММ).", 
                reply_markup=get_send_now_or_back_keyboard(), parse_mode='HTML'
            )
            return
        
        if message.text == Buttons.confirm_send:
            async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                text, media, m_type, kbd, s_time = (data.get('text'), data.get('media_file_id'), data.get('media_type'), data.get('keyboard'), data.get('schedule_time'))
                mailing_id = await db.add_mailing(message.from_user.id, text, media, m_type, kbd, s_time)
                if s_time <= datetime.now():
                    await bot.send_message(message.chat.id, "Начинаю рассылку...")
                    asyncio.create_task(ms.process_mailing(mailing_id))
                else:
                    ms.schedule_new_mailing(mailing_id, s_time)
                    await bot.send_message(message.chat.id, f"Рассылка запланирована на {s_time.strftime('%Y-%m-%d %H:%M')}.")
            await show_main_menu(bot, message, db)
        else:
            await bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки: '✅ Отправить', '⬅️ Назад' или '❌ Отмена'.")