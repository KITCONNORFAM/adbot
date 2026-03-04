"""
new_handlers.py – Replacement & new handler logic.
Provides: start_command, trial/referral callbacks, per-account auto-reply handlers.
Import and register these in main.py alongside handlers.py.
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from PyToday import database as db, config
from PyToday.middleware import ensure_user, not_banned
from PyToday.keyboards import (
    main_menu_keyboard, get_non_premium_keyboard, referral_keyboard,
    premium_benefits_keyboard, auto_reply_advanced_keyboard,
    account_settings_keyboard, owner_panel_keyboard, back_to_menu_keyboard
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

NON_PREMIUM_TEXT = (
    "<b>⊘ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss</b>\n\n"
    "@{bot_username} ɪs ONʟʏ ғᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀs\n\n"
    "ᴛᴏ ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴏᴡɴᴇʀs:\n{owner_tags}"
)

PREMIUM_SECTION_TEXT = """⭐️ ᴘʀᴇᴍɪᴜᴍ ━━━━━━━━━━━━━━━━━━━━━

ʙᴇɴᴇꜰɪᴛꜱ:
• ɴᴏ ᴛᴀɢ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ
• ᴘʀᴏꜰɪʟᴇ ꜱᴛᴀʏꜱ ᴜɴᴛᴏᴜᴄʜᴇᴅ
• ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴀᴠᴇ ᴍꜱɢ
• ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ
• ᴀʟʟ ᴀᴄᴄᴏᴜɴᴛꜱ ᴄᴏᴠᴇʀᴇᴅ
• ɪɴꜱᴛᴀɴᴛ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ
• ᴘʀɪᴏʀɪᴛʏ ꜱᴜᴘᴘᴏʀᴛ"""

WELCOME_TEXT = """<b>◈ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴅ ʙᴏᴛ ◈</b>

ʜᴇʏ <code>{first_name}</code> ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴀᴅᴠᴇʀᴛɪsɪɴɢ ʙᴏᴛ

