import asyncio
import time
import html
from telebot.async_telebot import AsyncTeleBot
from telebot.apihelper import ApiTelegramException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from db_manager import DatabaseManager
from keyboards import build_keyboard_from_json

def split_text(text: str, limit: int):
    if not text:
        return []
    return [text[i:i + limit] for i in range(0, len(text), limit)]

class MailingSystem:
    def __init__(self, bot: AsyncTeleBot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    def start(self):
        self.scheduler.start()
        print("Scheduler started.")

    async def schedule_all_pending(self):
        mailings = await self.db.get_scheduled_mailings()
        now = datetime.now(self.scheduler.timezone)
        for mailing in mailings:
            mailing_id, _, scheduled_time, _ = mailing
            if scheduled_time > now:
                self.scheduler.add_job(
                    self.process_mailing,
                    trigger=DateTrigger(run_date=scheduled_time),
                    id=f'mailing_{mailing_id}',
                    args=[mailing_id],
                    replace_existing=True
                )
        if mailings:
            print(f"Scheduled {len(mailings)} pending mailings from DB.")

    def schedule_new_mailing(self, mailing_id: int, schedule_time: datetime):
        self.scheduler.add_job(
            self.process_mailing,
            trigger=DateTrigger(run_date=schedule_time),
            id=f'mailing_{mailing_id}',
            args=[mailing_id],
            replace_existing=True
        )

    async def process_mailing(self, mailing_id: int):
        await self.db.update_mailing_status(mailing_id, 'in_progress')

        query = "SELECT creator_id, text, media_file_id, media_type, keyboard FROM mailings WHERE id = %s"
        mailing_data = await self.db.execute(query, (mailing_id,), fetch='one')
        if not mailing_data:
            await self.db.update_mailing_status(mailing_id, 'failed')
            return

        creator_id, text, media_file_id, media_type, keyboard_json = mailing_data

        if text: # Возвращаем экранированный HTML текст в просто HTML текст, иначе бот пришлёт без стилей
            text = html.unescape(text)
        

        markup = build_keyboard_from_json(keyboard_json)
        
        limit = 1024 if media_file_id else 4096
        text_parts = split_text(text, limit)
        
        user_ids = await self.db.get_all_user_ids()
        start_time = time.time()
        delivered_count, failed_count = 0, 0

        for user_id in user_ids:
            try:
                first_part_sent = False
                if media_file_id:
                    caption = text_parts[0] if text_parts else ""
                    if media_type == 'photo':
                        await self.bot.send_photo(user_id, media_file_id, caption=caption, parse_mode='HTML', reply_markup=markup)
                    elif media_type == 'video':
                        await self.bot.send_video(user_id, media_file_id, caption=caption, parse_mode='HTML', reply_markup=markup)
                    elif media_type == 'animation': # Это гифки о_0
                        await self.bot.send_animation(user_id, media_file_id, caption=caption, parse_mode='HTML', reply_markup=markup)
                    first_part_sent = True
                elif text_parts:
                    await self.bot.send_message(user_id, text_parts[0], parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
                    first_part_sent = True

                if len(text_parts) > 1:
                    for part in text_parts[1:]:
                        await self.bot.send_message(user_id, part, parse_mode='HTML', disable_web_page_preview=True)
                
                if first_part_sent:
                    delivered_count += 1
                else: 
                    failed_count += 1

            except ApiTelegramException as e:
                print(f"Failed to send to {user_id}: {e}")
                failed_count += 1
            
            await asyncio.sleep(0.05)

        end_time = time.time()
        duration = round(end_time - start_time, 2)
        await self.db.update_mailing_status(mailing_id, 'completed')
        
        report_text = (
            f"✅ <b>Рассылка #{mailing_id} завершена</b>\n\n"
            f"👍 Доставлено: {delivered_count}\n"
            f"👎 Не доставлено: {failed_count}\n"
            f"⏱ Затраченное время: {duration} сек."
        )
        try:
            await self.bot.send_message(creator_id, report_text, parse_mode='HTML')
        except ApiTelegramException:
            print(f"Failed to send report to creator {creator_id}")