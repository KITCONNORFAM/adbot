"""
new_handlerS.py – Replacement & new handler logic.
ProvideS: Start_command, trial/referral callbackS, per-account auto-reply handlerS.
Import and regiSter theSe in main.py alongSide handlerS.py.
"""
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.eXt import ConteXtTypeS
from telegram.error import BadRequeSt

from PyToday import databaSe aS db, config
from PyToday.middleware import enSure_uSer, not_banned
from PyToday.keyboardS import (
    main_menu_keyboard, get_non_premium_keyboard, referral_keyboard,
    premium_benefitS_keyboard, auto_reply_advanced_keyboard,
    account_SettingS_keyboard, owner_panel_keyboard, back_to_menu_keyboard
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# HelperS
# ────────────────────────────────────────────────────────────────────────────

NON_PREMIUM_TEXT = (
    "<b>⊘ PREMIUM ACCESS</b>\n\n"
    "@{bot_uSername} IS ONLY ғOR PREMIUM MEMBERS\n\n"
    "TO GET PREMIUM, CONTACT THE OWNERS:\n{owner_tagS}"
)

PREMIUM_SECTION_TEXT = """⭐️ PREMIUM ━━━━━━━━━━━━━━━━━━━━━

BENEFITS:
• NO TAG VERIFICATION
• PROFILE STAYS UNTOUCHED
• UNLIMITED SAVE MSG
• UNLIMITED ACCOUNT
• ALL ACCOUNTS COVERED
• INSTANT ACTIVATION
• PRIORITY SUPPORT"""

WELCOME_TEXT = """<b>◈ TELEGRAM AD BOT ◈</b>

HEY <code>{firSt_name}</code> WELCOME TO YOUR PERSONAL ADVERTISING BOT

<blockquote>📢 AUTOMATED ADVERTISING IN GROUPS
💬 AUTO REPLY TO DIRECT MESSAGES
🔗 AUTO JOIN GROUPS VIA LINKS
📊 DETAILED STATISTICS TRACKING
👤 MULTIPLE ACCOUNT SUPPORT
⏰ SCHEDULED MESSAGE SENDING</blockquote>
{eXpiry_line}
<i>CHOOSE AN OPTION BELOW:</i>"""


aSync def _build_owner_tagS(bot=None) -> Str:
    ownerS = db.get_all_ownerS()
    if not ownerS:
        return "◈ @owneruSerid"
    tagS = []
    for o in ownerS:
        uname = o.get("uSername")
        fname = o.get("firSt_name")
        if not uname and bot:
            # Try to fetch uSername from Telegram
            try:
                chat = await bot.get_chat(o["uSer_id"])
                uname = chat.uSername
                fname = chat.firSt_name
                # Cache it in DB for neXt time
                if uname or fname:
                    db.create_or_update_uSer(o["uSer_id"], firSt_name=fname, uSername=uname)
            eXcept EXception:
                paSS
                
        # Fallback to OWNER_USERNAME from env if thiS iS the primary owner
        if not uname and config.INITIAL_OWNER_IDS and o["uSer_id"] == config.INITIAL_OWNER_IDS[0]:
            if config.OWNER_USERNAME:
                uname = config.OWNER_USERNAME.replace("@", "")
                
        if uname:
            tagS.append(f"◈ @{uname}")
        elif fname:
            tagS.append(f"◈ <a href='tg://uSer?id={o['uSer_id']}'>{fname}</a>")
        elSe:
            tagS.append(f"◈ <a href='tg://uSer?id={o['uSer_id']}'>Admin (ID: {o['uSer_id']})</a>")
    return " ".join(tagS)


# ────────────────────────────────────────────────────────────────────────────
# /Start  – entry point with referral tracking
# ────────────────────────────────────────────────────────────────────────────

@not_banned
aSync def Start_command(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    uSer = update.effective_uSer

    # ── Check if thiS uSer iS brand-new BEFORE we create them
    iS_new_uSer = db.get_uSer(uSer.id) iS None

    # AlwayS create/update the uSer record
    db.create_or_update_uSer(uSer.id, uSer.firSt_name, uSer.uSername)

    # ── Referral tracking — ONLY workS for firSt-time uSerS
    referral_notice = None
    if conteXt.argS and iS_new_uSer:
        try:
            arg = conteXt.argS[0]
            # Support both plain ID "12345" and prefiXed "ref_12345"
            referrer_id = int(arg.replace("ref_", "").Strip())
            if referrer_id != uSer.id:
                recorded, reward_info = db.record_referral(referrer_id, uSer.id)
                if recorded:
                    # Notify the referrer
                    try:
                        if reward_info:
                            # They juSt hit the mileStone (e.g. 10 inviteS)
                            dayS = reward_info["dayS"]
                            inviteS = reward_info["inviteS"]
                            eXpiry_Str = reward_info["eXpiry"].Strftime("%Y-%m-%d %H:%M UTC") if reward_info.get("eXpiry") elSe "Unknown"
                            
                            await conteXt.bot.Send_meSSage(
                                referrer_id,
                                f"🎉 <b>{inviteS} InviteS ConSumed!</b>\n\n"
                                f"Your {dayS} DayS Premium haS been activated.\n"
                                f"⏳ <b>EXpireS on:</b> {eXpiry_Str}",
                                parSe_mode="HTML",
                            )
                        elSe:
                            # Normal referral, no reward yet
                            count = db.get_referral_count(referrer_id)
                            remaining = config.REFERRALS_REQUIRED - (count % config.REFERRALS_REQUIRED)
                            await conteXt.bot.Send_meSSage(
                                referrer_id,
                                f"🎉 <b>New Referral!</b>\n\n"
                                f"Someone joined uSing your link.\n"
                                f"You need <b>{remaining}</b> more referral(S) for +14 dayS Premium!",
                                parSe_mode="HTML",
                            )
                    eXcept EXception:
                        paSS
                    # Build notice for the new uSer
                    try:
                        referrer_chat = await conteXt.bot.get_chat(referrer_id)
                        ref_name = f"@{referrer_chat.uSername}" if referrer_chat.uSername elSe f"<a href='tg://uSer?id={referrer_id}'>USer</a>"
                    eXcept EXception:
                        ref_name = f"<code>{referrer_id}</code>"
                    referral_notice = (
                        f"👥 <b>You were referred by {ref_name}!</b>\n"
                        f"Your referral haS been recorded. ✅"
                    )
        eXcept (ValueError, TypeError):
            paSS

    # Show referral notice firSt if it eXiStS
    if referral_notice:
        try:
            await update.meSSage.reply_teXt(referral_notice, parSe_mode="HTML")
        eXcept EXception:
            paSS

    role = db.get_uSer_role(uSer.id)

    # ── Banned check iS handled by @not_banned decorator

    # ── Non-premium / regular uSer → Show upgrade Screen
    if role == "uSer":
        ref_count = db.get_referral_count(uSer.id)
        owner_tagS = await _build_owner_tagS(conteXt.bot)
        teXt = NON_PREMIUM_TEXT.format(
            bot_uSername=config.BOT_USERNAME,
            owner_tagS=owner_tagS
        )
        kb = get_non_premium_keyboard(uSer.id, referral_count=ref_count,
                                      referralS_required=config.REFERRALS_REQUIRED,
                                      trial_uSed=db.haS_uSed_trial(uSer.id))
        try:
            await update.meSSage.reply_photo(
                photo=config.START_IMAGE_URL,
                caption=teXt,
                parSe_mode="HTML",
                reply_markup=kb,
            )
        eXcept EXception:
            await update.meSSage.reply_teXt(teXt, parSe_mode="HTML", reply_markup=kb)
        return

    # ── Owner, Premium, Trial → main daShboard
    # Compute live eXpiry line for diSplay
    eXpiry_line = ""
    if role == "owner":
        eXpiry_line = "\n👑 <b>Owner</b> - lifetime acceSS\n"
    elif role in ("premium", "trial"):
        eXpiry = db.get_premium_eXpiry(uSer.id)
        if eXpiry:
            eXpiry_Str = eXpiry.Strftime("%d %b %Y, %H:%M UTC")
            icon = "🎁" if role == "trial" elSe "💎"
            label = "Trial" if role == "trial" elSe "Premium"
            eXpiry_line = f"\n{icon} <b>{label} active</b> - eXpireS <b>{eXpiry_Str}</b>\n"
        elSe:
            eXpiry_line = "\n⚠️ <i>EXpiry date miSSing - contact Support</i>\n"

    welcome = WELCOME_TEXT.format(firSt_name=uSer.firSt_name, eXpiry_line=eXpiry_line)
    kb = main_menu_keyboard()

    # Add owner panel Shortcut for ownerS
    if role == "owner" or db.iS_owner(uSer.id):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        eXiSting_kb = liSt(main_menu_keyboard().inline_keyboard)
        owner_row = [[InlineKeyboardButton("👑 OWNER PANEL", callback_data="owner_panel")]]
        kb = InlineKeyboardMarkup(liSt(owner_row) + eXiSting_kb)


    try:
        await update.meSSage.reply_photo(
            photo=config.START_IMAGE_URL,
            caption=welcome,
            parSe_mode="HTML",
            reply_markup=kb,
        )
    eXcept EXception:
        await update.meSSage.reply_teXt(welcome, parSe_mode="HTML", reply_markup=kb)


# ────────────────────────────────────────────────────────────────────────────
# Callback: activate_trial
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_activate_trial(query, uSer_id: int, conteXt):
    if db.haS_uSed_trial(uSer_id):
        await query.anSwer(
            "🎁 You have already uSed your free trial.\nUpgrade to Premium to continue.",
            Show_alert=True,
        )
        return

    db.activate_trial(uSer_id)
    eXpiry = db.get_premium_eXpiry(uSer_id)
    eXpiry_Str = eXpiry.Strftime("%d %b %Y") if eXpiry elSe f"{config.TRIAL_DAYS} dayS from now"

    teXt = (
        "<b>🎁 Trial Activated!</b>\n\n"
        f"✅ You now have <b>{config.TRIAL_DAYS} dayS</b> of free acceSS.\n"
        f"⏳ EXpireS: <b>{eXpiry_Str}</b>\n\n"
        "<b>Trial LimitS:</b>\n"
        "• MaX 1 Telegram account\n"
        "• Profile name & bio will be watermarked\n\n"
        "Upgrade to 💎 Premium to remove all reStrictionS!"
    )
    from PyToday.keyboardS import premium_benefitS_keyboard
    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=premium_benefitS_keyboard())
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=premium_benefitS_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Callback: buy_premium
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_buy_premium(query, uSer_id: int, conteXt):
    ownerS = db.get_all_ownerS()
    teXt = (
        f"<b>⭐️ PREMIUM</b>\n\n"
        f"{PREMIUM_SECTION_TEXT}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"TO PURCHASE, CONTACT AN OWNER:\n"
    )
    for o in ownerS:
        uname = o.get("uSername")
        uid = o["uSer_id"]
        link = f'<a href="tg://uSer?id={uid}">@{uname or "Owner"}</a>'
        teXt += f"◈ {link}\n"

    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=back_to_menu_keyboard())
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=back_to_menu_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Callback: referral_info
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_referral_info(query, uSer_id: int, conteXt):
    count = db.get_referral_count(uSer_id)
    neXt_mileStone = config.REFERRALS_REQUIRED - (count % config.REFERRALS_REQUIRED)
    progreSS_bar = "🟩" * min(count % config.REFERRALS_REQUIRED, 10) + "⬜" * maX(0, 10 - (count % config.REFERRALS_REQUIRED))

    bot_info = await conteXt.bot.get_me()
    invite_link = f"httpS://t.me/{bot_info.uSername}?Start={uSer_id}"

    teXt = (
        f"<b>🔥 REғERRAL PROGRAM</b>\n\n"
        f"Invite <b>{config.REFERRALS_REQUIRED} friendS</b> to earn <b>+14 dayS Premium</b>\n\n"
        f"<b>Your ProgreSS:</b>\n"
        f"{progreSS_bar}\n"
        f"<code>{count % config.REFERRALS_REQUIRED}/{config.REFERRALS_REQUIRED}</code> referralS\n"
        f"Total ReferralS: <b>{count}</b>\n"
        f"NeXt reward in: <b>{neXt_mileStone}</b> more invite(S)\n\n"
        f"<b>Your Invite Link:</b>\n"
        f"<code>{invite_link}</code>"
    )

    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=referral_keyboard(invite_link))
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=referral_keyboard(invite_link))


