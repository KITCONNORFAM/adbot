"""
middleware.py – Role-based access control decorators / helpers.

Usage in handlers:
    from PyToday.middleware import owner_only, premium_only, not_banned

    @owner_only
    async def my_handler(update, context): ...
"""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from PyToday import database as db

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Core: ensure user record exists
# ────────────────────────────────────────────────────────────────────────────

async def ensure_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upsert user record in DB. Call at the top of every handler."""
    user = update.effective_user
    if user:
        db.create_or_update_user(user.id, user.first_name, user.username)


# ────────────────────────────────────────────────────────────────────────────
# Check helpers (inline, non-decorator)
# ────────────────────────────────────────────────────────────────────────────

def check_banned(user_id: int) -> bool:
    return db.is_banned(user_id)


def check_owner(user_id: int) -> bool:
    return db.is_owner(user_id)


def check_premium_or_above(user_id: int) -> bool:
    return db.is_premium_or_above(user_id)


def check_access(user_id: int) -> bool:
    """True if user has any elevated access (owner, premium, or trial)."""
    role = db.get_user_role(user_id)
    return role in ("owner", "premium", "trial")


# ────────────────────────────────────────────────────────────────────────────
# Decorators
# ────────────────────────────────────────────────────────────────────────────

def not_banned(func):
    """Rejects banned users before the handler fires."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        await ensure_user(update, context)
        if db.is_banned(user.id):
            if update.message:
                await update.message.reply_text("🚫 You are banned from using this bot.")
            elif update.callback_query:
                await update.callback_query.answer("🚫 You are banned.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def owner_only(func):
    """Restricts handler to Owners only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        await ensure_user(update, context)
        if db.is_banned(user.id):
            if update.message:
                await update.message.reply_text("🚫 You are banned.")
            return
        if not db.is_owner(user.id):
            if update.message:
                await update.message.reply_text("👑 This command is for Owners only.")
            elif update.callback_query:
                await update.callback_query.answer("👑 Owners only.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def premium_only(func):
    """Restricts handler to Premium users and Owners."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        await ensure_user(update, context)
        if db.is_banned(user.id):
            if update.message:
                await update.message.reply_text("🚫 You are banned.")
            return
        if not db.is_premium_or_above(user.id):
            if update.message:
                await update.message.reply_text(
                    "💎 This feature is for Premium users only.\n"
                    "Use /start to see upgrade options."
                )
            elif update.callback_query:
                await update.callback_query.answer("💎 Premium only.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def access_required(func):
    """Requires at least trial access. Prompts /start for new users."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        await ensure_user(update, context)
        if db.is_banned(user.id):
            if update.message:
                await update.message.reply_text("🚫 You are banned.")
            return
        if not check_access(user.id):
            owners = db.get_all_owners()
            owner_tags = " ".join([f"◈ @{o['username']}" if o.get("username") else f"◈ ID:{o['user_id']}" for o in owners]) or "◈ @owneruserid"
            msg = (
                f"⊘ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss @{db.get_client() and ''} ɪs ᴏɴʟʏ ғᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀs "
                f"ᴛᴏ ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴏᴡɴᴇʀs: {owner_tags}"
            )
            if update.message:
                from PyToday.keyboards import get_non_premium_keyboard
                await update.message.reply_text(msg, reply_markup=get_non_premium_keyboard(user.id))
            elif update.callback_query:
                await update.callback_query.answer("⊘ Premium access required.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def trial_single_account(func):
    """
    Middleware for account add operations.
    Blocks trial users who already have 1 logged-in account.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        role = db.get_user_role(user.id)
        if role == "trial":
            count = db.count_accounts(user.id, logged_in_only=True)
            if count >= 1:
                if update.message:
                    await update.message.reply_text(
                        "🔒 <b>Trial Restriction</b>\n\n"
                        "Trial users can only have <b>1 Telegram account</b> linked.\n"
                        "Upgrade to 💎 Premium to add unlimited accounts.",
                        parse_mode="HTML"
                    )
                elif update.callback_query:
                    await update.callback_query.answer(
                        "🔒 Trial: max 1 account. Upgrade to Premium.", show_alert=True
                    )
                return
        return await func(update, context, *args, **kwargs)
    return wrapper
