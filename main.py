import asyncio
import logging
import signal
import sys
import time
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import NetworkError, TimedOut, RetryAfter, TelegramError
from aiohttp import web
import threading

from PyToday import database, config
from PyToday.new_handlers import start_command
from PyToday.owner_commands import (
    cmd_addprem, cmd_removeprem, cmd_ban, cmd_unban,
    cmd_addowner, cmd_removeowner, cmd_stats, cmd_broadcast
)
from PyToday.handlers import handle_callback, handle_message

# APScheduler for expiry cron
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


# ──────────────────────────────────────────────────────────────────────────────
# Error handler
# ──────────────────────────────────────────────────────────────────────────────

async def error_handler(update, context):
    try:
        raise context.error
    except NetworkError as e:
        logger.warning(f"Network error: {e}. Retrying...")
        await asyncio.sleep(config.RETRY_DELAY)
    except TimedOut as e:
        logger.warning(f"Timeout: {e}. Retrying...")
        await asyncio.sleep(config.RETRY_DELAY)
    except RetryAfter as e:
        logger.warning(f"Rate limited. Sleeping {e.retry_after}s")
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


# ──────────────────────────────────────────────────────────────────────────────
# Post-init: DB setup + seed owners + start scheduler
# ──────────────────────────────────────────────────────────────────────────────

async def post_init(application):
    await database.init_db()
    logger.info("✅ Database initialized")


# ──────────────────────────────────────────────────────────────────────────────
# Expiry Scheduler (runs every 30 minutes)
# ──────────────────────────────────────────────────────────────────────────────

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        database.sweep_expired_roles,
        trigger="interval",
        minutes=30,
        id="expiry_sweep",
        replace_existing=True
    )
    scheduler.start()
    logger.info("🕐 Expiry scheduler started (runs every 30 min)")
    return scheduler


# ──────────────────────────────────────────────────────────────────────────────
# Web server (health check)
# ──────────────────────────────────────────────────────────────────────────────

async def health_check(request):
    return web.Response(text="Bot is running!", status=200)


async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        port = int(os.getenv('PORT', 8081))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"🌐 Web server started on port {port}")
        return runner
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if not config.BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set in environment variables!")
        return

    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables!")
        return

    # Start scheduler in background
    scheduler = start_scheduler()

    # Start web server in a daemon thread
    def run_web():
        async def _run():
            runner = await start_web_server()
            while True:
                await asyncio.sleep(60)
        asyncio.run(_run())

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    print("╔══════════════════════════════════════╗")
    print("║  🤖 ᴀᴅ ʙᴏᴛ sᴛᴀʀᴛᴇᴅ (Supabase)       ║")
    print(f"║  @{config.BOT_USERNAME:<33}║")
    print("╚══════════════════════════════════════╝")

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Owner Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("addprem", cmd_addprem))
    application.add_handler(CommandHandler("removeprem", cmd_removeprem))
    application.add_handler(CommandHandler("ban", cmd_ban))
    application.add_handler(CommandHandler("unban", cmd_unban))
    application.add_handler(CommandHandler("addowner", cmd_addowner))
    application.add_handler(CommandHandler("removeowner", cmd_removeowner))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("broadcast", cmd_broadcast))

    # ── Callback & Message handlers
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    logger.info("🤖 Bot polling started...")
    # run_polling handles reconnects internally via error_handler
    try:
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            poll_interval=1.0,
            timeout=30
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