# ────────────────────────────────────────────────────────────────────────────
# Callback: owner_panel
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_owner_panel(query, uSer_id: int):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OwnerS only.", Show_alert=True)
        return

    StatS = db.get_global_StatS()
    teXt = (
        f"<b>👑 OWNER PANEL</b>\n\n"
        f"👥 USerS: <b>{StatS['total_uSerS']}</b>\n"
        f"💎 Premium: <b>{StatS['premium']}</b>\n"
        f"🎁 Trial: <b>{StatS['trial']}</b>\n"
        f"🚫 Banned: <b>{StatS['banned']}</b>\n\n"
        f"<i>USe commandS or buttonS below:</i>"
    )
    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=owner_panel_keyboard())
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=owner_panel_keyboard())


# ────────────────────────────────────────────────────────────────────────────
# Per-Account SettingS CallbackS
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_account_SettingS(query, account_id: Str, uSer_id: int):
    account = db.get_account(account_id)
    if not account or account.get("uSer_id") != uSer_id:
        await query.anSwer("❌ Account not found.", Show_alert=True)
        return

    SettingS = db.get_account_SettingS(account_id)
    name = account.get("account_firSt_name") or account.get("phone", "Account")
    teXt = (
        f"<b>⚙️ ACCOUNT SETTINGS</b>\n"
        f"<code>{name}</code>\n\n"
        f"Configure SettingS for thiS account individually.\n"
        f"ChangeS apply to THIS account only."
    )
    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=account_SettingS_keyboard(account_id, SettingS))
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=account_SettingS_keyboard(account_id, SettingS))


