"""
owner_commands.py – All Owner-exclusive commands.
Imported into handlers.py / main.py and registered as CommandHandlers.
"""
import asyncio
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from PyToday import database as db
from PyToday.middleware import owner_only, ensure_user

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# /addprem <user_id> <days>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_addprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "ℹ️ <b>Usage:</b> <code>/addprem user_id days</code>\n"
            "Example: <code>/addprem 123456789 30</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[0])
        days = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id or days. Both must be numbers.", parse_mode="HTML")
        return

    user = db.add_premium(target_id, days)
    expiry = db.get_premium_expiry(target_id)
    expiry_str = expiry.strftime("%d %b %Y") if expiry else "Unknown"

    await update.message.reply_text(
        f"✅ <b>Premium Granted</b>\n\n"
        f"👤 User ID: <code>{target_id}</code>\n"
        f"📅 Duration: <b>{days} days</b>\n"
        f"⏳ Expires: <b>{expiry_str}</b>",
        parse_mode="HTML"
    )
    # Notify the user
    try:
        await context.bot.send_message(
            target_id,
            f"🎉 <b>Premium Activated!</b>\n\n"
            f"Your account has been upgraded to 💎 Premium for <b>{days} days</b>.\n"
            f"Expiry: <b>{expiry_str}</b>\n\n"
            f"Use /start to access all premium features.",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# /removeprem <user_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_removeprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Usage: <code>/removeprem user_id</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id.", parse_mode="HTML")
        return

    removed = db.remove_premium(target_id)
    if removed:
        await update.message.reply_text(
            f"✅ <b>Premium Removed</b>\n\nUser <code>{target_id}</code> has been demoted.",
            parse_mode="HTML"
        )
        try:
            await context.bot.send_message(
                target_id,
                "⚠️ Your <b>Premium</b> access has been removed.\nContact an owner to renew.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await update.message.reply_text(
            f"⚠️ User <code>{target_id}</code> is not a Premium user.",
            parse_mode="HTML"
        )


# ──────────────────────────────────────────────────────────────────────────────
# /ban <user_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Usage: <code>/ban user_id</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id.", parse_mode="HTML")
        return

    if db.is_owner(target_id):
        await update.message.reply_text("🚫 Cannot ban an Owner.", parse_mode="HTML")
        return

    db.ban_user(target_id)
    await update.message.reply_text(
        f"🚫 <b>User Banned</b>\n\n<code>{target_id}</code> has been banned.",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(target_id, "🚫 You have been <b>banned</b> from this bot.", parse_mode="HTML")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# /unban <user_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Usage: <code>/unban user_id</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id.", parse_mode="HTML")
        return

    db.unban_user(target_id)
    await update.message.reply_text(
        f"✅ <b>User Unbanned</b>\n\n<code>{target_id}</code> can now use the bot.",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(target_id, "✅ You have been <b>unbanned</b>. Use /start to continue.", parse_mode="HTML")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# /addowner <user_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_addowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Usage: <code>/addowner user_id</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id.", parse_mode="HTML")
        return

    db.add_owner(target_id)
    await update.message.reply_text(
        f"👑 <b>Owner Added</b>\n\n<code>{target_id}</code> is now an Owner.",
        parse_mode="HTML"
    )
    try:
        await context.bot.send_message(target_id, "👑 You have been granted <b>Owner</b> access!", parse_mode="HTML")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# /removeowner <user_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_removeowner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ℹ️ Usage: <code>/removeowner user_id</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid user_id.", parse_mode="HTML")
        return

    if target_id == update.effective_user.id:
        await update.message.reply_text("⚠️ You cannot remove yourself as owner.", parse_mode="HTML")
        return

    removed = db.remove_owner(target_id)
    if removed:
        await update.message.reply_text(
            f"✅ <b>Owner Removed</b>\n\n<code>{target_id}</code> is no longer an Owner.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(f"⚠️ <code>{target_id}</code> is not an Owner.", parse_mode="HTML")


# ──────────────────────────────────────────────────────────────────────────────
# /stats
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_global_stats()
    owners = db.get_all_owners()
    owner_list = "\n".join([
        f"  ◈ @{o.get('username') or 'N/A'} (<code>{o['user_id']}</code>)"
        for o in owners
    ]) or "  None"

    text = (
        f"<b>▤ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
        f"👥 Total Users: <b>{stats['total_users']}</b>\n"
        f"👑 Owners: <b>{stats['owners']}</b>\n"
        f"💎 Premium: <b>{stats['premium']}</b>\n"
        f"🎁 Trial: <b>{stats['trial']}</b>\n"
        f"👤 Regular: <b>{stats['regular']}</b>\n"
        f"🚫 Banned: <b>{stats['banned']}</b>\n\n"
        f"<b>👑 Owner List:</b>\n{owner_list}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ──────────────────────────────────────────────────────────────────────────────
# /broadcast <text> OR reply to a message
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "<b>◈ ʙʀᴏᴀᴅᴄᴀsᴛ</b>\n\n"
            "Reply to a message OR send:\n"
            "<code>/broadcast Your message here</code>\n\n"
            "<i>Supports: text, photo, video, document, audio</i>",
            parse_mode="HTML"
        )
        return

    all_user_ids = db.get_all_bot_user_ids()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"<b>▸ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...</b>\n\n"
        f"◉ Total: <code>{len(all_user_ids)}</code>\n"
        f"● Sent: <code>0</code>\n"
        f"○ Failed: <code>0</code>",
        parse_mode="HTML"
    )

    for uid in all_user_ids:
        try:
            if update.message.reply_to_message:
                msg = update.message.reply_to_message
                if msg.photo:
                    await context.bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption, parse_mode="HTML")
                elif msg.video:
                    await context.bot.send_video(uid, msg.video.file_id, caption=msg.caption, parse_mode="HTML")
                elif msg.document:
                    await context.bot.send_document(uid, msg.document.file_id, caption=msg.caption, parse_mode="HTML")
                elif msg.audio:
                    await context.bot.send_audio(uid, msg.audio.file_id, caption=msg.caption, parse_mode="HTML")
                elif msg.sticker:
                    await context.bot.send_sticker(uid, msg.sticker.file_id)
                else:
                    await context.bot.send_message(uid, msg.text or msg.caption or "", parse_mode="HTML")
            else:
                await context.bot.send_message(uid, " ".join(context.args), parse_mode="HTML")
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {uid}: {e}")
            failed += 1

        if (sent + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"<b>▸ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...</b>\n\n"
                    f"◉ Total: <code>{len(all_user_ids)}</code>\n"
                    f"● Sent: <code>{sent}</code>\n"
                    f"○ Failed: <code>{failed}</code>",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"<b>✓ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>\n\n"
        f"◉ Total: <code>{len(all_user_ids)}</code>\n"
        f"● Sent: <code>{sent}</code>\n"
        f"○ Failed: <code>{failed}</code>",
        parse_mode="HTML"
    )
