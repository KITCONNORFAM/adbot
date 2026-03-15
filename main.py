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

# We now use PTB JobQueue instead of APScheduler for context.bot access

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
        try:
            if update:
                err_msg = "<b>❌ ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ. ɪꜰ ᴛʜɪs ᴘᴇʀsɪsᴛs, ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.</b>"
                if update.effective_message:
                    await update.effective_message.reply_html(err_msg)
                elif update.callback_query:
                    await update.callback_query.answer("❌ ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.", show_alert=True)
        except Exception as inner_e:
            logger.error(f"Failed to send error message to user: {inner_e}")


# ──────────────────────────────────────────────────────────────────────────────
# Post-init: DB setup + seed owners + start scheduler
# ──────────────────────────────────────────────────────────────────────────────

async def post_init(application):
    await database.init_db()
    logger.info("✅ Database initialized")

    # Auto-start auto-reply listeners for all accounts with auto_reply enabled
    asyncio.create_task(_auto_reply_watchdog())
    logger.info("✅ Auto-reply watchdog started")


async def _auto_reply_watchdog():
    """Periodically check and restart auto-reply listeners that have died."""
    from PyToday.account_worker import worker_pool
    from PyToday import telethon_handler

    await asyncio.sleep(5)  # Let the bot fully start first

    while True:
        try:
            # Get all users who have auto-reply enabled
            all_users = database.get_all_users_with_auto_reply() if hasattr(database, 'get_all_users_with_auto_reply') else []
            
            for user_data in all_users:
                user_id = user_data.get('user_id')
                if not user_id:
                    continue
                    
                accounts = database.get_accounts(user_id, logged_in_only=True)
                for account in accounts:
                    account_id = account["id"]
                    settings = database.get_account_settings(str(account_id)) or {}
                    auto_reply_enabled = settings.get('auto_reply', False)
                    reply_text = settings.get('auto_reply_text') or config.AUTO_REPLY_TEXT
                    
                    if auto_reply_enabled:
                        client_key = str(account_id)
                        adv_key = f"adv_{account_id}"
                        
                        # Check if listener is already running
                        if client_key not in telethon_handler.active_clients and adv_key not in telethon_handler.active_clients:
                            try:
                                worker = await worker_pool.get_worker(int(account_id), user_id)
                                if worker:
                                    success = await worker.start_auto_reply(reply_text)
                                    if success:
                                        telethon_handler.active_clients[adv_key] = worker.client
                                        asyncio.create_task(worker.client.run_until_disconnected())
                                        logger.info(f"Watchdog: restarted auto-reply for account {account_id}")
                            except Exception as e:
                                logger.error(f"Watchdog: failed to restart auto-reply for {account_id}: {e}")
        except Exception as e:
            logger.error(f"Auto-reply watchdog error: {e}")

        await asyncio.sleep(60)  # Check every 60 seconds



# ──────────────────────────────────────────────────────────────────────────────
# Expiry Scheduler (runs every 30 minutes via PTB JobQueue)
# ──────────────────────────────────────────────────────────────────────────────

from PyToday.keyboards import get_non_premium_keyboard

async def _check_expiries_job(context):
    """Called by PTB JobQueue every 30 minutes."""
    try:
        results = database.sweep_expired_roles()
        bot = context.bot
        
        # Notify Premium expiries
        for uid in results.get("expired_premium", []):
            try:
                ref_count = database.get_referral_count(uid)
                kb = get_non_premium_keyboard(uid, referral_count=ref_count, 
                                              referrals_required=config.REFERRALS_REQUIRED, 
                                              trial_used=database.has_used_trial(uid))
                await bot.send_message(
                    uid,
                    "⚠️ <b>Your Premium Subscription has expired!</b>\n\n"
                    "Your account has been downgraded to standard. "
                    "To regain access to Premium features, please renew your subscription or invite more users.",
                    parse_mode="HTML",
                    reply_markup=kb
                )
            except Exception as e:
                logger.error(f"Failed to notify premium expiry for {uid}: {e}")

        # Notify Trial expiries
        for uid in results.get("expired_trial", []):
            try:
                from PyToday.new_handlers import _build_owner_tags
                owner_tags = await _build_owner_tags(bot)
                ref_count = database.get_referral_count(uid)
                kb = get_non_premium_keyboard(uid, referral_count=ref_count, 
                                              referrals_required=config.REFERRALS_REQUIRED, 
                                              trial_used=True)
                
                await bot.send_message(
                    uid,
                    f"⚠️ <b>Your Free Trial has ended!</b>\n\n"
                    f"Your {config.TRIAL_DAYS}-day free trial has expired.\n\n"
                    f"TO PURCHASE PREMIUM, CONTACT AN OWNER:\n{owner_tags}",
                    parse_mode="HTML",
                    reply_markup=kb
                )
            except Exception as e:
                logger.error(f"Failed to notify trial expiry for {uid}: {e}")
                
    except Exception as e:
        logger.error(f"Expiry Job error: {e}")


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

    # Start web server in a daemon thread
    def run_web():
        async def _run():
            runner = await start_web_server()
            while True:
                await asyncio.sleep(60)
        asyncio.run(_run())

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    print("========================================")
    print("   AD BOT STARTED (Supabase)            ")
    print(f"   @{config.BOT_USERNAME:<33}")
    print("========================================")

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


if __name__ == "__main__":
    main()