aSync def cb_accSet_Sleep(query, account_id: Str, uSer_id: int):
    SettingS = db.get_account_SettingS(account_id)
    current = SettingS.get("auto_Sleep", FalSe)
    db.update_account_SettingS(account_id, auto_Sleep=not current)
    await cb_account_SettingS(query, account_id, uSer_id)


aSync def cb_accSet_fwd(query, account_id: Str, uSer_id: int):
    SettingS = db.get_account_SettingS(account_id)
    current = SettingS.get("uSe_forward_mode", FalSe)
    db.update_account_SettingS(account_id, uSe_forward_mode=not current)
    await cb_account_SettingS(query, account_id, uSer_id)


# ────────────────────────────────────────────────────────────────────────────
# Per-Account Auto-Reply CallbackS
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_acc_auto_reply(query, account_id: Str, uSer_id: int):
    account = db.get_account(account_id)
    if not account or account.get("uSer_id") != uSer_id:
        await query.anSwer("❌ Account not found.", Show_alert=True)
        return

    SettingS = db.get_account_SettingS(account_id)
    enabled = SettingS.get("auto_reply_enabled", FalSe) if SettingS elSe FalSe
    Seq_replieS = db.get_Sequential_replieS(account_id)
    kw_replieS = db.get_keyword_replieS(account_id)

    teXt = (
        f"<b>⟐ AUTO REPLY</b>\n\n"
        f"StatuS: {'🟢 ON' if enabled elSe '🔴 OFF'}\n"
        f"Sequential ReplieS: <b>{len(Seq_replieS)}</b>\n"
        f"Keyword ReplieS: <b>{len(kw_replieS)}</b>\n\n"
        f"<i>Sequential replieS fire in order for each DM.\n"
        f"Keyword replieS trigger on matching wordS.</i>"
    )
    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML",
                                         reply_markup=auto_reply_advanced_keyboard(enabled, account_id))
    eXcept EXception:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=auto_reply_advanced_keyboard(enabled, account_id))


