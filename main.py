import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.session import engine
from app.database.models import Base
from app.bot.middlewares.db_middleware import DbSessionMiddleware
from app.bot.middlewares.user_middleware import UserSyncMiddleware

# Import Handler Routers
from app.bot.handlers.parent_child import router as parent_child_router
from app.bot.handlers.pickup import router as pickup_router
from app.bot.handlers.admin import router as admin_router


async def on_startup(bot: Bot) -> None:
    """Startup tasks: Verify database structure and log state."""
    logging.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database schemas verified.")

    bot_info = await bot.get_me()
    logging.info(f"Bot started successfully as @{bot_info.username}")


async def main() -> None:
    # 1. Setup structured logging
    setup_logging()

    # 2. Initialize Bot and Dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Register Global Middlewares (Order Matters)
    # DbSessionMiddleware opens an async session and injects it as 'db'
    dp.update.middleware(DbSessionMiddleware())
    # UserSyncMiddleware registers/updates parent records on incoming updates
    dp.update.middleware(UserSyncMiddleware())

    # 4. Register Routers
    dp.include_router(parent_child_router)
    dp.include_router(pickup_router)
    dp.include_router(admin_router)

    # 5. Execute Startup Tasks
    await on_startup(bot)

    # 6. Start Long Polling
    try:
        logging.info("Starting Telegram bot long-polling loop...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await engine.dispose()
        logging.info("Bot engine shut down safely.")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by admin.")
    except Exception as e:
        logging.critical(f"Fatal error during bot runtime: {e}", exc_info=True)
        sys.exit(1)