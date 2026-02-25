import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode
from PyToday import database as _old_db  # legacy compat shim
from PyToday import database as db        # new Supabase DB
from PyToday.encryption import encrypt_data, decrypt_data
from PyToday.keyboards import (
    main_menu_keyboard, otp_keyboard, accounts_keyboard,
    groups_keyboard, delete_accounts_keyboard, confirm_delete_keyboard,
    time_keyboard, back_to_menu_keyboard, account_selection_keyboard,
    ad_text_menu_keyboard, ad_text_back_keyboard, settings_keyboard,
    twofa_keyboard, back_to_settings_keyboard, advertising_menu_keyboard,
    accounts_menu_keyboard, support_keyboard, target_adv_keyboard,
    selected_groups_keyboard, target_groups_list_keyboard, remove_groups_keyboard,
    single_account_selection_keyboard, auto_reply_settings_keyboard,
    back_to_auto_reply_keyboard, force_sub_keyboard, force_sub_join_keyboard,
    logs_channel_keyboard, load_groups_options_keyboard,
    force_join_keyboard, owner_panel_keyboard
)
from PyToday import telethon_handler
from PyToday import config
from PyToday.new_handlers import (
    cb_activate_trial, cb_buy_premium, cb_referral_info,
    cb_owner_panel, cb_owner_stats, cb_owner_addprem, cb_owner_ban,
    cb_account_settings, cb_accset_sleep, cb_accset_fwd,
    cb_acc_auto_reply, cb_toggle_auto_reply as cb_toggle_auto_reply_new,
    cb_view_all_replies, cb_clear_replies
)

logger = logging.getLogger(__name__)
user_states = {}

WELCOME_TEXT_TEMPLATE = """
<b>ˆ ᴢ´›ᴢ´‡ʟᴢ´‡ɴ¢ʙ€ᴢ´€ᴢ´ ᴢ´€ᴢ´… ʙ™ᴢ´ᴢ´› ˆ</b>

ʜᴢ´‡ʙ <code>{first_name}</code> ᴢ´¡ᴢ´‡ʟᴢ´„ᴢ´ᴢ´ᴢ´‡ ᴢ´›ᴢ´ ʙᴢ´ᴢ´œʙ€ ᴢ´˜ᴢ´‡ʙ€sᴢ´ɴ´ᴢ´€ʟ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢ ᴢ´„ᴢ´€ᴢ´› ᴢ´€ᴢ´…ʙ™ᴢ´ᴢ´› ʙ™ʙ ᴢ´ɴªᴢ´…ɴ´ɴªɴ¢ʜᴢ´› êœ°ᴢ´‡ᴢ´…ᴢ´‡ʙ€ᴢ´€ᴢ´›ɴªᴢ´ɴ´ (OWNER @CHARLIESPRINGFAM)

<blockquote>“¢ ᴢ´€ᴢ´œᴢ´›ᴢ´ᴢ´ᴢ´€ᴢ´›ᴢ´‡ᴢ´… ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢ ɴªɴ´ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s
’¬ ᴢ´€ᴢ´œᴢ´›ᴢ´ ʙ€ᴢ´‡ᴢ´˜ʟʙ ᴢ´›ᴢ´ ᴢ´…ɴªʙ€ᴢ´‡ᴢ´„ᴢ´› ᴢ´ᴢ´‡ssᴢ´€ɴ¢ᴢ´‡s
”— ᴢ´€ᴢ´œᴢ´›ᴢ´ ᴢ´Šᴢ´ɴªɴ´ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s ᴢ´ ɴªᴢ´€ ʟɴªɴ´ᴢ´‹s
“Š ᴢ´…ᴢ´‡ᴢ´›ᴢ´€ɴªʟᴢ´‡ᴢ´… sᴢ´›ᴢ´€ᴢ´›ɴªsᴢ´›ɴªᴢ´„s ᴢ´›ʙ€ᴢ´€ᴢ´„ᴢ´‹ɴªɴ´ɴ¢
‘¤ ᴢ´ᴢ´œʟᴢ´›ɴªᴢ´˜ʟᴢ´‡ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› sᴢ´œᴢ´˜ᴢ´˜ᴢ´ʙ€ᴢ´›
° sᴢ´„ʜᴢ´‡ᴢ´…ᴢ´œʟᴢ´‡ᴢ´… ᴢ´ᴢ´‡ssᴢ´€ɴ¢ᴢ´‡ sᴢ´‡ɴ´ᴢ´…ɴªɴ´ɴ¢</blockquote>
{expiry_line}
<i>ᴢ´„ʜᴢ´ᴢ´sᴢ´‡ ᴢ´€ɴ´ ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´ ʙ™ᴢ´‡ʟᴢ´ᴢ´¡:</i>
"""

MENU_TEXT_TEMPLATE = """
<b>ˆ ᴢ´›ᴢ´‡ʟᴢ´‡ɴ¢ʙ€ᴢ´€ᴢ´ ᴢ´€ᴢ´… ʙ™ᴢ´ᴢ´› ˆ</b>

<i>ᴢ´„ʜᴢ´ᴢ´sᴢ´‡ ᴢ´€ɴ´ ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´ ʙ™ᴢ´‡ʟᴢ´ᴢ´¡:</i>
"""


def is_admin(user_id):
    """Legacy helper €“ now checks if user is an Owner in DB."""
    return db.is_owner(user_id)


async def safe_edit_message(query, text, parse_mode="HTML", reply_markup=None):
    try:
        await query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Failed to edit message: {e}")


async def safe_edit_caption(query, text, parse_mode="HTML", reply_markup=None):
    try:
        await query.edit_message_caption(caption=text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Failed to edit caption: {e}")


async def send_notification(query, text, reply_markup=None):
    try:
        await query.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


async def send_new_message(query, text, reply_markup=None):
    try:
        has_media = query.message.photo or query.message.document or query.message.video

        if has_media:
            try:
                await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=reply_markup)
                return
            except BadRequest as e:
                error_msg = str(e)
                if "Message is not modified" in error_msg:
                    return
                logger.warning(f"Caption edit failed: {e}")
                return

        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise e
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        try:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception as ex:
            logger.error(f"Failed to send reply: {ex}")