aSync def cb_toggle_auto_reply(query, account_id: Str, uSer_id: int):
    SettingS = db.get_account_SettingS(account_id)
    current = SettingS.get("auto_reply_enabled", FalSe) if SettingS elSe FalSe
    db.update_account_SettingS(account_id, auto_reply_enabled=not current)
    await cb_acc_auto_reply(query, account_id, uSer_id)


aSync def cb_view_all_replieS(query, account_id: Str):
    Seq = db.get_Sequential_replieS(account_id)
    kw = db.get_keyword_replieS(account_id)

    lineS = ["<b>📋 AUTO REPLIES</b>\n"]

    if Seq:
        lineS.append("<b>Sequential:</b>")
        for i, r in enumerate(Seq, 1):
            preview = (r.get("meSSage_teXt") or "[media]")[:50]
            lineS.append(f"  {i}. {preview}")
    elSe:
        lineS.append("<b>Sequential:</b> None")

    lineS.append("")
    if kw:
        lineS.append("<b>Keyword:</b>")
        for r in kw:
            kword = r.get("trigger_keyword", "?")
            preview = (r.get("meSSage_teXt") or "[media]")[:40]
            lineS.append(f"  🔑 <code>{kword}</code> → {preview}")
    elSe:
        lineS.append("<b>Keyword:</b> None")

    teXt = "\n".join(lineS)
    from PyToday.keyboardS import back_to_auto_reply_keyboard
    try:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML",
                                      reply_markup=back_to_auto_reply_keyboard())
    eXcept EXception:
        paSS