<blockquote>📢 ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴀᴅᴠᴇʀᴛɪsɪɴɢ ɪɴ ɢʀᴏᴜᴘs
💬 ᴀᴜᴛᴏ ʀᴇᴘʟʏ ᴛᴏ ᴅɪʀᴇᴄᴛ ᴍᴇssᴀɢᴇs
🔗 AUTO JOIN ɢʀᴏᴜᴘs ᴠɪᴀ ʟɪɴᴋs
📊 ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛɪsᴛɪᴄs ᴛʀᴀᴄᴋɪɴɢ
👤 MULTIPLE ᴀᴄᴄᴏᴜɴᴛ sᴜᴘᴘᴏʀᴛ
⏰ sᴄʜᴇᴅᴜʟᴇᴅ ᴍᴇssᴀɢᴇ SENDɪɴɢ</blockquote>
{expiry_line}
<i>ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</i>"""


async def _build_owner_tags(bot=None) -> str:
    owners = db.get_all_owners()
    if not owners:
        return "◈ @owneruserid"
    tags = []
    for o in owners:
        uname = o.get("username")
        fname = o.get("first_name")
        if not uname and bot:
            # Try to fetch username from Telegram
            try:
                chat = await bot.get_chat(o["user_id"])
                uname = chat.username
                fname = chat.first_name
                # Cache it in DB for next time
                if uname or fname:
                    db.create_or_update_user(o["user_id"], first_name=fname, username=uname)
            except Exception:
                pass
                
        # Fallback to OWNER_USERNAME from env if this is the primary owner
        if not uname and config.INITIAL_OWNER_IDS and o["user_id"] == config.INITIAL_OWNER_IDS[0]:
            if config.OWNER_USERNAME:
                uname = config.OWNER_USERNAME.replace("@", "")
                
        if uname:
            tags.append(f"◈ @{uname}")
        elif fname:
            tags.append(f"◈ <a href='tg://user?id={o['user_id']}'>{fname}</a>")
        else:
            tags.append(f"◈ <a href='tg://user?id={o['user_id']}'>Admin (ID: {o['user_id']})</a>")
    return " ".join(tags)


# ────────────────────────────────────────────────────────────────────────────
# /start  – entry point with referral tracking
# ────────────────────────────────────────────────────────────────────────────

@not_banned
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # ── Check if this user is brand-new BEFORE we create them
    is_new_user = db.get_user(user.id) is None

    # Always create/update the user record
    db.create_or_update_user(user.id, user.first_name, user.username)

    # ── Referral tracking — ONLY works for first-time users
    referral_notice = None
    if context.args and is_new_user:
        try:
            arg = context.args[0]
            # Support both plain ID "12345" and prefixed "ref_12345"
            referrer_id = int(arg.replace("ref_", "").strip())
            if referrer_id != user.id:
                recorded, reward_info = db.record_referral(referrer_id, user.id)
                if recorded:
                    # Notify the referrer
                    try:
                        if reward_info:
                            # They just hit the milestone (e.g. 10 invites)
                            days = reward_info["days"]
                            invites = reward_info["invites"]
                            expiry_str = reward_info["expiry"].strftime("%Y-%m-%d %H:%M UTC") if reward_info.get("expiry") else "Unknown"
                            
                            await context.bot.send_message(
                                referrer_id,
                                f"🎉 <b>{invites} Invites Consumed!</b>\n\n"
                                f"Your {days} Days Premium has been activated.\n"
                                f"⏳ <b>Expires on:</b> {expiry_str}",
                                parse_mode="HTML",
                            )
                        else:
                            # Normal referral, no reward yet
                            count = db.get_referral_count(referrer_id)
                            remaining = config.REFERRALS_REQUIRED - (count % config.REFERRALS_REQUIRED)
                            await context.bot.send_message(
                                referrer_id,
                                f"🎉 <b>New Referral!</b>\n\n"
                                f"Someone joined using your link.\n"
                                f"You need <b>{remaining}</b> more referral(s) for +14 days Premium!",
                                parse_mode="HTML",
                            )
                    except Exception:
                        pass
                    # Build notice for the new user
                    try:
                        referrer_chat = await context.bot.get_chat(referrer_id)
                        ref_name = f"@{referrer_chat.username}" if referrer_chat.username else f"<a href='tg://user?id={referrer_id}'>User</a>"
                    except Exception:
                        ref_name = f"<code>{referrer_id}</code>"
                    referral_notice = (
                        f"👥 <b>You were referred by {ref_name}!</b>\n"
                        f"Your referral has been recorded. ✅"
                    )
        except (ValueError, TypeError):
            pass

    # Show referral notice first if it exists
    if referral_notice:
        try:
            await update.message.reply_text(referral_notice, parse_mode="ʜᴛᴍʟ")
        except Exception:
            pass

    role = db.get_user_role(user.id)

    # ── Banned check is handled by @not_banned decorator

    # ── Non-premium / regular user → show upgrade screen
    if role == "user":
        ref_count = db.get_referral_count(user.id)
        owner_tags = await _build_owner_tags(context.bot)
        text = NON_PREMIUM_TEXT.format(
            bot_username=config.BOT_USERNAME,
            owner_tags=owner_tags
        )
        kb = get_non_premium_keyboard(user.id, referral_count=ref_count,
                                      referrals_required=config.REFERRALS_REQUIRED,
                                      trial_used=db.has_used_trial(user.id))
        try:
            await update.message.reply_photo(
                photo=config.START_IMAGE_URL,
                caption=text,
                parse_mode="HTML",
                reply_markup=kb,
            )
        except Exception:
            await update.message.reply_text(text, parse_mode="ʜᴛᴍʟ", reply_markup=kb)
        return

    # ── Owner, Premium, Trial → main dashboard
    # Compute live expiry line for display
    expiry_line = ""
    if role == "owner":
        expiry_line = "\n👑 <b>Owner</b> - lifetime access\n"
    elif role in ("premium", "trial"):
        expiry = db.get_premium_expiry(user.id)
        if expiry:
            expiry_str = expiry.strftime("%d %b %Y, %H:%M UTC")
            icon = "🎁" if role == "trial" else "💎"
            label = "Trial" if role == "trial" else "Premium"
            expiry_line = f"\n{icon} <b>{label} active</b> - expires <b>{expiry_str}</b>\n"
        else:
            expiry_line = "\n⚠️ <i>Expiry date missing - contact support</i>\n"

    welcome = WELCOME_TEXT.format(first_name=user.first_name, expiry_line=expiry_line)
    kb = main_menu_keyboard()

    # Add owner panel shortcut for owners
    if role == "owner" or db.is_owner(user.id):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        existing_kb = list(main_menu_keyboard().inline_keyboard)
        owner_row = [[InlineKeyboardButton("👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", callback_data="owner_panel")]]
        kb = InlineKeyboardMarkup(list(owner_row) + existing_kb)


    try:
        await update.message.reply_photo(
            photo=config.START_IMAGE_URL,
            caption=welcome,
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception:
        await update.message.reply_text(welcome, parse_mode="ʜᴛᴍʟ", reply_markup=kb)


# ────────────────────────────────────────────────────────────────────────────
# Callback: activate_trial
# ────────────────────────────────────────────────────────────────────────────

async def cb_activate_trial(query, user_id: int, context):
    if db.has_used_trial(user_id):
        await query.answer(
            "🎁 ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ.\ɴᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.",
            show_alert=True,
        )
        return

    db.activate_trial(user_id)
    expiry = db.get_premium_expiry(user_id)
    expiry_str = expiry.strftime("%d %b %Y") if expiry else f"{config.TRIAL_DAYS} days from now"

    text = (
        "<b>🎁 Trial Activated!</b>\n\n"
        f"✅ You now have <b>{config.TRIAL_DAYS} days</b> of free access.\n"
        f"⏳ Expires: <b>{expiry_str}</b>\n\n"
        "<b>Trial Limits:</b>\n"
        "• Max 1 Telegram account\n"
        "• Profile name & bio will be watermarked\n\n"
        "Upgrade to 💎 Premium to remove all restrictions!"
    )
    from PyToday.keyboards import premium_benefits_keyboard
    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=premium_benefits_keyboard())
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=premium_benefits_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Callback: buy_premium
# ────────────────────────────────────────────────────────────────────────────

async def cb_buy_premium(query, user_id: int, context):
    owners = db.get_all_owners()
    text = (
        f"<b>⭐️ ᴘʀᴇᴍɪᴜᴍ</b>\n\n"
        f"{PREMIUM_SECTION_TEXT}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ, ᴄᴏɴᴛᴀᴄᴛ ᴀɴ ᴏᴡɴᴇʀ:\n"
    )
    for o in owners:
        uname = o.get("username")
        uid = o["user_id"]
        link = f'<a href="tg://user?id={uid}">@{uname or "Owner"}</a>'
        text += f"◈ {link}\n"

    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=back_to_menu_keyboard())
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=back_to_menu_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Callback: referral_info
# ────────────────────────────────────────────────────────────────────────────

async def cb_referral_info(query, user_id: int, context):
    count = db.get_referral_count(user_id)
    next_milestone = config.REFERRALS_REQUIRED - (count % config.REFERRALS_REQUIRED)
    progress_bar = "🟩" * min(count % config.REFERRALS_REQUIRED, 10) + "⬜" * max(0, 10 - (count % config.REFERRALS_REQUIRED))

    bot_info = await context.bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        f"<b>🔥 ʀᴇғᴇʀʀᴀʟ ᴘʀᴏɢʀᴀᴍ</b>\n\n"
        f"Invite <b>{config.REFERRALS_REQUIRED} friends</b> to earn <b>+14 days Premium</b>\n\n"
        f"<b>Your Progress:</b>\n"
        f"{progress_bar}\n"
        f"<code>{count % config.REFERRALS_REQUIRED}/{config.REFERRALS_REQUIRED}</code> referrals\n"
        f"Total Referrals: <b>{count}</b>\n"
        f"Next reward in: <b>{next_milestone}</b> more invite(s)\n\n"
        f"<b>Your Invite Link:</b>\n"
        f"<code>{invite_link}</code>"
    )

    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=referral_keyboard(invite_link))
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=referral_keyboard(invite_link))


# ────────────────────────────────────────────────────────────────────────────
# Callback: owner_panel
# ────────────────────────────────────────────────────────────────────────────

async def cb_owner_panel(query, user_id: int):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ᴏɴʟʏ.", show_alert=True)
        return

    stats = db.get_global_stats()
    text = (
        f"<b>👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ</b>\n\n"
        f"👥 Users: <b>{stats['total_users']}</b>\n"
        f"💎 Premium: <b>{stats['premium']}</b>\n"
        f"🎁 Trial: <b>{stats['trial']}</b>\n"
        f"🚫 Banned: <b>{stats['banned']}</b>\n\n"
        f"<i>Use commands or buttons below:</i>"
    )
    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=owner_panel_keyboard())
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=owner_panel_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Per-Account Settings Callbacks
# ────────────────────────────────────────────────────────────────────────────

async def cb_account_settings(query, account_id: str, user_id: int):
    account = db.get_account(account_id)
    if not account or account.get("user_id") != user_id:
        await query.answer("❌ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ.", show_alert=True)
        return

    settings = db.get_account_settings(account_id)
    name = account.get("account_first_name") or account.get("phone", "Account")
    text = (
        f"<b>⚙️ ᴀᴄᴄᴏᴜɴᴛ sᴇᴛᴛɪɴɢs</b>\n"
        f"<code>{name}</code>\n\n"
        f"Configure settings for this account individually.\n"
        f"Changes apply to THIS account only."
    )
    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=account_settings_keyboard(account_id, settings))
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=account_settings_keyboard(account_id, settings))


async def cb_accset_sleep(query, account_id: str, user_id: int):
    settings = db.get_account_settings(account_id)
    current = settings.get("auto_sleep", False)
    db.update_account_settings(account_id, auto_sleep=not current)
    await cb_account_settings(query, account_id, user_id)


async def cb_accset_fwd(query, account_id: str, user_id: int):
    settings = db.get_account_settings(account_id)
    current = settings.get("use_forward_mode", False)
    db.update_account_settings(account_id, use_forward_mode=not current)
    await cb_account_settings(query, account_id, user_id)


# ────────────────────────────────────────────────────────────────────────────
# Per-Account Auto-Reply Callbacks
# ────────────────────────────────────────────────────────────────────────────

async def cb_acc_auto_reply(query, account_id: str, user_id: int):
    account = db.get_account(account_id)
    if not account or account.get("user_id") != user_id:
        await query.answer("❌ ᴀᴄᴄᴏᴜɴᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ.", show_alert=True)
        return

    settings = db.get_account_settings(account_id)
    enabled = settings.get("auto_reply_enabled", False) if settings else False
    seq_replies = db.get_sequential_replies(account_id)
    kw_replies = db.get_keyword_replies(account_id)

    text = (
        f"<b>⟐ ᴀᴜᴛᴏ ʀᴇᴘʟʏ</b>\n\n"
        f"Status: {'🟢 ON' if enabled else '🔴 OFF'}\n"
        f"Sequential Replies: <b>{len(seq_replies)}</b>\n"
        f"Keyword Replies: <b>{len(kw_replies)}</b>\n\n"
        f"<i>Sequential replies fire in order for each DM.\n"
        f"Keyword replies trigger on matching words.</i>"
    )
    try:
        await query.edit_message_caption(caption=text, parse_mode="ʜᴛᴍʟ",
                                         reply_markup=auto_reply_advanced_keyboard(enabled, account_id))
    except Exception:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=auto_reply_advanced_keyboard(enabled, account_id))


async def cb_toggle_auto_reply(query, account_id: str, user_id: int):
    settings = db.get_account_settings(account_id)
    current = settings.get("auto_reply_enabled", False) if settings else False
    db.update_account_settings(account_id, auto_reply_enabled=not current)
    await cb_acc_auto_reply(query, account_id, user_id)


async def cb_view_all_replies(query, account_id: str):
    seq = db.get_sequential_replies(account_id)
    kw = db.get_keyword_replies(account_id)

    lines = ["<b>📋 ᴀᴜᴛᴏ ʀᴇᴘʟɪᴇs</b>\n"]

    if seq:
        lines.append("<b>Sequential:</b>")
        for i, r in enumerate(seq, 1):
            preview = (r.get("message_text") or "[media]")[:50]
            lines.append(f"  {i}. {preview}")
    else:
        lines.append("<b>Sequential:</b> None")

    lines.append("")
    if kw:
        lines.append("<b>Keyword:</b>")
        for r in kw:
            kword = r.get("trigger_keyword", "?")
            preview = (r.get("message_text") or "[media]")[:40]
            lines.append(f"  🔑 <code>{kword}</code> → {preview}")
    else:
        lines.append("<b>Keyword:</b> None")

    text = "\n".join(lines)
    from PyToday.keyboards import back_to_auto_reply_keyboard
    try:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ",
                                      reply_markup=back_to_auto_reply_keyboard())
    except Exception:
        pass


async def cb_clear_replies(query, account_id: str, user_id: int):
    db.clear_replies(account_id)
    await query.answer("✅ ᴀʟʟ ʀᴇᴘʟɪᴇs ᴄʟᴇᴀʀᴇᴅ.", show_alert=False)
    await cb_acc_auto_reply(query, account_id, user_id)


# ────────────────────────────────────────────────────────────────────────────
# Owner Panel Stats/Broadcast shortcuts via inline keyboard
# ────────────────────────────────────────────────────────────────────────────

async def cb_owner_stats(query, user_id: int):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ᴏɴʟʏ.", show_alert=True)
        return
    stats = db.get_global_stats()
    owners = db.get_all_owners()
    owner_list = "\n".join([
        f"  ◈ @{o.get('username') or 'N/A'} (<code>{o['user_id']}</code>)"
        for o in owners
    ]) or "  None"
    text = (
        f"<b>▤ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
        f"👥 Total: <b>{stats['total_users']}</b>\n"
        f"👑 Owners: <b>{stats['owners']}</b>\n"
        f"💎 Premium: <b>{stats['premium']}</b>\n"
        f"🎁 Trial: <b>{stats['trial']}</b>\n"
        f"👤 Regular: <b>{stats['regular']}</b>\n"
        f"🚫 Banned: <b>{stats['banned']}</b>\n\n"
        f"<b>Owners:</b>\n{owner_list}"
    )
    try:
        await query.edit_message_text(text, parse_mode="ʜᴛᴍʟ", reply_markup=owner_panel_keyboard())
    except Exception:
        pass


async def cb_owner_addprem(query, user_id: int):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ᴏɴʟʏ.", show_alert=True)
        return
    await query.answer()
    try:
        await query.message.reply_text(
            "💎 <b>Add Premium</b>\n\nSend: <code>/addprem user_id days</code>\n"
            "Example: <code>/addprem 123456789 30</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass


async def cb_owner_ban(query, user_id: int):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ᴏɴʟʏ.", show_alert=True)
        return
    await query.answer()
    try:
        await query.message.reply_text(
            "🚫 <b>Ban User</b>\n\nSend: <code>/ban user_id</code>",
            parse_mode="HTML"
        )
    except Exception:
        pass