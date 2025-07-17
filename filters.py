from telebot.asyncio_filters import SimpleCustomFilter
from telebot.types import Message
from db_manager import DatabaseManager

class AdminFilter(SimpleCustomFilter):
    key = 'is_admin'
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

    async def check(self, message: Message):
        role = await self.db.get_user_role(message.from_user.id)
        return role == 'admin' 

class ModeratorFilter(SimpleCustomFilter):
    key = 'is_moderator'
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

    async def check(self, message: Message):
        role = await self.db.get_user_role(message.from_user.id)
        return role in ['moderator', 'admin']