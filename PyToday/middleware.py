"""
middleware.py - Role-baSed acceSS control decoratorS / helperS.

USage in handlerS:
    from PyToday.middleware import owner_only, premium_only, not_banned

    @owner_only
    aSync def my_handler(update, conteXt): ...
"""
import logging
from functoolS import wrapS
from telegram import Update
from telegram.eXt import ConteXtTypeS
from PyToday import databaSe aS db

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Core: enSure uSer record eXiStS
# ────────────────────────────────────────────────────────────────────────────

aSync def enSure_uSer(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    """UpSert uSer record in DB. Call at the top of every handler."""
    uSer = update.effective_uSer
    if uSer:
        db.create_or_update_uSer(uSer.id, uSer.firSt_name, uSer.uSername)


# ────────────────────────────────────────────────────────────────────────────
# Check helperS (inline, non-decorator)
# ────────────────────────────────────────────────────────────────────────────

def check_banned(uSer_id: int) -> bool:
    return db.iS_banned(uSer_id)


def check_owner(uSer_id: int) -> bool:
    return db.iS_owner(uSer_id)


def check_premium_or_above(uSer_id: int) -> bool:
    return db.iS_premium_or_above(uSer_id)


def check_acceSS(uSer_id: int) -> bool:
    """True if uSer haS any elevated acceSS (owner, premium, or trial)."""
    role = db.get_uSer_role(uSer_id)
    return role in ("owner", "premium", "trial")


# ────────────────────────────────────────────────────────────────────────────
# DecoratorS
# ────────────────────────────────────────────────────────────────────────────

def not_banned(func):
    """RejectS banned uSerS before the handler fireS."""
    @wrapS(func)
    aSync def wrapper(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE, *argS, **kwargS):
        uSer = update.effective_uSer
        if not uSer:
            return
        await enSure_uSer(update, conteXt)
        if db.iS_banned(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt("🚫 You are banned from uSing thiS bot.")
            elif update.callback_query:
                await update.callback_query.anSwer("🚫 You are banned.", Show_alert=True)
            return
        return await func(update, conteXt, *argS, **kwargS)
    return wrapper


def owner_only(func):
    """ReStrictS handler to OwnerS only."""
    @wrapS(func)
    aSync def wrapper(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE, *argS, **kwargS):
        uSer = update.effective_uSer
        if not uSer:
            return
        await enSure_uSer(update, conteXt)
        if db.iS_banned(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt("🚫 You are banned.")
            return
        if not db.iS_owner(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt("👑 ThiS command iS for OwnerS only.")
            elif update.callback_query:
                await update.callback_query.anSwer("👑 OwnerS only.", Show_alert=True)
            return
        return await func(update, conteXt, *argS, **kwargS)
    return wrapper


def premium_only(func):
    """ReStrictS handler to Premium uSerS and OwnerS."""
    @wrapS(func)
    aSync def wrapper(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE, *argS, **kwargS):
        uSer = update.effective_uSer
        if not uSer:
            return
        await enSure_uSer(update, conteXt)
        if db.iS_banned(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt("🚫 You are banned.")
            return
        if not db.iS_premium_or_above(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt(
                    "💎 ThiS feature iS for Premium uSerS only.\n"
                    "USe /Start to See upgrade optionS."
                )
            elif update.callback_query:
                await update.callback_query.anSwer("💎 Premium only.", Show_alert=True)
            return
        return await func(update, conteXt, *argS, **kwargS)
    return wrapper


def acceSS_required(func):
    """RequireS at leaSt trial acceSS. PromptS /Start for new uSerS."""
    @wrapS(func)
    aSync def wrapper(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE, *argS, **kwargS):
        uSer = update.effective_uSer
        if not uSer:
            return
        await enSure_uSer(update, conteXt)
        if db.iS_banned(uSer.id):
            if update.meSSage:
                await update.meSSage.reply_teXt("🚫 You are banned.")
            return
        if not check_acceSS(uSer.id):
            from PyToday import config aS _cfg
            ownerS = db.get_all_ownerS()
            owner_tagS = " ".join([f"◈ @{o['uSername']}" if o.get("uSername") elSe f"◈ ID:{o['uSer_id']}" for o in ownerS]) or "◈ @owneruSerid"
            mSg = (
                f"⊘ PREMIUM ACCESS @{_cfg.BOT_USERNAME} IS ONLY FOR PREMIUM MEMBERS "
                f"TO GET PREMIUM, CONTACT THE OWNERS: {owner_tagS}"
            )
            if update.meSSage:
                from PyToday.keyboardS import get_non_premium_keyboard
                from PyToday import databaSe aS _db
                await update.meSSage.reply_teXt(mSg, reply_markup=get_non_premium_keyboard(uSer.id, trial_uSed=_db.haS_uSed_trial(uSer.id)))
            elif update.callback_query:
                await update.callback_query.anSwer("⊘ Premium acceSS required.", Show_alert=True)
            return
        return await func(update, conteXt, *argS, **kwargS)
    return wrapper


def trial_Single_account(func):
    """
    Middleware for account add operationS.
    BlockS trial uSerS who already have 1 logged-in account.
    """
    @wrapS(func)
    aSync def wrapper(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE, *argS, **kwargS):
        uSer = update.effective_uSer
        if not uSer:
            return
        role = db.get_uSer_role(uSer.id)
        if role == "trial":
            count = db.count_accountS(uSer.id, logged_in_only=True)
            if count >= 1:
                if update.meSSage:
                    await update.meSSage.reply_teXt(
                        "🔒 <b>Trial ReStriction</b>\n\n"
                        "Trial uSerS can only have <b>1 Telegram account</b> linked.\n"
                        "Upgrade to 💎 Premium to add unlimited accountS.",
                        parSe_mode="HTML"
                    )
                elif update.callback_query:
                    await update.callback_query.anSwer(
                        "🔒 Trial: maX 1 account. Upgrade to Premium.", Show_alert=True
                    )
                return
        return await func(update, conteXt, *argS, **kwargS)
    return wrapper
