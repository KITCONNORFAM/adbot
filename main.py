import asyncio
import logging
import signal
import sys
import time
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import NetworkError, TimedOut, RetryAfter, TelegramError
from PyToday import database
from PyToday.handlers import start_command, handle_callback, handle_message, broadcast_command
from PyToday import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

async def error_handler(update, context):
    try:
        raise context.error
    except NetworkError as e:
        logger.warning(f"Network error occurred: {e}. Retrying...")
        await asyncio.sleep(config.RETRY_DELAY)
    except TimedOut as e:
        logger.warning(f"Request timed out: {e}. Retrying...")
        await asyncio.sleep(config.RETRY_DELAY)
    except RetryAfter as e:
        logger.warning(f"Rate limited. Sleeping for {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
    except TelegramError as e:
        if "Query is too old" in str(e):
            logger.warning("Callback query expired, ignoring")
        elif "Message is not modified" in str(e):
            pass
        elif "Chat not found" in str(e):
            logger.warning(f"Chat not found: {e}")
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

async def post_init(application):
    await database.init_db()
    logger.info("✅ Database initialized successfully")

async def keep_alive():
    while True:
        try:
            await asyncio.sleep(300)
            logger.debug("Keep-alive ping")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")

def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set in environment variables!")
        print("ERROR: Please set BOT_TOKEN environment variable")
        print("Get your bot token from @BotFather on Telegram")
        return
    
    if not config.MONGODB_URI:
        logger.error("MONGODB_URI not set in environment variables!")
        print("ERROR: Please set MONGODB_URI environment variable")
        return
    
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Bot started successfully!")
    print("╔══════════════════════════════════════╗")
    print("║  🤖 ᴘʏᴛᴏᴅᴀʏ ᴀᴅ ʙᴏᴛ sᴛᴀʀᴛᴇᴅ          ║")
    print("║  📢 Join t.me/PythonTodayz           ║")
    print("╚══════════════════════════════════════╝")
    
    while True:
        try:
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,
                poll_interval=1.0,
                timeout=30
            )
        except NetworkError as e:
            logger.error(f"Network error, restarting in {config.RETRY_DELAY}s: {e}")
            time.sleep(config.RETRY_DELAY)
        except TimedOut as e:
            logger.error(f"Timeout error, restarting in {config.RETRY_DELAY}s: {e}")
            time.sleep(config.RETRY_DELAY)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Fatal error, restarting in {config.RETRY_DELAY}s: {e}", exc_info=True)
            time.sleep(config.RETRY_DELAY)

if __name__ == "__main__":
    main()
