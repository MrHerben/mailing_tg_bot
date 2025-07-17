import aiomysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASSWORD,
            db=DB_NAME, autocommit=True
        )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute(self, query, args=None, fetch=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, args)
                if fetch == 'one':
                    return await cursor.fetchone()
                if fetch == 'all':
                    return await cursor.fetchall()
                await conn.commit()

    async def create_tables(self):
        await self.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255) NOT NULL,
            role ENUM('user', 'moderator', 'admin') NOT NULL DEFAULT 'user', 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await self.execute("""
        CREATE TABLE IF NOT EXISTS mailings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            creator_id BIGINT NOT NULL,
            text TEXT,
            media_file_id VARCHAR(255),
            media_type ENUM('photo', 'video', 'animation'),
            keyboard JSON,
            scheduled_time DATETIME,
            status ENUM('scheduled', 'in_progress', 'completed', 'failed') NOT NULL DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(user_id)
        )
        """)

    async def add_or_update_user(self, user_id, username, first_name):
        query = """
        INSERT INTO users (user_id, username, first_name)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE username = %s, first_name = %s
        """
        await self.execute(query, (user_id, username, first_name, username, first_name))

    async def get_user_role(self, user_id):
        query = "SELECT role FROM users WHERE user_id = %s"
        result = await self.execute(query, (user_id,), fetch='one')
        return result[0] if result else 'user'

    async def set_user_role(self, user_id, role):
        user_exists = await self.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,), fetch='one')
        if not user_exists:
            return False
            
        query = "UPDATE users SET role = %s WHERE user_id = %s"
        await self.execute(query, (role, user_id))
        return True


    async def count_users(self):
        result = await self.execute("SELECT COUNT(*) FROM users", fetch='one')
        return result[0] if result else 0

    async def get_all_user_ids(self):
        results = await self.execute("SELECT user_id FROM users", fetch='all')
        return [row[0] for row in results]

    async def add_mailing(self, creator_id, text, media_file_id, media_type, keyboard, scheduled_time):
        query = """
        INSERT INTO mailings (creator_id, text, media_file_id, media_type, keyboard, scheduled_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        await self.execute(query, (creator_id, text, media_file_id, media_type, keyboard, scheduled_time))
        res = await self.execute("SELECT LAST_INSERT_ID()", fetch='one')
        return res[0]

    async def get_scheduled_mailings(self):
        query = """
        SELECT id, creator_id, scheduled_time, SUBSTRING(text, 1, 50) 
        FROM mailings 
        WHERE status = 'scheduled' AND scheduled_time > NOW()
        ORDER BY scheduled_time ASC
        """
        return await self.execute(query, fetch='all')

    async def update_mailing_status(self, mailing_id, status):
        query = "UPDATE mailings SET status = %s WHERE id = %s"
        await self.execute(query, (status, mailing_id))