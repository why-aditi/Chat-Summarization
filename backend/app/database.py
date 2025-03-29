from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        cls.client = AsyncIOMotorClient(settings.mongodb_url)
        cls.db = cls.client.chat_db
        
        # Create indexes for better query performance
        await cls.db.messages.create_index([('conversation_id', 1)])
        await cls.db.messages.create_index([('user_id', 1)])
        await cls.db.messages.create_index([('timestamp', -1)])
        await cls.db.summaries.create_index([('conversation_id', 1)])

    @classmethod
    async def close_db(cls):
        if cls.client:
            await cls.client.close()

    @classmethod
    async def get_db(cls):
        if not cls.client:
            await cls.connect_db()
        return cls.db

db = Database()