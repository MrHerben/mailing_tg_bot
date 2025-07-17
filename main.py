import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_filters

import config
from db_manager import DatabaseManager
from mailing_system import MailingSystem
from filters import AdminFilter, ModeratorFilter 
from states import MailingStates, AdminStates

from handlers.common import register_common_handlers
from handlers.admin import register_admin_handlers
from handlers.moderator import register_moderator_handlers


async def main():
    bot = AsyncTeleBot(config.BOT_TOKEN, parse_mode=None)
    db = DatabaseManager()
    await db.connect()
    await db.create_tables()

    ms = MailingSystem(bot, db)

    bot.add_custom_filter(AdminFilter(db))
    bot.add_custom_filter(ModeratorFilter(db))
    
    bot.add_custom_filter(asyncio_filters.StateFilter(bot))

    register_common_handlers(bot, db)
    register_admin_handlers(bot, db)
    register_moderator_handlers(bot, db, ms)
    
    ms.start()
    await ms.schedule_all_pending()

    print("Bot is starting...")
    await bot.polling(non_stop=True)
    print("Bot is started.")
    await db.close()
    ms.scheduler.shutdown()
    print("Shutted down.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")