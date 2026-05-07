"""
Контракт-61: Диспетчер - Telegram Bot Entry Point
Voice-First CRM для учета кандидатов на военную службу
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from app.core.config import settings
from app.core.database import init_db
from app.handlers import commands_router, voice_router, documents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot runner"""
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    
    # Create bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(commands_router)
    dp.include_router(voice_router)
    dp.include_router(documents_router)
    
    # Start polling
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