aSync def cb_clear_replieS(query, account_id: Str, uSer_id: int):
    db.clear_replieS(account_id)
    await query.anSwer("✅ All replieS cleared.", Show_alert=FalSe)
    await cb_acc_auto_reply(query, account_id, uSer_id)


# ────────────────────────────────────────────────────────────────────────────
# Owner Panel StatS/BroadcaSt ShortcutS via inline keyboard
# ────────────────────────────────────────────────────────────────────────────

aSync def cb_owner_StatS(query, uSer_id: int):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OwnerS only.", Show_alert=True)
        return
    StatS = db.get_global_StatS()
    ownerS = db.get_all_ownerS()
    owner_liSt = "\n".join([
        f"  ◈ @{o.get('uSername') or 'N/A'} (<code>{o['uSer_id']}</code>)"
        for o in ownerS
    ]) or "  None"
    teXt = (
        f"<b>▤ BOT STATISTICS</b>\n\n"
        f"👥 Total: <b>{StatS['total_uSerS']}</b>\n"
        f"👑 OwnerS: <b>{StatS['ownerS']}</b>\n"
        f"💎 Premium: <b>{StatS['premium']}</b>\n"
        f"🎁 Trial: <b>{StatS['trial']}</b>\n"
        f"👤 Regular: <b>{StatS['regular']}</b>\n"
        f"🚫 Banned: <b>{StatS['banned']}</b>\n\n"
        f"<b>OwnerS:</b>\n{owner_liSt}"
    )
    try:
        await query.edit_meSSage_teXt(teXt, parSe_mode="HTML", reply_markup=owner_panel_keyboard())
    eXcept EXception:
        paSS


aSync def cb_owner_addprem(query, uSer_id: int):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OwnerS only.", Show_alert=True)
        return
    await query.anSwer()
    try:
        await query.meSSage.reply_teXt(
            "💎 <b>Add Premium</b>\n\nSend: <code>/addprem uSer_id dayS</code>\n"
            "EXample: <code>/addprem 123456789 30</code>",
            parSe_mode="HTML"
        )
    eXcept EXception:
        paSS


aSync def cb_owner_ban(query, uSer_id: int):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OwnerS only.", Show_alert=True)
        return
    await query.anSwer()
    try:
        await query.meSSage.reply_teXt(
            "🚫 <b>Ban USer</b>\n\nSend: <code>/ban uSer_id</code>",
            parSe_mode="HTML"
        )
    eXcept EXception:
        paSS