async def check_force_sub_required(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined required channels/groups"""
    settings = db.get_force_sub_settings()
    if not settings or not settings.get('enabled', False):
        return True

    channel_id = settings.get('channel_id')
    group_id = settings.get('group_id')

    if not channel_id and not group_id:
        return True

    # Check channel membership
    if channel_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            member = await bot.get_chat_member(int(channel_id), user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return False

    # Check group membership
    if group_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            member = await bot.get_chat_member(int(group_id), user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking group membership: {e}")
            return False

    return True


async def send_force_sub_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send force subscribe message to user"""
    settings = db.get_force_sub_settings()
    channel_id = settings.get('channel_id')
    group_id = settings.get('group_id')

    force_text = """<b>š ï¸ ᴢ´Šᴢ´ɴªɴ´ ʙ€ᴢ´‡ǫ«ᴢ´œɴªʙ€ᴢ´‡ᴢ´…</b>

<blockquote>ʙᴢ´ᴢ´œ ᴢ´ᴢ´œsᴢ´› ᴢ´Šᴢ´ɴªɴ´ ᴢ´›ʜᴢ´‡ ғ“ᴢ´ʟʟᴢ´ᴢ´¡ɴªɴ´ɴ¢ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟs/ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s ᴢ´›ᴢ´ ᴢ´œsᴢ´‡ ᴢ´›ʜɴªs ʙ™ᴢ´ᴢ´›:</blockquote>

"""
    keyboard = []

    if channel_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            chat = await bot.get_chat(int(channel_id))
            channel_title = chat.title or "Channel"
            force_text += f"ˆ <b>{channel_title}</b>\n"
            invite_link = chat.invite_link
            if not invite_link and chat.username:
                invite_link = f"https://t.me/{chat.username}"
            if invite_link:
                keyboard.append([InlineKeyboardButton(f"ˆ ᴢ´Šᴢ´ɴªɴ´ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ", url=invite_link)])
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            force_text += f"ˆ <b>Channel</b>\n"

    if group_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            chat = await bot.get_chat(int(group_id))
            group_title = chat.title or "Group"
            force_text += f"‰ <b>{group_title}</b>\n"
            invite_link = chat.invite_link
            if not invite_link and chat.username:
                invite_link = f"https://t.me/{chat.username}"
            if invite_link:
                keyboard.append([InlineKeyboardButton(f"‰ ᴢ´Šᴢ´ɴªɴ´ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜", url=invite_link)])
        except Exception as e:
            logger.error(f"Error getting group info: {e}")
            force_text += f"‰ <b>Group</b>\n"

    keyboard.append([InlineKeyboardButton("†» ᴢ´„ʜᴢ´‡ᴢ´„ᴢ´‹ ᴢ´€ɴ¢ᴢ´€ɴªɴ´", callback_data="check_force_sub")])

    if update.message:
        await update.message.reply_text(force_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await send_new_message(update.callback_query, force_text, InlineKeyboardMarkup(keyboard))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    db_user = db.get_user(user.id)
    if not db_user:
        db.create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    # Check force subscribe
    force_sub_settings = db.get_force_sub_settings()
    if force_sub_settings and force_sub_settings.get('enabled', False):
        is_joined = await check_force_sub_required(user.id, context)
        if not is_joined:
            await send_force_sub_message(update, context)
            return

    if config.ADMIN_ONLY_MODE and not db.is_owner(user.id):
        private_text = """
<b>Š˜ ᴢ´˜ʙ€ᴢ´‡ᴢ´ɴªᴢ´œᴢ´ ᴢ´€ᴢ´„ᴢ´„ᴢ´‡ss</b>

@cat_adbot ɴªs ᴢ´ɴ´ʟʙ ғ“ᴢ´ʙ€ ᴢ´˜ʙ€ᴢ´‡ᴢ´ɴªᴢ´œᴢ´ ᴢ´ᴢ´‡ᴢ´ʙ™ᴢ´‡ʙ€s  

ᴢ´›ᴢ´ ɴ¢ᴢ´‡ᴢ´› ᴢ´˜ʙ€ᴢ´‡ᴢ´ɴªᴢ´œᴢ´, ᴢ´„ᴢ´ɴ´ᴢ´›ᴢ´€ᴢ´„ᴢ´› ᴢ´›ʜᴢ´‡ ᴢ´ᴢ´¡ɴ´ᴢ´‡ʙ€s:  
ˆ <a href="tg://user?id=7756391784">@CHARLIESPRINGFAM</a>  
ˆ @KITCONNORFAM
"""
        try:
            await update.message.reply_photo(
                photo=config.START_IMAGE_URL,
                caption=private_text,
                parse_mode="HTML"
            )
        except:
            await update.message.reply_text(private_text, parse_mode="HTML")
        return

    total_users = db.get_users_count()

    welcome_text = WELCOME_TEXT_TEMPLATE.format(
        first_name=user.first_name,
        total_users=total_users
    )

    context.user_data['welcome_text'] = welcome_text
    context.user_data['first_name'] = user.first_name

    try:
        await update.message.reply_photo(
            photo=config.START_IMAGE_URL,
            caption=welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        await update.message.reply_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel command"""
    user = update.effective_user

    if not db.is_owner(user.id):
        await update.message.reply_text("<b>Š˜ ᴢ´›ʜɴªs ᴢ´„ᴢ´ᴢ´ᴢ´ᴢ´€ɴ´ᴢ´… ɴªs ᴢ´ɴ´ʟʙ ғ“ᴢ´ʙ€ ᴢ´€ᴢ´…ᴢ´ɴªɴ´s.</b>", parse_mode="HTML")
        return

    admin_text = """
<b>ˆ ᴢ´€ᴢ´…ᴢ´ɴªɴ´ ᴢ´˜ᴢ´€ɴ´ᴢ´‡ʟ ˆ</b>

<b>ᴢ´€ᴢ´ ᴢ´€ɴªʟᴢ´€ʙ™ʟᴢ´‡ ғ“ᴢ´‡ᴢ´€ᴢ´›ᴢ´œʙ€ᴢ´‡s:</b>

¤ sᴢ´›ᴢ´€ᴢ´›s - ᴢ´ ɴªᴢ´‡ᴢ´¡ ʙ™ᴢ´ᴢ´› sᴢ´›ᴢ´€ᴢ´›ɴªsᴢ´›ɴªᴢ´„s
ˆ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´› - sᴢ´‡ɴ´ᴢ´… ᴢ´ᴢ´‡ssᴢ´€ɴ¢ᴢ´‡ ᴢ´›ᴢ´ ᴢ´€ʟʟ ᴢ´œsᴢ´‡ʙ€s
Š— ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ sᴢ´œʙ™ - ᴢ´ᴢ´€ɴ´ᴢ´€ɴ¢ᴢ´‡ ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ sᴢ´œʙ™sᴢ´„ʙ€ɴªʙ™ᴢ´‡
‰ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ - sᴢ´‡ᴢ´› ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ
‰¡ ᴢ´œsᴢ´‡ʙ€s - ᴢ´ ɴªᴢ´‡ᴢ´¡ ᴢ´€ʟʟ ᴢ´œsᴢ´‡ʙ€s
œ• ʙ™ᴢ´€ɴ´/ᴢ´œɴ´ʙ™ᴢ´€ɴ´ - ᴢ´ᴢ´€ɴ´ᴢ´€ɴ¢ᴢ´‡ ʙ™ᴢ´€ɴ´ɴ´ᴢ´‡ᴢ´… ᴢ´œsᴢ´‡ʙ€s

<i>sᴢ´‡ʟᴢ´‡ᴢ´„ᴢ´› ᴢ´€ɴ´ ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´:</i>
"""

    await update.message.reply_text(admin_text, parse_mode="HTML", reply_markup=admin_panel_keyboard())


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not db.is_owner(user.id):
        await update.message.reply_text("<b>Š˜ ᴢ´›ʜɴªs ᴢ´„ᴢ´ᴢ´ᴢ´ᴢ´€ɴ´ᴢ´… ɴªs ᴢ´ɴ´ʟʙ ғ“ᴢ´ʙ€ ᴢ´€ᴢ´…ᴢ´ɴªɴ´s.</b>", parse_mode="HTML")
        return

    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text(
            "<b>ˆ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´› ᴢ´„ᴢ´ᴢ´ᴢ´ᴢ´€ɴ´ᴢ´…</b>\n\n"
            "ʙ€ᴢ´‡ᴢ´˜ʟʙ ᴢ´›ᴢ´ ᴢ´€ ᴢ´ᴢ´‡ssᴢ´€ɴ¢ᴢ´‡ ᴢ´ʙ€ sᴢ´‡ɴ´ᴢ´…:\n"
            "<code>/broadcast Your message here</code>\n\n"
            "<i>sᴢ´œᴢ´˜ᴢ´˜ᴢ´ʙ€ᴢ´›s: ᴢ´›ᴢ´‡xᴢ´›, ᴢ´˜ʜᴢ´ᴢ´›ᴢ´, ᴢ´ ɴªᴢ´…ᴢ´‡ᴢ´, ᴢ´…ᴢ´ᴢ´„ᴢ´œᴢ´ᴢ´‡ɴ´ᴢ´›, ᴢ´€ᴢ´œᴢ´…ɴªᴢ´</i>",
            parse_mode="HTML"
        )
        return

    user_states[user.id] = {"state": "broadcasting", "data": {}}

    all_users = db.get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"<b>¸ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´›ɴªɴ´ɴ¢...</b>\n\n"
        f"‰ ᴢ´›ᴢ´ᴢ´›ᴢ´€ʟ: <code>{len(all_users)}</code>\n"
        f" sᴢ´‡ɴ´ᴢ´›: <code>0</code>\n"
        f"‹ ғ“ᴢ´€ɴªʟᴢ´‡ᴢ´…: <code>0</code>",
        parse_mode="HTML"
    )

    for bot_user in all_users:
        try:
            if update.message.reply_to_message:
                reply_msg = update.message.reply_to_message
                if reply_msg.photo:
                    await context.bot.send_photo(
                        bot_user["_id"],
                        reply_msg.photo[-1].file_id,
                        caption=reply_msg.caption,
                        parse_mode="HTML"
                    )
                elif reply_msg.video:
                    await context.bot.send_video(
                        bot_user["_id"],
                        reply_msg.video.file_id,
                        caption=reply_msg.caption,
                        parse_mode="HTML"
                    )
                elif reply_msg.document:
                    await context.bot.send_document(
                        bot_user["_id"],
                        reply_msg.document.file_id,
                        caption=reply_msg.caption,
                        parse_mode="HTML"
                    )
                elif reply_msg.audio:
                    await context.bot.send_audio(
                        bot_user["_id"],
                        reply_msg.audio.file_id,
                        caption=reply_msg.caption,
                        parse_mode="HTML"
                    )
                elif reply_msg.voice:
                    await context.bot.send_voice(
                        bot_user["_id"],
                        reply_msg.voice.file_id,
                        caption=reply_msg.caption
                    )
                elif reply_msg.sticker:
                    await context.bot.send_sticker(
                        bot_user["_id"],
                        reply_msg.sticker.file_id
                    )
                else:
                    await context.bot.send_message(
                        bot_user["_id"],
                        reply_msg.text or reply_msg.caption,
                        parse_mode="HTML"
                    )
            else:
                text = " ".join(context.args)
                await context.bot.send_message(
                    bot_user["_id"],
                    text,
                    parse_mode="HTML"
                )
            sent += 1
        except Exception as e:
            logger.error(f"Broadcast failed for {bot_user['_id']}: {e}")
            failed += 1

        if (sent + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"<b>¸ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´›ɴªɴ´ɴ¢...</b>\n\n"
                    f"‰ ᴢ´›ᴢ´ᴢ´›ᴢ´€ʟ: <code>{len(all_users)}</code>\n"
                    f" sᴢ´‡ɴ´ᴢ´›: <code>{sent}</code>\n"
                    f"‹ ғ“ᴢ´€ɴªʟᴢ´‡ᴢ´…: <code>{failed}</code>",
                    parse_mode="HTML"
                )
            except:
                pass

        await asyncio.sleep(0.05)

    if user.id in user_states:
        del user_states[user.id]

    await status_msg.edit_text(
        f"<b>œ“ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´› ᴢ´„ᴢ´ᴢ´ᴢ´˜ʟᴢ´‡ᴢ´›ᴢ´‡</b>\n\n"
        f"‰ ᴢ´›ᴢ´ᴢ´›ᴢ´€ʟ: <code>{len(all_users)}</code>\n"
        f" sᴢ´‡ɴ´ᴢ´›: <code>{sent}</code>\n"
        f"‹ ғ“ᴢ´€ɴªʟᴢ´‡ᴢ´…: <code>{failed}</code>",
        parse_mode="HTML"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data

    await query.answer()

    # ”€”€ Ban check on every callback
    if db.is_banned(user_id):
        await query.answer("š« You are banned from using this bot.", show_alert=True)
        return

    # Check force subscribe for all callbacks except check_force_sub
    if data != "check_force_sub":
        force_sub_settings = db.get_force_sub_settings()
        if force_sub_settings and force_sub_settings.get('enabled', False):
            is_joined = await check_force_sub_required(user_id, context)
            if not is_joined:
                await send_force_sub_message(update, context)
                return

    if data.startswith("otp_"):
        await handle_otp_input(query, user_id, data, context)
        return

    if data == "twofa_cancel":
        if user_id in user_states:
            del user_states[user_id]
        await send_new_message(query, "<b>œ• 2ғ“ᴢ´€ ᴢ´ ᴢ´‡ʙ€ɴªғ“ɴªᴢ´„ᴢ´€ᴢ´›ɴªᴢ´ɴ´ ᴢ´„ᴢ´€ɴ´ᴢ´„ᴢ´‡ʟʟᴢ´‡ᴢ´….</b>\n\n<i>ʙ€ᴢ´‡ᴢ´›ᴢ´œʙ€ɴ´ɴªɴ´ɴ¢ ᴢ´›ᴢ´ ᴢ´ᴢ´€ɴªɴ´ ᴢ´ᴢ´‡ɴ´ᴢ´œ...</i>", main_menu_keyboard())
        return

    if data == "main_menu":
        await show_main_menu(query, context)

    elif data == "advertising_menu":
        await show_advertising_menu(query)

    elif data == "accounts_menu":
        await show_accounts_menu(query)

    elif data == "support":
        await show_support(query)

    elif data == "settings":
        await show_settings(query, user_id)

    elif data == "toggle_forward_mode":
        await toggle_forward_mode(query, user_id)

    elif data == "auto_reply_menu":
        await show_auto_reply_menu(query, user_id)

    elif data == "toggle_auto_reply":
        await toggle_auto_reply(query, user_id)

    elif data == "set_default_reply":
        await set_default_reply_text(query, user_id)

    elif data == "add_reply_text":
        await prompt_add_reply_text(query, user_id)

    elif data == "delete_reply_text":
        await delete_reply_text(query, user_id)

    elif data == "view_reply_text":
        await view_reply_text(query, user_id)

    elif data == "toggle_auto_group_join":
        await toggle_auto_group_join(query, user_id)

    elif data == "target_adv":
        await show_target_adv(query, user_id)

    elif data == "target_all_groups":
        await set_target_all_groups(query, user_id)

    elif data == "target_selected_groups":
        await show_selected_groups_menu(query, user_id)

    elif data == "add_target_group":
        await prompt_add_target_group(query, user_id)

    elif data == "remove_target_group":
        await show_remove_target_groups(query, user_id)

    elif data.startswith("rm_tg_"):
        group_id = int(data.split("_")[2])
        await remove_target_group(query, user_id, group_id)

    elif data == "clear_target_groups":
        await clear_all_target_groups(query, user_id)

    elif data == "view_target_groups":
        await view_target_groups(query, user_id)

    elif data == "add_account":
        await start_add_account(query, user_id)

    elif data == "delete_account":
        await show_delete_accounts(query, user_id)

    elif data.startswith("del_acc_"):
        account_id = data.split("_")[2]
        await confirm_delete_account(query, account_id)

    elif data.startswith("confirm_del_"):
        account_id = data.split("_")[2]
        await delete_account(query, user_id, account_id)

    elif data.startswith("del_page_"):
        page = int(data.split("_")[2])
        await show_delete_accounts(query, user_id, page)

    elif data == "load_groups":
        await show_load_groups_options(query)

    elif data == "load_my_groups":
        await load_groups(query, user_id)

    elif data == "load_default_groups":
        await load_default_groups(query, user_id, context)

    elif data.startswith("grp_page_"):
        parts = data.split("_")
        account_id = parts[2]
        page = int(parts[3])
        await load_account_groups_page(query, user_id, account_id, page, context)

    elif data.startswith("load_grp_"):
        account_id = data.split("_")[2]
        await load_account_groups(query, user_id, account_id, context)

    elif data == "statistics":
        await show_statistics(query, user_id)

    elif data == "set_ad_text":
        await show_ad_text_menu(query, user_id)

    elif data == "ad_saved_text":
        await show_saved_ad_text(query, user_id)

    elif data == "ad_add_text":
        await prompt_ad_text(query, user_id)

    elif data == "ad_delete_text":
        await delete_ad_text(query, user_id)

    elif data == "set_time":
        await show_time_options(query)

    elif data.startswith("time_"):
        time_val = data.split("_")[1]
        await set_time_interval(query, user_id, time_val)

    elif data == "single_mode":
        await set_single_mode(query, user_id)

    elif data == "multiple_mode":
        await set_multiple_mode(query, user_id, context)

    elif data.startswith("toggle_acc_"):
        account_id = data.split("_")[2]
        await toggle_account_selection(query, user_id, account_id, context)

    elif data.startswith("sel_page_"):
        page = int(data.split("_")[2])
        await show_account_selection(query, user_id, page, context)

    elif data == "confirm_selection":
        await confirm_account_selection(query, user_id, context)

    elif data == "my_accounts":
        await show_my_accounts(query, user_id)

    elif data.startswith("acc_page_"):
        page = int(data.split("_")[2])
        await show_my_accounts(query, user_id, page)

    elif data == "start_advertising":
        await start_advertising(query, user_id, context)

    elif data == "stop_advertising":
        context.user_data["advertising_active"] = False
        await send_new_message(
            query,
            "<b>£ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢ sᴢ´›ᴢ´ᴢ´˜ᴢ´˜ᴢ´‡ᴢ´…</b>\n\nœ“ <i>ʙᴢ´ᴢ´œʙ€ ᴢ´„ᴢ´€ᴢ´ᴢ´˜ᴢ´€ɴªɴ¢ɴ´ ʜᴢ´€s ʙ™ᴢ´‡ᴢ´‡ɴ´ sᴢ´›ᴢ´ᴢ´˜ᴢ´˜ᴢ´‡ᴢ´… sᴢ´œᴢ´„ᴢ´„ᴢ´‡ssғ“ᴢ´œʟʟʙ.</i>",
            advertising_menu_keyboard()
        )

    elif data.startswith("select_single_"):
        account_id = data.split("_")[2]
        await select_single_account(query, user_id, account_id)

    elif data.startswith("single_page_"):
        page = int(data.split("_")[2])
        await show_single_account_page(query, user_id, page)

    # Admin panel callbacks
    elif data == "admin_stats":
        await show_admin_stats(query, user_id)

    elif data == "admin_broadcast":
        await prompt_admin_broadcast(query, user_id)

    elif data == "admin_users":
        await show_admin_users(query, user_id)

    elif data == "admin_ban":
        await show_ban_menu(query, user_id)

    # Force sub callbacks
    elif data == "force_sub_menu":
        await show_force_sub_menu(query, user_id)

    elif data == "toggle_force_sub":
        await toggle_force_sub(query, user_id)

    elif data == "set_force_channel":
        await prompt_set_force_channel(query, user_id)

    elif data == "set_force_group":
        await prompt_set_force_group(query, user_id)

    elif data == "view_force_sub":
        await view_force_sub_settings(query, user_id)

    elif data == "check_force_sub":
        await check_force_sub_callback(query, user_id, context)

    # Logs channel callbacks
    elif data == "logs_channel_menu":
        await show_logs_channel_menu(query, user_id)

    elif data == "set_logs_channel":
        await prompt_set_logs_channel(query, user_id)

    elif data == "verify_logs_channel":
        await verify_logs_channel_callback(query, user_id)

    elif data == "remove_logs_channel":
        await remove_logs_channel_callback(query, user_id)

    # Force join callbacks
    elif data == "force_join_menu":
        await show_force_join_menu(query, user_id)

    elif data == "toggle_force_join":
        await toggle_force_join_callback(query, user_id)

    # ”€”€ NEW: Trial / Referral / Premium callbacks ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
    elif data == "activate_trial":
        await cb_activate_trial(query, user_id, context)

    elif data == "buy_premium":
        await cb_buy_premium(query, user_id, context)

    elif data == "referral_info":
        await cb_referral_info(query, user_id, context)

    # ”€”€ Owner panel inline callbacks ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
    elif data == "owner_panel":
        await cb_owner_panel(query, user_id)

    elif data == "owner_stats":
        await cb_owner_stats(query, user_id)

    elif data == "owner_addprem":
        await cb_owner_addprem(query, user_id)

    elif data == "owner_ban":
        await cb_owner_ban(query, user_id)

    elif data == "owner_broadcast":
        await prompt_admin_broadcast(query, user_id)

    # ”€”€ Per-account settings callbacks ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
    elif data.startswith("acc_settings_"):
        account_id = data.split("acc_settings_")[1]
        await cb_account_settings(query, account_id, user_id)

    elif data.startswith("accset_sleep_"):
        account_id = data.split("accset_sleep_")[1]
        await cb_accset_sleep(query, account_id, user_id)

    elif data.startswith("accset_fwd_"):
        account_id = data.split("accset_fwd_")[1]
        await cb_accset_fwd(query, account_id, user_id)

    elif data.startswith("accset_interval_"):
        account_id = data.split("accset_interval_")[1]
        user_states[user_id] = {"state": "awaiting_accset_interval", "account_id": account_id}
        await query.message.reply_text("⏱ <b>Set Time Interval</b>\n\nSend the delay in seconds (e.g. <code>60</code>):", parse_mode="HTML")

    elif data.startswith("accset_gap_"):
        account_id = data.split("accset_gap_")[1]
        user_states[user_id] = {"state": "awaiting_accset_gap", "account_id": account_id}
        await query.message.reply_text("⏸ <b>Set Gap</b>\n\nSend the gap in seconds between messages (e.g. <code>5</code>):", parse_mode="HTML")

    elif data.startswith("accset_rdelay_"):
        account_id = data.split("accset_rdelay_")[1]
        user_states[user_id] = {"state": "awaiting_accset_rdelay", "account_id": account_id}
        await query.message.reply_text("🔄 <b>Set Round Delay</b>\n\nSend the round delay in seconds (e.g. <code>30</code>):", parse_mode="HTML")

    # ”€”€ Per-account auto-reply advanced callbacks ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
    elif data.startswith("acc_auto_reply_"):
        account_id = data.split("acc_auto_reply_")[1]
        await cb_acc_auto_reply(query, account_id, user_id)

    elif data.startswith("toggle_auto_reply_"):
        account_id = data.split("toggle_auto_reply_")[1]
        await cb_toggle_auto_reply_new(query, account_id, user_id)

    elif data.startswith("view_all_replies_"):
        account_id = data.split("view_all_replies_")[1]
        await cb_view_all_replies(query, account_id)

    elif data.startswith("clear_replies_"):
        account_id = data.split("clear_replies_")[1]
        await cb_clear_replies(query, account_id, user_id)

    elif data.startswith("add_seq_reply_"):
        account_id = data.split("add_seq_reply_")[1]
        user_states[user_id] = {"state": "awaiting_seq_reply", "account_id": account_id}
        await query.message.reply_text(
            "œï¸ <b>Add Sequential Reply</b>\n\nSend your reply text (or send a photo/media with caption):",
            parse_mode="HTML"
        )

    elif data.startswith("add_kw_reply_"):
        account_id = data.split("add_kw_reply_")[1]
        user_states[user_id] = {"state": "awaiting_kw_keyword", "account_id": account_id}
        await query.message.reply_text(
            "”‘ <b>Add Keyword Reply</b>\n\nFirst, send the <b>trigger keyword</b> (e.g. <code>price</code>):",
            parse_mode="HTML"
        )


async def show_main_menu(query, context=None):
    if user_states.get(query.from_user.id):
        del user_states[query.from_user.id]

    first_name = query.from_user.first_name
    user_id = query.from_user.id

    # Check if user still has access
    role = db.get_user_role(user_id)
    if db.is_banned(user_id):
        await query.answer("š« You are banned.", show_alert=True)
        return
    if role == "user":
        from PyToday.new_handlers import cb_buy_premium
        ref_count = db.get_referral_count(user_id)
        from PyToday.keyboards import get_non_premium_keyboard
        from PyToday.new_handlers import NON_PREMIUM_TEXT, _build_owner_tags
        owner_tags = await _build_owner_tags(context.bot)
        text = NON_PREMIUM_TEXT.format(bot_username=config.BOT_USERNAME, owner_tags=owner_tags)
        await send_new_message(query, text, get_non_premium_keyboard(user_id, ref_count, trial_used=db.has_used_trial(user_id)))
        return

    total_users = db.get_users_count()

    # ”€”€ Live expiry display for premium / trial users
    expiry_line = ""
    if role in ("premium", "trial"):
        expiry = db.get_premium_expiry(user_id)
        if expiry:
            expiry_str = expiry.strftime("%d %b %Y, %H:%M UTC")
            icon = "Ž" if role == "trial" else "’Ž"
            label = "Trial" if role == "trial" else "Premium"
            expiry_line = f"\n{icon} <b>{label} active</b> €” expires <b>{expiry_str}</b>\n"
        else:
            expiry_line = "\nš ï¸ <i>Expiry date not found €“ contact support</i>\n"

    menu_text = WELCOME_TEXT_TEMPLATE.format(
        first_name=first_name,
        total_users=total_users,
        expiry_line=expiry_line
    )
    await send_new_message(query, menu_text, main_menu_keyboard())


async def show_advertising_menu(query):
    adv_text = """
<b>ˆ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢ ᴢ´ᴢ´‡ɴ´ᴢ´œ</b>

Â» <b>sᴢ´›ᴢ´€ʙ€ᴢ´›</b> - ʙ™ᴢ´‡ɴ¢ɴªɴ´ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢
£ <b>sᴢ´›ᴢ´ᴢ´˜</b> - sᴢ´›ᴢ´ᴢ´˜ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢
´ <b>sᴢ´‡ᴢ´› ᴢ´›ɴªᴢ´ᴢ´‡</b> - ᴢ´„ʜᴢ´€ɴ´ɴ¢ᴢ´‡ ɴªɴ´ᴢ´›ᴢ´‡ʙ€ᴢ´ ᴢ´€ʟ

<i>sᴢ´‡ʟᴢ´‡ᴢ´„ᴢ´› ᴢ´€ɴ´ ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´:</i>
"""
    await send_new_message(query, adv_text, advertising_menu_keyboard())


async def show_accounts_menu(query):
    acc_text = """
<b>ˆ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›s ᴢ´ᴢ´‡ɴ´ᴢ´œ</b>

ï¼‹ <b>ᴢ´€ᴢ´…ᴢ´…</b> - ᴢ´€ᴢ´…ᴢ´… ɴ´ᴢ´‡ᴢ´¡ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›
œ• <b>ᴢ´…ᴢ´‡ʟᴢ´‡ᴢ´›ᴢ´‡</b> - ʙ€ᴢ´‡ᴢ´ᴢ´ᴢ´ ᴢ´‡ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›
‰¡ <b>ᴢ´ʙ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›s</b> - ᴢ´ ɴªᴢ´‡ᴢ´¡ ᴢ´€ʟʟ

<i>sᴢ´‡ʟᴢ´‡ᴢ´„ᴢ´› ᴢ´€ɴ´ ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´:</i>
"""
    await send_new_message(query, acc_text, accounts_menu_keyboard())


async def show_support(query):
    support_text = """
<b>’¬ sᴢ´œᴢ´˜ᴢ´˜ᴢ´ʙ€ᴢ´› & ʜᴢ´‡ʟᴢ´˜ ᴢ´„ᴢ´‡ɴ´ᴢ´›ᴢ´‡ʙ€</b>

<blockquote expandable>†˜ <b>ɴ´ᴢ´‡ᴢ´‡ᴢ´… ᴢ´€ssɴªsᴢ´›ᴢ´€ɴ´ᴢ´„ᴢ´‡?</b>
ᴢ´¡ᴢ´‡'ʙ€ᴢ´‡ ʜᴢ´‡ʙ€ᴢ´‡ ᴢ´›ᴢ´ ʜᴢ´‡ʟᴢ´˜ ʙᴢ´ᴢ´œ 24/7!

“Œ <b>ǫ«ᴢ´œɴªᴢ´„ᴢ´‹ ʜᴢ´‡ʟᴢ´˜:</b>
€¢ ɴ¢ᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢ sᴢ´›ᴢ´€ʙ€ᴢ´›ᴢ´‡ᴢ´…: ᴢ´€ᴢ´…ᴢ´… ʙᴢ´ᴢ´œʙ€ ᴢ´›ᴢ´‡ʟᴢ´‡ɴ¢ʙ€ᴢ´€ᴢ´ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› ғ“ɴªʙ€sᴢ´›
€¢ ᴢ´€ᴢ´˜ɴª ᴢ´„ʙ€ᴢ´‡ᴢ´…ᴢ´‡ɴ´ᴢ´›ɴªᴢ´€ʟs: ɴ¢ᴢ´‡ᴢ´› ғ“ʙ€ᴢ´ᴢ´ ᴢ´ʙ.ᴢ´›ᴢ´‡ʟᴢ´‡ɴ¢ʙ€ᴢ´€ᴢ´.ᴢ´ʙ€ɴ¢
€¢ ᴢ´€ᴢ´œᴢ´›ᴢ´ ʙ€ᴢ´‡ᴢ´˜ʟʙ: ᴢ´‡ɴ´ᴢ´€ʙ™ʟᴢ´‡ ɴªɴ´ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s ᴢ´›ᴢ´ ᴢ´€ᴢ´œᴢ´›ᴢ´-ʙ€ᴢ´‡sᴢ´˜ᴢ´ɴ´ᴢ´…
€¢ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢: sᴢ´‡ᴢ´› ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´›, ᴢ´›ʜᴢ´‡ɴ´ sᴢ´›ᴢ´€ʙ€ᴢ´› ᴢ´„ᴢ´€ᴢ´ᴢ´˜ᴢ´€ɴªɴ¢ɴ´

“ž <b>ᴢ´„ᴢ´ɴ´ᴢ´›ᴢ´€ᴢ´„ᴢ´› ᴢ´ᴢ´˜ᴢ´›ɴªᴢ´ɴ´s:</b>
€¢ ᴢ´€ᴢ´…ᴢ´ɴªɴ´ sᴢ´œᴢ´˜ᴢ´˜ᴢ´ʙ€ᴢ´›: ᴢ´…ɴªʙ€ᴢ´‡ᴢ´„ᴢ´› ʜᴢ´‡ʟᴢ´˜ ғ“ʙ€ᴢ´ᴢ´ ᴢ´…ᴢ´‡ᴢ´ ᴢ´‡ʟᴢ´ᴢ´˜ᴢ´‡ʙ€
€¢ ᴢ´›ᴢ´œᴢ´›ᴢ´ʙ€ɴªᴢ´€ʟ: sᴢ´›ᴢ´‡ᴢ´˜-ʙ™ʙ-sᴢ´›ᴢ´‡ᴢ´˜ ɴ¢ᴢ´œɴªᴢ´…ᴢ´‡ ᴢ´›ᴢ´ ᴢ´œsᴢ´‡ ʙ™ᴢ´ᴢ´›

š ï¸ <b>ᴢ´„ᴢ´ᴢ´ᴢ´ᴢ´ɴ´ ɴªssᴢ´œᴢ´‡s:</b>
€¢ sᴢ´‡ssɴªᴢ´ɴ´ ᴢ´‡xᴢ´˜ɴªʙ€ᴢ´‡ᴢ´…? ʙ€ᴢ´‡-ʟᴢ´ɴ¢ɴªɴ´ ʙᴢ´ᴢ´œʙ€ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›
€¢ ᴢ´ᴢ´›ᴢ´˜ ɴ´ᴢ´ᴢ´› ʙ€ᴢ´‡ᴢ´„ᴢ´‡ɴªᴢ´ ᴢ´‡ᴢ´…? ᴢ´„ʜᴢ´‡ᴢ´„ᴢ´‹ ᴢ´›ᴢ´‡ʟᴢ´‡ɴ¢ʙ€ᴢ´€ᴢ´ ᴢ´€ᴢ´˜ᴢ´˜
€¢ 2ғ“ᴢ´€ ʙ€ᴢ´‡ǫ«ᴢ´œɴªʙ€ᴢ´‡ᴢ´…? ᴢ´‡ɴ´ᴢ´›ᴢ´‡ʙ€ ʙᴢ´ᴢ´œʙ€ ᴢ´„ʟᴢ´ᴢ´œᴢ´… ᴢ´˜ᴢ´€ssᴢ´¡ᴢ´ʙ€ᴢ´…</blockquote>
"""
    await send_new_message(query, support_text, support_keyboard())


async def show_settings(query, user_id):
    # Fetch account-level settings for the user's primary account
    accounts = db.get_accounts(user_id, logged_in_only=True)
    use_multiple = len(accounts) > 1
    use_forward = False
    auto_reply = False
    auto_group_join = False
    if accounts:
        s = db.get_account_settings(accounts[0]["id"])
        use_forward = s.get("use_forward_mode", False) if s else False
        auto_reply = s.get("auto_reply_enabled", False) if s else False

    mode_text = "“±“± Multiple" if use_multiple else "“± Single"
    forward_text = "œ‰ï¸ Forward" if use_forward else "“¤ Send"
    auto_reply_text = "Ÿ¢ ON" if auto_reply else "”´ OFF"
    auto_join_text = "Ÿ¢ ON" if auto_group_join else "”´ OFF"

    settings_text = f"""
<b>š™ï¸ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<b>“Š Current Configuration:</b>

”¹ <b>Account Mode:</b> {mode_text}
”¹ <b>Message Mode:</b> {forward_text}
”¹ <b>Auto Reply:</b> {auto_reply_text}
”¹ <b>Auto Join:</b> {auto_join_text}

<i>Tap to change settings:
For per-account config, open My Accounts †’ select account.</i>
"""

    force_sub_settings = db.get_force_sub_settings()
    force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False

    await send_new_message(query, settings_text, settings_keyboard(use_multiple, use_forward, auto_reply, auto_group_join, force_sub_enabled, db.is_owner(user_id)))


async def toggle_forward_mode(query, user_id):
    """Toggle forward mode for first active account."""
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if not accounts:
        await query.answer("š ï¸ No accounts connected. Add an account first.", show_alert=True)
        return
    acc = accounts[0]
    s = db.get_account_settings(acc["id"]) or {}
    current_mode = s.get("use_forward_mode", False)
    new_mode = not current_mode
    db.update_account_settings(acc["id"], use_forward_mode=new_mode)

    if new_mode:
        mode_text = "<b>œ‰ï¸ ғ“ᴢ´ʙ€ᴢ´¡ᴢ´€ʙ€ᴢ´… ᴢ´ᴢ´ᴢ´…ᴢ´‡</b>"
        description = "<i>Messages will be forwarded from Saved Messages</i>"
        icon = "Ÿ¢"
    else:
        mode_text = "<b>“¤ sᴢ´‡ɴ´ᴢ´… ᴢ´ᴢ´ᴢ´…ᴢ´‡</b>"
        description = "<i>Messages will be sent directly</i>"
        icon = "”´"

    result_text = f"""
{icon} <b>ᴢ´ᴢ´ᴢ´…ᴢ´‡ ᴢ´„ʜᴢ´€ɴ´ɴ¢ᴢ´‡ᴢ´…</b>

œ… Changed to: {mode_text}
{description}
"""
    await send_new_message(query, result_text, back_to_settings_keyboard())


async def show_auto_reply_menu(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    auto_reply = False
    is_custom = False
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        auto_reply = s.get("auto_reply_enabled", False)
        is_custom = bool(s.get("sequential_replies") or s.get("keyword_replies"))

    status = "Ÿ¢ ON" if auto_reply else "”´ OFF"
    text_type = "Custom" if is_custom else "Default"

    menu_text = f"""
<b>’¬ ᴢ´€ᴢ´œᴢ´›ᴢ´ ʙ€ᴢ´‡ᴢ´˜ʟʙ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<b>“Š Current Configuration:</b>

”¹ <b>Status:</b> {status}
”¹ <b>Text Type:</b> {text_type}

<i>Manage your auto-reply settings:</i>
"""
    await send_new_message(query, menu_text, auto_reply_settings_keyboard(auto_reply))


async def toggle_auto_reply(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if not accounts:
        await query.answer("š ï¸ No accounts connected.", show_alert=True)
        return
    acc = accounts[0]
    s = db.get_account_settings(acc["id"]) or {}
    current_mode = s.get("auto_reply_enabled", False)
    new_mode = not current_mode
    db.update_account_settings(acc["id"], auto_reply_enabled=new_mode)

    if new_mode:
        await telethon_handler.start_all_auto_reply_listeners(user_id, config.AUTO_REPLY_TEXT)
        status_detail = "Auto-reply started"
    else:
        await telethon_handler.stop_all_auto_reply_listeners(user_id)
        status_detail = "Auto-reply stopped"

    status = "Ÿ¢ ON" if new_mode else "”´ OFF"
    result_text = f"""
<b>’¬ ᴢ´€ᴢ´œᴢ´›ᴢ´ ʙ€ᴢ´‡ᴢ´˜ʟʙ</b>

œ… Auto Reply is now: <b>{status}</b>
“Š {status_detail}
"""
    await send_new_message(query, result_text, auto_reply_settings_keyboard(new_mode))


async def set_default_reply_text(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        auto_reply = s.get("auto_reply_enabled", False)
        if auto_reply:
            await telethon_handler.start_all_auto_reply_listeners(user_id, config.AUTO_REPLY_TEXT)
    else:
        auto_reply = False

    result_text = f"""
<b>“ ᴢ´…ᴢ´‡ғ“ᴢ´€ᴢ´œʟᴢ´› ᴢ´›ᴢ´‡xᴢ´› sᴢ´‡ᴢ´›</b>

œ… Now using default reply text:

{config.AUTO_REPLY_TEXT}
"""
    await send_new_message(query, result_text, auto_reply_settings_keyboard(auto_reply))


async def prompt_add_reply_text(query, user_id):
    user_states[user_id] = {"state": "awaiting_reply_text"}

    prompt_text = """
<b>• ᴢ´€ᴢ´…ᴢ´… ʙ€ᴢ´‡ᴢ´˜ʟʙ ᴢ´›ᴢ´‡xᴢ´›</b>

“ <b>Send your custom auto-reply text:</b>

<i>This message will be sent automatically when someone DMs your account.</i>
"""

    await send_new_message(query, prompt_text, back_to_auto_reply_keyboard())


async def delete_reply_text(query, user_id):
    user = db.get_user(user_id)
    current_text = user.get('auto_reply_text', '') if user else ''
    auto_reply = user.get('auto_reply_enabled', False) if user else False

    if not current_text:
        result_text = """
<b>Œ ɴ´ᴢ´ ᴢ´„ᴢ´œsᴢ´›ᴢ´ᴢ´ ᴢ´›ᴢ´‡xᴢ´›</b>

<i>You don't have any custom reply text set. Using default text.</i>
"""
    else:
        db.update_user(user_id, auto_reply_text='')

        if auto_reply:
            await telethon_handler.start_all_auto_reply_listeners(user_id, config.AUTO_REPLY_TEXT)

        result_text = """
<b>—‘ï¸ ᴢ´›ᴢ´‡xᴢ´› ᴢ´…ᴢ´‡ʟᴢ´‡ᴢ´›ᴢ´‡ᴢ´…</b>

œ… Custom reply text has been deleted.

<i>Now using default text.</i>
"""

    await send_new_message(query, result_text, auto_reply_settings_keyboard(auto_reply))


async def view_reply_text(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    auto_reply = False
    custom_text = ""
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        auto_reply = s.get("auto_reply_enabled", False)
        replies = s.get("sequential_replies") or []
        custom_text = replies[0].get("text", "") if replies else ""

    if custom_text:
        text_type = "Custom"
        display_text = custom_text
    else:
        text_type = "Default"
        display_text = config.AUTO_REPLY_TEXT

    result_text = f"""
<b>‘ï¸ ᴢ´„ᴢ´œʙ€ʙ€ᴢ´‡ɴ´ᴢ´› ʙ€ᴢ´‡ᴢ´˜ʟʙ ᴢ´›ᴢ´‡xᴢ´›</b>

<b>“Š Type:</b> {text_type}

<b>“ Text:</b>
{display_text}
"""
    await send_new_message(query, result_text, auto_reply_settings_keyboard(auto_reply))


async def toggle_auto_group_join(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if not accounts:
        await query.answer("š ï¸ No accounts connected.", show_alert=True)
        return
    acc = accounts[0]
    s = db.get_account_settings(acc["id"]) or {}
    current_mode = s.get("auto_group_join", False)
    new_mode = not current_mode
    db.update_account_settings(acc["id"], auto_group_join=new_mode)

    accounts_all = db.get_accounts(user_id, logged_in_only=True)
    use_multiple = len(accounts_all) > 1
    use_forward = s.get("use_forward_mode", False)
    auto_reply = s.get("auto_reply_enabled", False)
    force_sub_settings = db.get_force_sub_settings() or {}
    force_sub_enabled = force_sub_settings.get('enabled', False)

    status = "Ÿ¢ ON" if new_mode else "”´ OFF"
    result_text = f"""
<b>”— ᴢ´€ᴢ´œᴢ´›ᴢ´ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜ ᴢ´Šᴢ´ɴªɴ´</b>

œ… Auto Join is now: <b>{status}</b>

<i>When enabled, accounts will auto-join groups from links</i>
"""
    await send_new_message(query, result_text, settings_keyboard(use_multiple, use_forward, auto_reply, new_mode, force_sub_enabled, db.is_owner(user_id)))


async def show_target_adv(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    target_mode = "all"
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        target_mode = s.get("target_mode", "all")

    target_text = f"""
<b>🎯 ᴛᴀʀɢᴇᴛ ᴀᴅᴠᴇʀᴛɪsɪɴɢ</b>

<b>📊 Current Mode:</b> <code>{target_mode.upper()}</code>

📢 <b>All Groups</b> - Send to all groups
🎯 <b>Selected</b> - Send to specific groups
"""
    await send_new_message(query, target_text, target_adv_keyboard(target_mode))


async def set_target_all_groups(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if accounts:
        db.update_account_settings(accounts[0]["id"], target_mode="all")

    result_text = """
<b>œ… ᴢ´›ᴢ´€ʙ€ɴ¢ᴢ´‡ᴢ´› sᴢ´‡ᴢ´›</b>

“¢ Target Mode: <b>ALL GROUPS</b>

<i>Messages will be sent to all groups</i>
"""
    await send_new_message(query, result_text, target_adv_keyboard("all"))


async def show_selected_groups_menu(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if accounts:
        db.update_account_settings(accounts[0]["id"], target_mode="selected")

    target_groups = db.get_target_groups(user_id)

    menu_text = f"""
<b>Ž¯ sᴢ´‡ʟᴢ´‡ᴢ´„ᴢ´›ᴢ´‡ᴢ´… ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s</b>

<b>“Š Selected Groups:</b> <code>{len(target_groups)}</code>

• Add groups by ID
– Remove groups
“‹ View all selected
"""
    await send_new_message(query, menu_text, selected_groups_keyboard())


async def prompt_add_target_group(query, user_id):
    user_states[user_id] = {"state": "awaiting_target_group_id", "data": {}}

    prompt_text = """
<b>• ᴢ´€ᴢ´…ᴢ´… ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜</b>

<i>Send the Group ID to add:</i>

<b>’¡ How to get Group ID:</b>
Forward a message from the group to @userinfobot
"""

    await send_new_message(query, prompt_text, back_to_menu_keyboard())


async def remove_target_group(query, user_id, group_id):
    removed = db.remove_target_group(user_id, group_id)

    if removed:
        result_text = f"""
<b>œ… ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜ ʙ€ᴢ´‡ᴢ´ᴢ´ᴢ´ ᴢ´‡ᴢ´…</b>

—‘ï¸ Group <code>{group_id}</code> removed successfully.
"""
    else:
        result_text = f"""
<b>Œ ᴢ´‡ʙ€ʙ€ᴢ´ʙ€</b>

Group <code>{group_id}</code> not found.
"""
    await send_new_message(query, result_text, selected_groups_keyboard())


async def show_remove_target_groups(query, user_id, page=0):
    target_groups = db.get_target_groups(user_id)

    if not target_groups:
        await send_new_message(
            query,
            "<b>Œ No groups to remove</b>\n\n<i>Add some groups first.</i>",
            selected_groups_keyboard()
        )
        return

    await send_new_message(
        query,
        "<b>—‘ï¸ Select a group to remove:</b>",
        remove_groups_keyboard(target_groups, page)
    )


async def clear_all_target_groups(query, user_id):
    count = db.clear_target_groups(user_id)

    result_text = f"""
<b>—‘ï¸ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s ᴢ´„ʟᴢ´‡ᴢ´€ʙ€ᴢ´‡ᴢ´…</b>

œ… Removed <code>{count or 0}</code> groups from target list.
"""
    await send_new_message(query, result_text, selected_groups_keyboard())


async def view_target_groups(query, user_id, page=0):
    target_groups = db.get_target_groups(user_id)

    if not target_groups:
        await send_new_message(
            query,
            "<b>“‹ No targeted groups</b>\n\n<i>Add groups to target them.</i>",
            selected_groups_keyboard()
        )
        return

    await send_new_message(
        query,
        f"<b>“‹ Targeted Groups ({len(target_groups)})</b>",
        target_groups_list_keyboard(target_groups, page)
    )


async def start_add_account(query, user_id):
    user_states[user_id] = {"state": "awaiting_api_id", "data": {}}

    prompt_text = """
<b>• ᴢ´€ᴢ´…ᴢ´… ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´›</b>

<b>Step 1/4:</b> Send your <b>API ID</b>

Get it from: <a href="https://my.telegram.org">my.telegram.org</a>
"""

    await send_new_message(query, prompt_text, back_to_menu_keyboard())


async def show_delete_accounts(query, user_id, page=0):
    accounts = db.get_accounts(user_id)

    if not accounts:
        await send_new_message(
            query,
            "<b>Œ No accounts to delete</b>\n\n<i>Add an account first.</i>",
            accounts_menu_keyboard()
        )
        return

    await send_new_message(
        query,
        "<b>—‘ï¸ Select an account to delete:</b>",
        delete_accounts_keyboard(accounts, page)
    )


async def confirm_delete_account(query, account_id):
    account = db.get_account(account_id)

    if not account:
        await send_new_message(
            query,
            "<b>Œ Account not found</b>",
            accounts_menu_keyboard()
        )
        return

    display_name = account.get('account_first_name') or account.get('phone', 'Unknown')

    confirm_text = f"""
<b>š ï¸ ᴢ´„ᴢ´ɴ´ғ“ɴªʙ€ᴢ´ ᴢ´…ᴢ´‡ʟᴢ´‡ᴢ´›ᴢ´‡</b>

Are you sure you want to delete:
<b>{display_name}</b>?

<i>This action cannot be undone.</i>
"""
    await send_new_message(query, confirm_text, confirm_delete_keyboard(account_id))


async def delete_account(query, user_id, account_id):
    deleted = db.delete_account(account_id, user_id)

    if deleted:
        result_text = """
<b>œ… ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› ᴢ´…ᴢ´‡ʟᴢ´‡ᴢ´›ᴢ´‡ᴢ´…</b>

Account removed successfully.
"""
    else:
        result_text = """
<b>Œ ᴢ´‡ʙ€ʙ€ᴢ´ʙ€</b>

Failed to delete account.
"""
    await send_new_message(query, result_text, accounts_menu_keyboard())


async def show_load_groups_options(query):
    """Show options for loading groups"""
    options_text = """
<b>“‚ ʟᴢ´ᴢ´€ᴢ´… ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s/ᴢ´ᴢ´€ʙ€ᴢ´‹ᴢ´‡ᴢ´›ᴢ´˜ʟᴢ´€ᴢ´„ᴢ´‡s</b>

<b>ˆ ʟᴢ´ᴢ´€ᴢ´… ᴢ´ʙ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s</b>
Load groups from your logged-in account

<b>‰ ʟᴢ´ᴢ´€ᴢ´… ᴢ´…ᴢ´‡ғ“ᴢ´€ᴢ´œʟᴢ´› ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s</b>
Load groups from group_mps.txt file

<i>Select an option:</i>
"""
    await send_new_message(query, options_text, load_groups_options_keyboard())


async def load_groups(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)

    if not accounts:
        await send_new_message(
            query,
            "<b>Œ No logged in accounts</b>\n\n<i>Please add and login to an account first.</i>",
            main_menu_keyboard()
        )
        return

    if len(accounts) == 1:
        account = accounts[0]
        account_id = str(account.get("id", account.get("_id", "")))

        await send_new_message(
            query,
            "<b>³ Loading groups...</b>\n\n<i>Please wait while we fetch your groups and marketplaces.</i>",
            None
        )

        result = await telethon_handler.get_groups_and_marketplaces(account_id)

        if not result["success"]:
            await send_new_message(
                query,
                f"<b>Œ Error loading groups</b>\n\n{result.get('error', 'Unknown error')}",
                main_menu_keyboard()
            )
            return

        all_chats = result["groups"] + result["marketplaces"]

        groups_text = f"""
<b>“‚ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s & ᴢ´ᴢ´€ʙ€ᴢ´‹ᴢ´‡ᴢ´›ᴢ´˜ʟᴢ´€ᴢ´„ᴢ´‡s</b>

‘¥ <b>Groups:</b> <code>{len(result['groups'])}</code>
ª <b>Marketplaces:</b> <code>{len(result['marketplaces'])}</code>
“Š <b>Total:</b> <code>{result['total']}</code>
"""
        await send_new_message(query, groups_text, groups_keyboard(all_chats, account_id))
    else:
        await send_new_message(
            query,
            "<b>“‚ Select an account to load groups:</b>",
            single_account_selection_keyboard([acc for acc in accounts if acc.get('is_logged_in')])
        )


async def load_default_groups(query, user_id, context):
    """Load groups from group_mps.txt file and auto-join with user's logs channel"""
    try:
        # Check if user has logs channel set and verified
        logs_channel = db.get_logs_channel(user_id)
        if not logs_channel or not logs_channel.get('verified'):
            await send_new_message(
                query,
                "<b>š ï¸ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ʙ€ᴢ´‡ǫ«ᴢ´œɴªʙ€ᴢ´‡ᴢ´…</b>\n\n"
                "<blockquote>ʙᴢ´ᴢ´œ ᴢ´ᴢ´œsᴢ´› sᴢ´‡ᴢ´› ᴢ´œᴢ´˜ ᴢ´€ɴ´ᴢ´… ᴢ´ ᴢ´‡ʙ€ɴªғ“ʙ ᴢ´€ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ʙ™ᴢ´‡ғ“ᴢ´ʙ€ᴢ´‡ ᴢ´€ᴢ´œᴢ´›ᴢ´-ᴢ´Šᴢ´ɴªɴ´ɴªɴ´ɴ¢ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s.</blockquote>\n\n"
                "<b>ʜᴢ´ᴢ´¡ ᴢ´›ᴢ´ sᴢ´‡ᴢ´› ᴢ´œᴢ´˜:</b>\n"
                "1. ᴢ´„ʙ€ᴢ´‡ᴢ´€ᴢ´›ᴢ´‡ ᴢ´€ ɴ´ᴢ´‡ᴢ´¡ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ\n"
                "2. ᴢ´€ᴢ´…ᴢ´… ᴢ´›ʜɴªs ʙ™ᴢ´ᴢ´› ᴢ´€s ᴢ´€ᴢ´…ᴢ´ɴªɴ´\n"
                "3. ɴ¢ᴢ´ ᴢ´›ᴢ´ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s †’ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ\n"
                "4. sᴢ´‡ɴ´ᴢ´… ᴢ´›ʜᴢ´‡ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ɴªᴢ´… ᴢ´€ɴ´ᴢ´… ᴢ´ ᴢ´‡ʙ€ɴªғ“ʙ.",
                back_to_menu_keyboard()
            )
            return

        logs_channel_id = logs_channel.get('channel_id')

        # Read group links from file (use bundled file)
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        group_file_path = os.path.join(script_dir, '..', 'group_mps.txt')
        
        # Also check in current directory
        if not os.path.exists(group_file_path):
            group_file_path = 'group_mps.txt'
        
        group_links = []
        try:
            with open(group_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        group_links.append(line)
        except FileNotFoundError:
            await send_new_message(
                query,
                "<b>Œ Error</b>\n\n<i>Group links file not found. Please contact admin.</i>",
                main_menu_keyboard()
            )
            return

        if not group_links:
            await send_new_message(
                query,
                "<b>Œ No groups found</b>\n\n<i>No valid group links found in the file.</i>",
                main_menu_keyboard()
            )
            return

        # Get user's accounts
        accounts = db.get_accounts(user_id, logged_in_only=True)
        if not accounts:
            await send_new_message(
                query,
                "<b>Œ No logged in accounts</b>\n\n<i>Please add and login to an account first.</i>",
                main_menu_keyboard()
            )
            return

        await send_new_message(
            query,
            f"<b>³ Auto-joining groups...</b>\n\n<i>Found {len(group_links)} groups to join. This may take a while.</i>",
            None
        )

        # Join groups using the first account with user's logs channel
        account = accounts[0]
        account_id = str(account["_id"])

        # Auto-join groups with user's logs channel (only this user's logs will be sent)
        result = await telethon_handler.auto_join_groups_from_file(
            account_id,
            group_links,
            logs_channel_id=logs_channel_id,
            user_id=user_id
        )

        result_text = f"""
<b>œ… ᴢ´€ᴢ´œᴢ´›ᴢ´-ᴢ´Šᴢ´ɴªɴ´ ᴢ´„ᴢ´ᴢ´ᴢ´˜ʟᴢ´‡ᴢ´›ᴢ´‡</b>

“Š <b>Results:</b>
œ… Joined: <code>{result['joined']}</code>
š ï¸ Already member: <code>{result['already_member']}</code>
Œ Failed: <code>{result['failed']}</code>
“Š Total: <code>{result['total']}</code>

<i>All logs sent to your logs channel only.</i>
"""

        await send_new_message(query, result_text, main_menu_keyboard())

    except Exception as e:
        logger.error(f"Error loading default groups: {e}")
        await send_new_message(
            query,
            f"<b>Œ Error</b>\n\n<i>{str(e)}</i>",
            main_menu_keyboard()
        )


async def load_account_groups(query, user_id, account_id, context):
    await send_new_message(
        query,
        "<b>³ Loading groups...</b>\n\n<i>Please wait...</i>",
        None
    )

    result = await telethon_handler.get_groups_and_marketplaces(account_id)

    if not result["success"]:
        await send_new_message(
            query,
            f"<b>Œ Error loading groups</b>\n\n{result.get('error', 'Unknown error')}",
            main_menu_keyboard()
        )
        return

    all_chats = result["groups"] + result["marketplaces"]
    context.user_data[f"groups_{account_id}"] = all_chats

    groups_text = f"""
<b>“‚ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜s & ᴢ´ᴢ´€ʙ€ᴢ´‹ᴢ´‡ᴢ´›ᴢ´˜ʟᴢ´€ᴢ´„ᴢ´‡s</b>

‘¥ <b>Groups:</b> <code>{len(result['groups'])}</code>
ª <b>Marketplaces:</b> <code>{len(result['marketplaces'])}</code>
“Š <b>Total:</b> <code>{result['total']}</code>
"""

    await send_new_message(query, groups_text, groups_keyboard(all_chats, account_id))


async def load_account_groups_page(query, user_id, account_id, page, context):
    all_chats = context.user_data.get(f"groups_{account_id}", [])

    if not all_chats:
        result = await telethon_handler.get_groups_and_marketplaces(account_id)
        if result["success"]:
            all_chats = result["groups"] + result["marketplaces"]
            context.user_data[f"groups_{account_id}"] = all_chats

    await send_new_message(
        query,
        f"<b>“‚ Groups (Page {page + 1})</b>",
        groups_keyboard(all_chats, account_id, page)
    )


async def show_statistics(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)

    if not accounts:
        stats_text = """
<b>“Š sᴢ´›ᴢ´€ᴢ´›ɴª sᴢ´›ɴªᴢ´„s</b>

<i>No accounts found. Add an account first.</i>
"""
        await send_new_message(query, stats_text, back_to_settings_keyboard())
        return

    stats_text = "<b>“Š ʙᴢ´ᴢ´œʙ€ ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› sᴢ´›ᴢ´€ᴢ´›ɴªsᴢ´›ɴªᴢ´„s</b>\n\n"

    for account in accounts:
        display_name = account.get('account_first_name') or account.get('phone', 'Unknown')
        if account.get('account_username'):
            display_name = f"{display_name} (@{account.get('account_username')})"

        acc_id = account.get("id", account.get("_id", ""))
        stats = db.get_account_stats(acc_id) if hasattr(db, 'get_account_stats') else {}

        sent = (stats or {}).get("messages_sent", 0)
        failed = (stats or {}).get("messages_failed", 0)
        groups = (stats or {}).get("groups_count", 0) + (stats or {}).get("marketplaces_count", 0)
        replies = (stats or {}).get("auto_replies_sent", 0)
        joined = (stats or {}).get("groups_joined", 0)

        stats_text += f"""
<b>“± {display_name[:30]}</b>
œ… Sent: <code>{sent}</code> | Œ Failed: <code>{failed}</code>
‘¥ Groups: <code>{groups}</code> | ’¬ Replies: <code>{replies}</code>
”— Joined: <code>{joined}</code>
"""

    stats_text += f"""
<b>“± Total Accounts:</b> <code>{len(accounts)}</code>
"""
    await send_new_message(query, stats_text, back_to_settings_keyboard())


async def show_ad_text_menu(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    ad_text = None
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        ad_text = s.get("ad_text")
    ad_status = "œ… Set" if ad_text else "Œ Not Set"

    menu_text = f"""
<b>“ ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´› ᴢ´ᴢ´‡ɴ´ᴢ´œ</b>

“ <b>Ad Text:</b> {ad_status}

<i>Select an option:</i>
"""
    await send_new_message(query, menu_text, ad_text_menu_keyboard())


async def show_saved_ad_text(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    ad_text = None
    if accounts:
        s = db.get_account_settings(accounts[0]["id"]) or {}
        ad_text = s.get("ad_text")

    if ad_text:
        display_text = f"""
<b>“„ sᴢ´€ᴢ´ ᴢ´‡ᴢ´… ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´›</b>

{ad_text[:500]}{'...' if len(ad_text) > 500 else ''}
"""
    else:
        display_text = """
<b>“„ sᴢ´€ᴢ´ ᴢ´‡ᴢ´… ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´›</b>

<i>No ad text saved.</i>
"""
    await send_new_message(query, display_text, ad_text_back_keyboard())


async def prompt_ad_text(query, user_id):
    user_states[user_id] = {"state": "awaiting_ad_text", "data": {}}

    prompt_text = """
<b>• ᴢ´€ᴢ´…ᴢ´… ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´›</b>

<i>Send your ad text now:</i>

<b>’¡ Tips:</b>
€¢ Use <code>&lt;b&gt;text&lt;/b&gt;</code> for <b>bold</b>
€¢ Use <code>&lt;i&gt;text&lt;/i&gt;</code> for <i>italic</i>
€¢ Use <code>&lt;blockquote&gt;text&lt;/blockquote&gt;</code> for quotes
"""

    await send_new_message(query, prompt_text, ad_text_back_keyboard())


async def delete_ad_text(query, user_id):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    if accounts:
        db.update_account_settings(accounts[0]["id"], ad_text=None)

    result_text = """
<b>—‘ï¸ ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´› ᴢ´…ᴢ´‡ʟᴢ´‡ᴢ´›ᴢ´‡ᴢ´…</b>

œ… Your ad text has been deleted.
"""
    await send_new_message(query, result_text, ad_text_menu_keyboard())


async def show_time_options(query):
    time_text = """
<b>±ï¸ sᴢ´‡ᴢ´› ᴢ´›ɴªᴢ´ᴢ´‡ ɴªɴ´ᴢ´›ᴢ´‡ʙ€ᴢ´ ᴢ´€ʟ</b>

<i>Select the delay between messages:</i>
"""

    await send_new_message(query, time_text, time_keyboard())


async def set_time_interval(query, user_id, time_val):
    if time_val == "custom":
        user_states[user_id] = {"state": "awaiting_custom_time", "data": {}}
        await send_new_message(
            query,
            "<b>š™ï¸ Custom Time</b>\n\n<i>Send the delay in seconds:</i>",
            back_to_menu_keyboard()
        )
        return

    try:
        seconds = int(time_val)
        accounts = db.get_accounts(user_id, logged_in_only=True)
        if accounts:
            db.update_account_settings(accounts[0]["id"], time_interval=seconds)

        if seconds < 60:
            time_display = f"{seconds} seconds"
        elif seconds < 3600:
            time_display = f"{seconds // 60} minute(s)"
        else:
            time_display = f"{seconds // 3600} hour(s)"

        result_text = f"""
<b>œ… ᴢ´›ɴªᴢ´ᴢ´‡ sᴢ´‡ᴢ´›</b>

±ï¸ Interval set to: <b>{time_display}</b>
"""

        await send_new_message(query, result_text, advertising_menu_keyboard())
    except ValueError:
        await send_new_message(
            query,
            "<b>Œ Invalid time value</b>",
            time_keyboard()
        )


async def set_single_mode(query, user_id):
    db.update_user(user_id, use_multiple_accounts=False)

    accounts = db.get_accounts(user_id, logged_in_only=True)

    if not accounts:
        force_sub_settings = db.get_force_sub_settings()
        force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False
        await send_new_message(
            query,
            "<b>Œ No logged in accounts</b>\n\n<i>Please add an account first.</i>",
            settings_keyboard(False, False, False, False, force_sub_enabled, db.is_owner(user_id))
        )
        return

    if len(accounts) == 1:
        result_text = """
<b>œ… sɴªɴ´ɴ¢ʟᴢ´‡ ᴢ´ᴢ´ᴢ´…ᴢ´‡ ᴢ´€ᴢ´„ᴢ´›ɴªᴢ´ ᴢ´€ᴢ´›ᴢ´‡ᴢ´…</b>

“± Using your only account for advertising.
"""
        user = db.get_user(user_id)
        use_forward = user.get('use_forward_mode', False) if user else False
        auto_reply = user.get('auto_reply_enabled', False) if user else False
        auto_group_join = user.get('auto_group_join_enabled', False) if user else False

        force_sub_settings = db.get_force_sub_settings()
        force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False

        await send_new_message(query, result_text, settings_keyboard(False, use_forward, auto_reply, auto_group_join, force_sub_enabled, db.is_owner(user_id)))
    else:
        await send_new_message(
            query,
            "<b>“± Select an account for single mode:</b>",
            single_account_selection_keyboard(accounts)
        )


async def set_multiple_mode(query, user_id, context):
    accounts = db.get_accounts(user_id, logged_in_only=True)

    if len(accounts) < 2:
        force_sub_settings = db.get_force_sub_settings()
        force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False
        await send_new_message(
            query,
            "<b>Œ Need at least 2 accounts</b>\n\n<i>Add more accounts for multiple mode.</i>",
            settings_keyboard(False, False, False, False, force_sub_enabled, db.is_owner(user_id))
        )
        return

    context.user_data["selected_accounts"] = []

    await send_new_message(
        query,
        "<b>“±“± Select accounts for multiple mode:</b>",
        account_selection_keyboard(accounts, [])
    )


async def toggle_account_selection(query, user_id, account_id, context):
    selected = context.user_data.get("selected_accounts", [])

    if account_id in selected:
        selected.remove(account_id)
    else:
        selected.append(account_id)

    context.user_data["selected_accounts"] = selected
    accounts = db.get_accounts(user_id, logged_in_only=True)

    await send_new_message(
        query,
        f"<b>“±“± Selected: {len(selected)} accounts</b>",
        account_selection_keyboard(accounts, selected)
    )


async def show_account_selection(query, user_id, page, context):
    accounts = db.get_accounts(user_id, logged_in_only=True)
    selected = context.user_data.get("selected_accounts", [])

    await send_new_message(
        query,
        f"<b>“±“± Selected: {len(selected)} accounts</b>",
        account_selection_keyboard(accounts, selected, page)
    )


async def confirm_account_selection(query, user_id, context):
    selected = context.user_data.get("selected_accounts", [])

    if len(selected) < 2:
        await send_new_message(
            query,
            "<b>Œ Select at least 2 accounts</b>",
            account_selection_keyboard(db.get_accounts(user_id, logged_in_only=True), selected)
        )
        return

    db.update_user(user_id, use_multiple_accounts=True, selected_accounts=selected)

    user = db.get_user(user_id)
    use_forward = user.get('use_forward_mode', False) if user else False
    auto_reply = user.get('auto_reply_enabled', False) if user else False
    auto_group_join = user.get('auto_group_join_enabled', False) if user else False

    result_text = f"""
<b>œ… ᴢ´ᴢ´œʟᴢ´›ɴªᴢ´˜ʟᴢ´‡ ᴢ´ᴢ´ᴢ´…ᴢ´‡ ᴢ´€ᴢ´„ᴢ´›ɴªᴢ´ ᴢ´€ᴢ´›ᴢ´‡ᴢ´…</b>

“±“± Using <b>{len(selected)}</b> accounts for advertising.
"""

    force_sub_settings = db.get_force_sub_settings()
    force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False

    await send_new_message(query, result_text, settings_keyboard(True, use_forward, auto_reply, auto_group_join, force_sub_enabled, db.is_owner(user_id)))


async def show_my_accounts(query, user_id, page=0):
    accounts = db.get_accounts(user_id)

    if not accounts:
        await send_new_message(
            query,
            "<b>“‹ No accounts</b>\n\n<i>Add an account to get started.</i>",
            accounts_menu_keyboard()
        )
        return

    await send_new_message(
        query,
        f"<b>“‹ Your Accounts ({len(accounts)})</b>",
        accounts_keyboard(accounts, page)
    )


async def select_single_account(query, user_id, account_id):
    db.update_user(user_id, use_multiple_accounts=False, selected_single_account=account_id)

    account = db.get_account(account_id)
    display_name = account.get('account_first_name', 'Unknown') if account else 'Unknown'

    user = db.get_user(user_id)
    use_forward = user.get('use_forward_mode', False) if user else False
    auto_reply = user.get('auto_reply_enabled', False) if user else False
    auto_group_join = user.get('auto_group_join_enabled', False) if user else False

    result_text = f"""
<b>œ… ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› sᴢ´‡ʟᴢ´‡ᴢ´„ᴢ´›ᴢ´‡ᴢ´…</b>

“± Using: <b>{display_name}</b>
"""

    force_sub_settings = db.get_force_sub_settings()
    force_sub_enabled = force_sub_settings.get('enabled', False) if force_sub_settings else False

    await send_new_message(query, result_text, settings_keyboard(False, use_forward, auto_reply, auto_group_join, force_sub_enabled, db.is_owner(user_id)))


async def show_single_account_page(query, user_id, page):
    accounts = db.get_accounts(user_id, logged_in_only=True)

    await send_new_message(
        query,
        "<b>“± Select an account:</b>",
        single_account_selection_keyboard(accounts, page)
    )


async def start_advertising(query, user_id, context):
    user = db.get_user(user_id)

    if not user:
        await send_new_message(
            query,
            "<b>Œ Error: User not found</b>",
            advertising_menu_keyboard()
        )
        return

    # Check if logs channel is set (required)
    logs_channel = db.get_logs_channel(user_id)
    if not logs_channel or not logs_channel.get('verified'):
        await send_new_message(
            query,
            "<b>š ï¸ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ʙ€ᴢ´‡ǫ«ᴢ´œɴªʙ€ᴢ´‡ᴢ´…</b>\n\n"
            "<blockquote>ʙᴢ´ᴢ´œ ᴢ´ᴢ´œsᴢ´› sᴢ´‡ᴢ´› ᴢ´œᴢ´˜ ᴢ´€ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ʙ™ᴢ´‡ғ“ᴢ´ʙ€ᴢ´‡ sᴢ´›ᴢ´€ʙ€ᴢ´›ɴªɴ´ɴ¢ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢.</blockquote>\n\n"
            "<b>ʜᴢ´ᴢ´¡ ᴢ´›ᴢ´ sᴢ´‡ᴢ´› ᴢ´œᴢ´˜:</b>\n"
            "1. ᴢ´„ʙ€ᴢ´‡ᴢ´€ᴢ´›ᴢ´‡ ᴢ´€ ɴ´ᴢ´‡ᴢ´¡ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ\n"
            "2. ᴢ´€ᴢ´…ᴢ´… ᴢ´›ʜɴªs ʙ™ᴢ´ᴢ´› ᴢ´€s ᴢ´€ᴢ´…ᴢ´ɴªɴ´\n"
            "3. ɴ¢ᴢ´ ᴢ´›ᴢ´ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s †’ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ\n"
            "4. sᴢ´‡ɴ´ᴢ´… ᴢ´›ʜᴢ´‡ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ɴªᴢ´… ᴢ´ʙ€ ʟɴªɴ´ᴢ´‹",
            back_to_menu_keyboard()
        )
        return

    ad_text = user.get('ad_text')
    use_forward = user.get('use_forward_mode', False)
    use_multiple = user.get('use_multiple_accounts', False)
    time_interval = user.get('time_interval', 60)
    target_mode = user.get('target_mode', 'all')

    accounts = db.get_accounts(user_id, logged_in_only=True)

    if not accounts:
        await send_new_message(
            query,
            "<b>Œ No logged in accounts</b>\n\n<i>Please add and login to an account first.</i>",
            advertising_menu_keyboard()
        )
        return

    if not use_forward and not ad_text:
        await send_new_message(
            query,
            "<b>Œ No ad text set</b>\n\n<i>Please set your ad text first or enable forward mode to forward from Saved Messages.</i>",
            advertising_menu_keyboard()
        )
        return

    if use_multiple:
        selected_accounts = user.get('selected_accounts', [])
        if not selected_accounts:
            selected_accounts = [str(acc["_id"]) for acc in accounts]
        active_accounts = [acc for acc in accounts if str(acc["_id"]) in selected_accounts]
    else:
        single_account = user.get('selected_single_account')
        if single_account:
            active_accounts = [acc for acc in accounts if str(acc["_id"]) == single_account]
        else:
            active_accounts = [accounts[0]] if accounts else []

    if not active_accounts:
        await send_new_message(
            query,
            "<b>Œ No accounts selected</b>\n\n<i>Please select accounts in settings.</i>",
            advertising_menu_keyboard()
        )
        return

    if target_mode == "selected":
        target_groups = db.get_target_groups(user_id)
        if not target_groups:
            await send_new_message(
                query,
                "<b>Œ No target groups selected</b>\n\n<i>Please add target groups in Targeting settings.</i>",
                advertising_menu_keyboard()
            )
            return

    context.user_data["advertising_active"] = True

    mode_text = "Forward from Saved Messages" if use_forward else "Direct Send"
    target_text = f"Selected ({len(target_groups) if target_mode == 'selected' else 0} groups)" if target_mode == "selected" else "All Groups"

    start_text = f"""
<b>š€ ᴢ´€ᴢ´…ᴢ´ ᴢ´‡ʙ€ᴢ´›ɴªsɴªɴ´ɴ¢ sᴢ´›ᴢ´€ʙ€ᴢ´›ᴢ´‡ᴢ´…</b>

“± <b>Accounts:</b> <code>{len(active_accounts)}</code>
œ‰ï¸ <b>Mode:</b> <code>{mode_text}</code>
Ž¯ <b>Target:</b> <code>{target_text}</code>
±ï¸ <b>Interval:</b> <code>{time_interval}s</code>

<i>Campaign is running...</i>
"""

    await send_new_message(query, start_text, advertising_menu_keyboard())

    asyncio.create_task(run_advertising_campaign(user_id, active_accounts, ad_text, time_interval, use_forward, target_mode, context))


async def run_advertising_campaign(user_id, accounts, ad_text, delay, use_forward, target_mode, context):
    try:
        logs_channel = db.get_logs_channel(user_id)
        logs_channel_id = logs_channel.get('channel_id') if logs_channel else None

        while context.user_data.get("advertising_active", False):
            for account in accounts:
                if not context.user_data.get("advertising_active", False):
                    break

                account_id = str(account["_id"])

                if target_mode == "selected":
                    target_groups = db.get_target_groups(user_id)
                    result = await telethon_handler.broadcast_to_target_groups(
                        account_id, target_groups, ad_text, delay, use_forward, logs_channel_id
                    )
                else:
                    result = await telethon_handler.broadcast_message(
                        account_id, ad_text, delay, use_forward, logs_channel_id
                    )

                if not context.user_data.get("advertising_active", False):
                    break

                await asyncio.sleep(delay)
    except Exception as e:
        logger.error(f"Advertising campaign error: {e}")


async def handle_otp_input(query, user_id, data, context):
    state = user_states.get(user_id, {})

    if state.get("state") != "awaiting_otp":
        return

    otp_code = state.get("data", {}).get("otp_code", "")

    action = data.replace("otp_", "")

    if action == "cancel":
        if user_id in user_states:
            del user_states[user_id]
        await send_new_message(query, "<b>Œ Login cancelled</b>", main_menu_keyboard())
        return

    if action == "delete":
        otp_code = otp_code[:-1]
        user_states[user_id]["data"]["otp_code"] = otp_code

        display = otp_code + "" * (5 - len(otp_code))
        await send_new_message(
            query,
            f"<b>” Enter OTP Code</b>\n\n<code>{display}</code>",
            otp_keyboard()
        )
        return

    if action == "submit":
        if len(otp_code) < 5:
            await query.answer("Please enter at least 5 digits", show_alert=True)
            return

        await send_new_message(query, "<b>³ Verifying code...</b>", None)

        account_data = state.get("data", {})
        api_id = account_data.get("api_id")
        api_hash = account_data.get("api_hash")
        phone = account_data.get("phone")
        phone_code_hash = account_data.get("phone_code_hash")
        session_string = account_data.get("session_string")

        result = await telethon_handler.verify_code(
            api_id, api_hash, phone, otp_code, phone_code_hash, session_string
        )

        if result["success"]:
            from PyToday.encryption import encrypt_data

            account = db.create_account(
                user_id, phone,
                encrypt_data(str(api_id)),
                encrypt_data(api_hash)
            )

            db.update_account(
                account["_id"],
                session_string=encrypt_data(result["session_string"]),
                is_logged_in=True
            )

            info = await telethon_handler.get_account_info(api_id, api_hash, result["session_string"])
            if info["success"]:
                db.update_account(
                    account["_id"],
                    account_first_name=info["first_name"],
                    account_last_name=info["last_name"],
                    account_username=info["username"]
                )

            if user_id in user_states:
                del user_states[user_id]

            await send_new_message(
                query,
                "<b>œ… ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› ᴢ´€ᴢ´…ᴢ´…ᴢ´‡ᴢ´…</b>\n\n<i>Account logged in successfully!</i>",
                main_menu_keyboard()
            )
        elif result.get("requires_2fa"):
            user_states[user_id]["state"] = "awaiting_2fa"
            user_states[user_id]["data"]["session_string"] = result["session_string"]

            await send_new_message(
                query,
                "<b>” 2FA Required</b>\n\n<i>Send your 2FA password:</i>",
                twofa_keyboard()
            )
        else:
            await send_new_message(
                query,
                f"<b>Œ Error:</b> {result.get('error', 'Unknown error')}",
                otp_keyboard()
            )
        return

    if action.isdigit():
        if len(otp_code) < 6:
            otp_code += action
            user_states[user_id]["data"]["otp_code"] = otp_code

        display = otp_code + "" * (5 - len(otp_code))
        await send_new_message(
            query,
            f"<b>” Enter OTP Code</b>\n\n<code>{display}</code>",
            otp_keyboard()
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    state = user_states.get(user_id, {})
    current_state = state.get("state")

    if not current_state:
        return

    if current_state == "awaiting_api_id":
        try:
            api_id = int(text)
            user_states[user_id]["data"]["api_id"] = api_id
            user_states[user_id]["state"] = "awaiting_api_hash"

            await update.message.reply_text(
                "<b>Step 2/4:</b> Send your <b>API Hash</b>",
                parse_mode="HTML"
            )
        except ValueError:
            await update.message.reply_text(
                "<b>Œ Invalid API ID</b>\n\nPlease send a valid number.",
                parse_mode="HTML"
            )

    elif current_state == "awaiting_api_hash":
        user_states[user_id]["data"]["api_hash"] = text
        user_states[user_id]["state"] = "awaiting_phone"

        await update.message.reply_text(
            "<b>Step 3/4:</b> Send your <b>Phone Number</b>\n\nFormat: +1234567890",
            parse_mode="HTML"
        )

    elif current_state == "awaiting_phone":
        phone = text.strip()
        if not phone.startswith("+"):
            phone = "+" + phone

        user_states[user_id]["data"]["phone"] = phone

        await update.message.reply_text(
            "<b>³ Sending OTP...</b>",
            parse_mode="HTML"
        )

        api_id = user_states[user_id]["data"]["api_id"]
        api_hash = user_states[user_id]["data"]["api_hash"]

        result = await telethon_handler.send_code(api_id, api_hash, phone)

        if result["success"]:
            user_states[user_id]["state"] = "awaiting_otp"
            user_states[user_id]["data"]["phone_code_hash"] = result["phone_code_hash"]
            user_states[user_id]["data"]["session_string"] = result["session_string"]
            user_states[user_id]["data"]["otp_code"] = ""

            await update.message.reply_text(
                "<b>” Enter OTP Code</b>\n\n<code></code>",
                parse_mode="HTML",
                reply_markup=otp_keyboard()
            )
        else:
            await update.message.reply_text(
                f"<b>Œ Error:</b> {result.get('error', 'Unknown error')}",
                parse_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
            if user_id in user_states:
                del user_states[user_id]

    elif current_state == "awaiting_2fa":
        password = text

        await update.message.reply_text(
            "<b>³ Verifying 2FA...</b>",
            parse_mode="HTML"
        )

        api_id = user_states[user_id]["data"]["api_id"]
        api_hash = user_states[user_id]["data"]["api_hash"]
        phone = user_states[user_id]["data"]["phone"]
        session_string = user_states[user_id]["data"]["session_string"]

        result = await telethon_handler.verify_2fa_password(api_id, api_hash, password, session_string)

        if result["success"]:
            from PyToday.encryption import encrypt_data

            account = db.create_account(
                user_id, phone,
                encrypt_data(str(api_id)),
                encrypt_data(api_hash)
            )

            db.update_account(
                account["_id"],
                session_string=encrypt_data(result["session_string"]),
                is_logged_in=True
            )

            info = await telethon_handler.get_account_info(api_id, api_hash, result["session_string"])
            if info["success"]:
                db.update_account(
                    account["_id"],
                    account_first_name=info["first_name"],
                    account_last_name=info["last_name"],
                    account_username=info["username"]
                )

            if user_id in user_states:
                del user_states[user_id]

            await update.message.reply_text(
                "<b>œ… ᴢ´€ᴢ´„ᴢ´„ᴢ´ᴢ´œɴ´ᴢ´› ᴢ´€ᴢ´…ᴢ´…ᴢ´‡ᴢ´…</b>\n\n<i>Account logged in successfully!</i>",
                parse_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                f"<b>Œ Error:</b> {result.get('error', 'Unknown error')}",
                parse_mode="HTML",
                reply_markup=twofa_keyboard()
            )

    elif current_state == "awaiting_ad_text":
        db.update_user(user_id, ad_text=text)

        if user_id in user_states:
            del user_states[user_id]

        await update.message.reply_text(
            "<b>œ… ᴢ´€ᴢ´… ᴢ´›ᴢ´‡xᴢ´› sᴢ´€ᴢ´ ᴢ´‡ᴢ´…</b>\n\n<i>Your ad text has been saved.</i>",
            parse_mode="HTML",
            reply_markup=ad_text_menu_keyboard()
        )

    elif current_state == "awaiting_reply_text":
        db.update_user(user_id, auto_reply_text=text)

        user = db.get_user(user_id)
        auto_reply = user.get('auto_reply_enabled', False) if user else False

        if auto_reply:
            await telethon_handler.start_all_auto_reply_listeners(user_id, text)

        if user_id in user_states:
            del user_states[user_id]

        await update.message.reply_text(
            "<b>œ… ʙ€ᴢ´‡ᴢ´˜ʟʙ ᴢ´›ᴢ´‡xᴢ´› sᴢ´€ᴢ´ ᴢ´‡ᴢ´…</b>\n\n<i>Your custom auto-reply text has been saved.</i>",
            parse_mode="HTML",
            reply_markup=auto_reply_settings_keyboard(auto_reply)
        )

    elif current_state == "awaiting_custom_time":
        try:
            seconds = int(text)
            if seconds < 10:
                await update.message.reply_text(
                    "<b>Œ Time must be at least 10 seconds</b>",
                    parse_mode="HTML"
                )
                return

            db.update_user(user_id, time_interval=seconds)

            if user_id in user_states:
                del user_states[user_id]

            await update.message.reply_text(
                f"<b>œ… Time set to {seconds} seconds</b>",
                parse_mode="HTML",
                reply_markup=advertising_menu_keyboard()
            )
        except ValueError:
            await update.message.reply_text(
                "<b>Œ Please send a valid number</b>",
                parse_mode="HTML"
            )

    elif current_state == "awaiting_accset_interval":
        try:
            seconds = int(text)
            if seconds < 10:
                await update.message.reply_text("<b>❌ Time must be at least 10 seconds</b>", parse_mode="HTML")
                return
            account_id = user_states[user_id].get("account_id")
            db.update_account_settings(account_id, {"time_interval": seconds})
            if user_id in user_states:
                del user_states[user_id]
            await update.message.reply_text(f"<b>✅ Interval set to {seconds} seconds</b>", parse_mode="HTML")
            await cb_account_settings(update, account_id, user_id)
        except ValueError:
            await update.message.reply_text("<b>❌ Please send a valid number</b>", parse_mode="HTML")

    elif current_state == "awaiting_accset_gap":
        try:
            seconds = int(text)
            account_id = user_states[user_id].get("account_id")
            db.update_account_settings(account_id, {"gap_seconds": seconds})
            if user_id in user_states:
                del user_states[user_id]
            await update.message.reply_text(f"<b>✅ Gap set to {seconds} seconds</b>", parse_mode="HTML")
            await cb_account_settings(update, account_id, user_id)
        except ValueError:
            await update.message.reply_text("<b>❌ Please send a valid number</b>", parse_mode="HTML")

    elif current_state == "awaiting_accset_rdelay":
        try:
            seconds = int(text)
            account_id = user_states[user_id].get("account_id")
            db.update_account_settings(account_id, {"round_delay": seconds})
            if user_id in user_states:
                del user_states[user_id]
            await update.message.reply_text(f"<b>✅ Round Delay set to {seconds} seconds</b>", parse_mode="HTML")
            await cb_account_settings(update, account_id, user_id)
        except ValueError:
            await update.message.reply_text("<b>❌ Please send a valid number</b>", parse_mode="HTML")

    elif current_state == "awaiting_target_group_id":
        try:
            group_id = int(text.strip().replace("-100", "-100"))

            added = db.add_target_group(user_id, group_id, f"Group {group_id}")

            if user_id in user_states:
                del user_states[user_id]

            if added:
                await update.message.reply_text(
                    f"<b>œ… Group added</b>\n\nGroup ID: <code>{group_id}</code>",
                    parse_mode="HTML",
                    reply_markup=selected_groups_keyboard()
                )
            else:
                await update.message.reply_text(
                    "<b>š ï¸ Group already in list</b>",
                    parse_mode="HTML",
                    reply_markup=selected_groups_keyboard()
                )
        except ValueError:
            await update.message.reply_text(
                "<b>Œ Invalid Group ID</b>\n\nPlease send a valid number.",
                parse_mode="HTML"
            )

    elif current_state == "awaiting_force_channel":
        channel_input = text.strip()

        # Extract channel ID from input
        channel_id = None
        if channel_input.startswith('-100'):
            try:
                channel_id = int(channel_input)
            except ValueError:
                pass
        elif channel_input.lstrip('-').isdigit():
            try:
                channel_id = int(channel_input)
            except ValueError:
                pass

        if not channel_id:
            await update.message.reply_text(
                "<b>Œ Invalid format</b>\n\n<i>Please send a valid channel ID (e.g., -1001234567890).</i>",
                parse_mode="HTML"
            )
            return

        db.update_force_sub_settings(channel_id=str(channel_id))

        if user_id in user_states:
            del user_states[user_id]

        await update.message.reply_text(
            f"<b>œ… Channel set</b>\n\nChannel ID: <code>{channel_id}</code>",
            parse_mode="HTML",
            reply_markup=force_sub_keyboard(True)
        )

    elif current_state == "awaiting_force_group":
        group_input = text.strip()

        # Extract group ID from input
        group_id = None
        if group_input.startswith('-100'):
            try:
                group_id = int(group_input)
            except ValueError:
                pass
        elif group_input.lstrip('-').isdigit():
            try:
                group_id = int(group_input)
            except ValueError:
                pass

        if not group_id:
            await update.message.reply_text(
                "<b>Œ Invalid format</b>\n\n<i>Please send a valid group ID (e.g., -1001234567890).</i>",
                parse_mode="HTML"
            )
            return

        db.update_force_sub_settings(group_id=str(group_id))

        if user_id in user_states:
            del user_states[user_id]

        await update.message.reply_text(
            f"<b>œ… Group set</b>\n\nGroup ID: <code>{group_id}</code>",
            parse_mode="HTML",
            reply_markup=force_sub_keyboard(True)
        )

    elif current_state == "awaiting_logs_channel":
        channel_input = text.strip()

        # Extract channel ID from input - FIXED
        channel_id = None
        channel_link = None

        # Handle different input formats
        if channel_input.startswith('-100'):
            # Format: -1001234567890
            try:
                # Validate it's a proper number
                test_id = int(channel_input)
                channel_id = str(test_id)
                logger.info(f"Channel ID received: {channel_id}")
            except ValueError:
                logger.error(f"Invalid channel ID format: {channel_input}")
                pass
        elif channel_input.startswith('@'):
            # Format: @channelusername
            try:
                from telegram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                chat = await bot.get_chat(channel_input)
                channel_id = str(chat.id)
                logger.info(f"Channel resolved from username: {channel_id}")
            except Exception as e:
                logger.error(f"Error getting channel from username: {e}")
        elif channel_input.lstrip('-').isdigit():
            # Format: 1234567890 or -1234567890 (add -100 prefix if needed)
            try:
                num = int(channel_input)
                # If it's a positive number, add -100 prefix
                if num > 0:
                    channel_id = f"-100{channel_input}"
                else:
                    channel_id = channel_input
                logger.info(f"Channel ID converted: {channel_id}")
            except ValueError:
                logger.error(f"Invalid number format: {channel_input}")
                pass
        elif channel_input.startswith('https://t.me/'):
            # Format: https://t.me/channelusername
            channel_link = channel_input
            try:
                from telegram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                username = channel_input.replace('https://t.me/', '').split('/')[0]
                chat = await bot.get_chat(f"@{username}")
                channel_id = str(chat.id)
                logger.info(f"Channel resolved from link: {channel_id}")
            except Exception as e:
                logger.error(f"Error getting channel from link: {e}")

        if not channel_id:
            await update.message.reply_text(
                "<b>Œ Invalid format</b>\n\n"
                "<i>Please send a valid channel ID or link.</i>\n\n"
                "<b>Supported formats:</b>\n"
                "€¢ <code>-1001234567890</code> (Channel ID)\n"
                "€¢ <code>@channelusername</code> (Username)\n"
                "€¢ <code>https://t.me/channelusername</code> (Link)\n\n"
                "<b>How to get Channel ID:</b>\n"
                "1. Forward a message from your channel to @userinfobot\n"
                "2. Copy the ID and send it here",
                parse_mode="HTML"
            )
            return

        # Validate channel ID format
        try:
            int(channel_id)
        except ValueError:
            await update.message.reply_text(
                "<b>Œ Invalid channel ID</b>\n\n"
                "<i>The channel ID format is incorrect.</i>\n\n"
                "<b>Please try again with a valid format:</b>\n"
                "€¢ <code>-1001234567890</code>\n"
                "€¢ <code>@channelusername</code>",
                parse_mode="HTML"
            )
            return

        # Store the channel - FIXED
        try:
            db.set_logs_channel(user_id, channel_id, channel_link)
            logger.info(f"Logs channel set for user {user_id}: {channel_id}")
        except Exception as e:
            logger.error(f"Error saving logs channel: {e}")
            await update.message.reply_text(
                "<b>Œ Error saving channel</b>\n\n"
                "<i>Please try again later.</i>",
                parse_mode="HTML"
            )
            return

        if user_id in user_states:
            del user_states[user_id]

        await update.message.reply_text(
            "<b>œ… ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ sᴢ´‡ᴢ´› sᴢ´œᴢ´„ᴢ´„ᴢ´‡ssғ“ᴢ´œʟʟʙ</b>\n\n"
            f"“‹ <b>Channel ID:</b> <code>{channel_id}</code>\n\n"
            "<i>Please verify that you have:</i>\n"
            "1. Added this bot as admin to the channel\n"
            "2. Given the bot permission to send messages\n\n"
            "Click <b>'†» ᴢ´ ᴢ´‡ʙ€ɴªғ“ʙ'</b> to check permissions.",
            parse_mode="HTML",
            reply_markup=logs_channel_keyboard(has_channel=True, verified=False)
        )

    elif current_state == "awaiting_broadcast":
        # Admin broadcast via callback
        if user_id in user_states:
            del user_states[user_id]


# Admin Panel Functions
async def show_admin_stats(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    total_users = db.get_users_count()
    all_users = db.get_all_users()

    # Get total accounts via Supabase
    try:
        total_accounts = db.count_accounts() or 0
        all_accs = db.get_accounts(None) or []
        logged_in_accounts = len([a for a in all_accs if a.get('is_logged_in')])
    except Exception as e:
        logger.error(f'Error getting account stats: {e}')
        total_accounts = 0
        logged_in_accounts = 0

    stats_text = f"""
<b>ˆ ʙ™ᴢ´ᴢ´› sᴢ´›ᴢ´€ᴢ´›ɴªsᴢ´›ɴªᴢ´„s ˆ</b>

‘¥ <b>Total Users:</b> <code>{total_users}</code>
“± <b>Total Accounts:</b> <code>{total_accounts}</code>
œ… <b>Logged In:</b> <code>{logged_in_accounts}</code>

<i>Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>
"""

    await send_new_message(query, stats_text, admin_panel_keyboard())


async def prompt_admin_broadcast(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    user_states[user_id] = {"state": "awaiting_broadcast", "data": {}}

    prompt_text = """
<b>ˆ ʙ™ʙ€ᴢ´ᴢ´€ᴢ´…ᴢ´„ᴢ´€sᴢ´›</b>

<i>Send the message you want to broadcast to all users:</i>

<b>Supported formats:</b>
€¢ Text
€¢ Photo (with caption)
€¢ Video (with caption)
€¢ Document

Or send /cancel to cancel.
"""

    await send_new_message(query, prompt_text, back_to_menu_keyboard())


async def show_admin_users(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    all_users = db.get_all_users()

    users_text = f"""
<b>ˆ ᴢ´œsᴢ´‡ʙ€s ʟɴªsᴢ´› ˆ</b>

<b>Total Users:</b> <code>{len(all_users)}</code>

<b>Recent Users:</b>
"""

    # Show last 10 users
    for user in all_users[-10:]:
        user_id = user.get('_id', 'N/A')
        first_name = user.get('first_name', 'N/A')
        username = user.get('username', 'N/A')
        users_text += f"\n€¢ <code>{user_id}</code> - {first_name}"
        if username:
            users_text += f" (@{username})"

    await send_new_message(query, users_text, admin_panel_keyboard())


async def show_ban_menu(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    ban_text = """
<b>ˆ ʙ™ᴢ´€ɴ´/ᴢ´œɴ´ʙ™ᴢ´€ɴ´ ᴢ´œsᴢ´‡ʙ€s ˆ</b>

<i>To ban or unban a user, use the commands:</i>

<code>/ban user_id</code> - Ban a user
<code>/unban user_id</code> - Unban a user

<i>Feature coming soon...</i>
"""

    await send_new_message(query, ban_text, admin_panel_keyboard())


# Force Sub Functions (Admin only)
async def show_force_sub_menu(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    settings = db.get_force_sub_settings()
    enabled = settings.get('enabled', False) if settings else False

    menu_text = """
<b>Š— ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ sᴢ´œʙ™ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<i>Manage force subscription settings here.</i>

<b>How to set up:</b>
1. Get channel/group ID from @userinfobot
2. Set the IDs below
3. Enable force sub
"""
    await send_new_message(query, menu_text, force_sub_keyboard(enabled))


async def toggle_force_sub(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    settings = db.get_force_sub_settings()
    current = settings.get('enabled', False) if settings else False
    new_state = not current

    db.update_force_sub_settings(enabled=new_state)

    status = "Ÿ¢ ON" if new_state else "”´ OFF"
    result_text = f"""
<b>Š— ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ sᴢ´œʙ™</b>

Status: <b>{status}</b>
"""
    await send_new_message(query, result_text, force_sub_keyboard(new_state))


async def prompt_set_force_channel(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    user_states[user_id] = {"state": "awaiting_force_channel"}

    prompt_text = """
<b>ˆ sᴢ´‡ᴢ´› ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ</b>

<i>Send the channel ID:</i>

<b>How to get Channel ID:</b>
1. Forward a message from your channel to @userinfobot
2. Copy the ID (starts with -100)
3. Send it here

<b>Example:</b>
<code>-1001234567890</code>
"""
    await send_new_message(query, prompt_text, back_to_menu_keyboard())


async def prompt_set_force_group(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    user_states[user_id] = {"state": "awaiting_force_group"}

    prompt_text = """
<b>‰ sᴢ´‡ᴢ´› ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ ɴ¢ʙ€ᴢ´ᴢ´œᴢ´˜</b>

<i>Send the group ID:</i>

<b>How to get Group ID:</b>
1. Forward a message from your group to @userinfobot
2. Copy the ID (starts with -100)
3. Send it here

<b>Example:</b>
<code>-1001234567890</code>
"""
    await send_new_message(query, prompt_text, back_to_menu_keyboard())


async def view_force_sub_settings(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("š ï¸ Only admin can access this!", show_alert=True)
        return

    settings = db.get_force_sub_settings()

    if not settings:
        await send_new_message(
            query,
            "<b>Œ No settings found</b>\n\n<i>Force sub is not configured yet.</i>",
            force_sub_keyboard(False)
        )
        return

    enabled = settings.get('enabled', False)
    channel_id = settings.get('channel_id', 'Not set')
    group_id = settings.get('group_id', 'Not set')

    status = "Ÿ¢ ON" if enabled else "”´ OFF"

    view_text = f"""
<b> ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ sᴢ´œʙ™ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<b>Status:</b> {status}
<b>Channel ID:</b> <code>{channel_id}</code>
<b>Group ID:</b> <code>{group_id}</code>
"""
    await send_new_message(query, view_text, force_sub_keyboard(enabled))


async def check_force_sub_callback(query, user_id, context):
    """Check if user has joined required channels/groups"""
    is_joined = await check_force_sub_required(user_id, context)

    if is_joined:
        await query.answer("œ… You have joined all required channels!", show_alert=True)
        await show_main_menu(query, context)
    else:
        await query.answer("š ï¸ Please join all required channels/groups!", show_alert=True)
        await send_force_sub_message(query, context)


# Logs Channel Functions
async def show_logs_channel_menu(query, user_id):
    logs_channel = db.get_logs_channel(user_id)

    if logs_channel:
        has_channel = True
        verified = logs_channel.get('verified', False)
    else:
        has_channel = False
        verified = False

    menu_text = """
<b>‰ ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<i>Setup a channel to receive logs of all sent messages.</i>

<b>How to set up:</b>
1. Create a new channel
2. Add this bot as admin with post permissions
3. Send the channel ID or link here

<b>Required for advertising!</b>
"""

    await send_new_message(query, menu_text, logs_channel_keyboard(has_channel, verified))


async def prompt_set_logs_channel(query, user_id):
    user_states[user_id] = {"state": "awaiting_logs_channel"}

    prompt_text = """
<b>ï¼‹ sᴢ´‡ᴢ´› ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ</b>

<i>Send your channel ID or link:</i>

<b>How to get Channel ID:</b>
1. Forward a message from your channel to @userinfobot
2. Copy the ID (starts with -100)
3. Send it here

<b>Examples:</b>
<code>-1001234567890</code>
or
<code>https://t.me/yourchannel</code>
"""
    await send_new_message(query, prompt_text, back_to_settings_keyboard())


async def verify_logs_channel_callback(query, user_id):
    """Verify logs channel permissions - FIXED"""
    logs_channel = db.get_logs_channel(user_id)

    if not logs_channel:
        await query.answer("Œ No logs channel set!", show_alert=True)
        return

    channel_id = logs_channel.get('channel_id')
    
    if not channel_id:
        await query.answer("Œ Channel ID not found!", show_alert=True)
        return

    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)

        # Try to send a test message
        test_msg = await bot.send_message(
            int(channel_id),
            "<b>œ… Logs channel verified!</b>\n\n<i>This channel will receive logs of all advertising activities.</i>",
            parse_mode="HTML"
        )

        # If successful, mark as verified
        db.verify_logs_channel(user_id)

        await query.answer("œ… Channel verified successfully!", show_alert=True)
        await send_new_message(
            query,
            "<b>œ… ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ᴢ´ ᴢ´‡ʙ€ɴªғ“ɴªᴢ´‡ᴢ´…</b>\n\n<i>Your logs channel is now active. All advertising logs will be sent here.</i>",
            logs_channel_keyboard(has_channel=True, verified=True)
        )
    except Exception as e:
        logger.error(f"Error verifying logs channel: {e}")
        await query.answer("Œ Failed to verify channel. Make sure bot is admin with post permissions.", show_alert=True)
        await send_new_message(
            query,
            "<b>Œ ᴢ´ ᴢ´‡ʙ€ɴªғ“ɴªᴢ´„ᴢ´€ᴢ´›ɴªᴢ´ɴ´ ғ“ᴢ´€ɴªʟᴢ´‡ᴢ´…</b>\n\n<i>Please make sure:</i>\n1. Bot is added as admin to the channel\n2. Bot has permission to send messages\n3. The channel ID is correct",
            logs_channel_keyboard(has_channel=True, verified=False)
        )


async def remove_logs_channel_callback(query, user_id):
    db.delete_logs_channel(user_id)

    await query.answer("œ… Logs channel removed!", show_alert=True)
    await send_new_message(
        query,
        "<b>œ… ʟᴢ´ɴ¢s ᴢ´„ʜᴢ´€ɴ´ɴ´ᴢ´‡ʟ ʙ€ᴢ´‡ᴢ´ᴢ´ᴢ´ ᴢ´‡ᴢ´…</b>\n\n<i>You can set a new logs channel anytime.</i>",
        logs_channel_keyboard(has_channel=False, verified=False)
    )


# Force Join Functions (User-specific)
async def show_force_join_menu(query, user_id):
    status = db.get_force_join_status(user_id)
    enabled = status.get('enabled', False)

    menu_text = """
<b>Š— ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ ᴢ´Šᴢ´ɴªɴ´ sᴢ´‡ᴢ´›ᴢ´›ɴªɴ´ɴ¢s</b>

<i>When enabled, your accounts will automatically join all groups from group_mps.txt</i>
"""

    await send_new_message(query, menu_text, force_join_keyboard(enabled))


async def toggle_force_join_callback(query, user_id):
    new_status = db.toggle_force_join(user_id)

    status_text = "Ÿ¢ ON" if new_status else "”´ OFF"

    await query.answer(f"Force Join: {status_text}", show_alert=True)
    await send_new_message(
        query,
        f"<b>Š— ғ“ᴢ´ʙ€ᴢ´„ᴢ´‡ ᴢ´Šᴢ´ɴªɴ´</b>\n\nStatus: <b>{status_text}</b>",
        force_join_keyboard(new_status)
    )

