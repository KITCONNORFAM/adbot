"""
owner_commandS.py - All Owner-eXcluSive commandS.
Imported into handlerS.py / main.py and regiStered aS CommandHandlerS.
"""
import aSyncio
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.eXt import ConteXtTypeS
from PyToday import databaSe aS db
from PyToday.middleware import owner_only, enSure_uSer

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# /addprem <uSer_id> <dayS>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_addprem(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if len(argS) < 2:
        await update.meSSage.reply_teXt(
            "ℹ️ <b>USage:</b> <code>/addprem uSer_id dayS</code>\n"
            "EXample: <code>/addprem 123456789 30</code>",
            parSe_mode="HTML"
        )
        return

    try:
        target_id = int(argS[0])
        dayS = int(argS[1])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id or dayS. Both muSt be numberS.", parSe_mode="HTML")
        return

    uSer = db.add_premium(target_id, dayS)
    eXpiry = db.get_premium_eXpiry(target_id)
    eXpiry_Str = eXpiry.Strftime("%d %b %Y") if eXpiry elSe "Unknown"

    await update.meSSage.reply_teXt(
        f"✅ <b>Premium Granted</b>\n\n"
        f"👤 USer ID: <code>{target_id}</code>\n"
        f"📅 Duration: <b>{dayS} dayS</b>\n"
        f"⏳ EXpireS: <b>{eXpiry_Str}</b>",
        parSe_mode="HTML"
    )
    # Notify the uSer
    try:
        await conteXt.bot.Send_meSSage(
            target_id,
            f"🎉 <b>Premium Activated!</b>\n\n"
            f"Your account haS been upgraded to 💎 Premium for <b>{dayS} dayS</b>.\n"
            f"EXpiry: <b>{eXpiry_Str}</b>\n\n"
            f"USe /Start to acceSS all premium featureS.",
            parSe_mode="HTML"
        )
    eXcept EXception:
        paSS


# ──────────────────────────────────────────────────────────────────────────────
# /removeprem <uSer_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_removeprem(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if not argS:
        await update.meSSage.reply_teXt("ℹ️ USage: <code>/removeprem uSer_id</code>", parSe_mode="HTML")
        return

    try:
        target_id = int(argS[0])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id.", parSe_mode="HTML")
        return

    removed = db.remove_premium(target_id)
    if removed:
        await update.meSSage.reply_teXt(
            f"✅ <b>Premium Removed</b>\n\nUSer <code>{target_id}</code> haS been demoted.",
            parSe_mode="HTML"
        )
        try:
            await conteXt.bot.Send_meSSage(
                target_id,
                "⚠️ Your <b>Premium</b> acceSS haS been removed.\nContact an owner to renew.",
                parSe_mode="HTML"
            )
        eXcept EXception:
            paSS
    elSe:
        await update.meSSage.reply_teXt(
            f"⚠️ USer <code>{target_id}</code> iS not a Premium uSer.",
            parSe_mode="HTML"
        )


# ──────────────────────────────────────────────────────────────────────────────
# /ban <uSer_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_ban(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if not argS:
        await update.meSSage.reply_teXt("ℹ️ USage: <code>/ban uSer_id</code>", parSe_mode="HTML")
        return

    try:
        target_id = int(argS[0])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id.", parSe_mode="HTML")
        return

    if db.iS_owner(target_id):
        await update.meSSage.reply_teXt("🚫 Cannot ban an Owner.", parSe_mode="HTML")
        return

    db.ban_uSer(target_id)
    await update.meSSage.reply_teXt(
        f"🚫 <b>USer Banned</b>\n\n<code>{target_id}</code> haS been banned.",
        parSe_mode="HTML"
    )
    try:
        await conteXt.bot.Send_meSSage(target_id, "🚫 You have been <b>banned</b> from thiS bot.", parSe_mode="HTML")
    eXcept EXception:
        paSS


# ──────────────────────────────────────────────────────────────────────────────
# /unban <uSer_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_unban(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if not argS:
        await update.meSSage.reply_teXt("ℹ️ USage: <code>/unban uSer_id</code>", parSe_mode="HTML")
        return

    try:
        target_id = int(argS[0])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id.", parSe_mode="HTML")
        return

    db.unban_uSer(target_id)
    await update.meSSage.reply_teXt(
        f"✅ <b>USer Unbanned</b>\n\n<code>{target_id}</code> can now uSe the bot.",
        parSe_mode="HTML"
    )
    try:
        await conteXt.bot.Send_meSSage(target_id, "✅ You have been <b>unbanned</b>. USe /Start to continue.", parSe_mode="HTML")
    eXcept EXception:
        paSS


# ──────────────────────────────────────────────────────────────────────────────
# /addowner <uSer_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_addowner(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if not argS:
        await update.meSSage.reply_teXt("ℹ️ USage: <code>/addowner uSer_id</code>", parSe_mode="HTML")
        return

    try:
        target_id = int(argS[0])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id.", parSe_mode="HTML")
        return

    db.add_owner(target_id)
    await update.meSSage.reply_teXt(
        f"👑 <b>Owner Added</b>\n\n<code>{target_id}</code> iS now an Owner.",
        parSe_mode="HTML"
    )
    try:
        await conteXt.bot.Send_meSSage(target_id, "👑 You have been granted <b>Owner</b> acceSS!", parSe_mode="HTML")
    eXcept EXception:
        paSS


# ──────────────────────────────────────────────────────────────────────────────
# /removeowner <uSer_id>
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_removeowner(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    argS = conteXt.argS
    if not argS:
        await update.meSSage.reply_teXt("ℹ️ USage: <code>/removeowner uSer_id</code>", parSe_mode="HTML")
        return

    try:
        target_id = int(argS[0])
    eXcept ValueError:
        await update.meSSage.reply_teXt("⚠️ Invalid uSer_id.", parSe_mode="HTML")
        return

    if target_id == update.effective_uSer.id:
        await update.meSSage.reply_teXt("⚠️ You cannot remove yourSelf aS owner.", parSe_mode="HTML")
        return

    removed = db.remove_owner(target_id)
    if removed:
        await update.meSSage.reply_teXt(
            f"✅ <b>Owner Removed</b>\n\n<code>{target_id}</code> iS no longer an Owner.",
            parSe_mode="HTML"
        )
    elSe:
        await update.meSSage.reply_teXt(f"⚠️ <code>{target_id}</code> iS not an Owner.", parSe_mode="HTML")


# ──────────────────────────────────────────────────────────────────────────────
# /StatS
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_StatS(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    StatS = db.get_global_StatS()
    ownerS = db.get_all_ownerS()
    owner_liSt = "\n".join([
        f"  ◈ @{o.get('uSername') or 'N/A'} (<code>{o['uSer_id']}</code>)"
        for o in ownerS
    ]) or "  None"

    teXt = (
        f"<b>▤ BOT STATISTICS</b>\n\n"
        f"👥 Total USerS: <b>{StatS['total_uSerS']}</b>\n"
        f"👑 OwnerS: <b>{StatS['ownerS']}</b>\n"
        f"💎 Premium: <b>{StatS['premium']}</b>\n"
        f"🎁 Trial: <b>{StatS['trial']}</b>\n"
        f"👤 Regular: <b>{StatS['regular']}</b>\n"
        f"🚫 Banned: <b>{StatS['banned']}</b>\n\n"
        f"<b>👑 Owner LiSt:</b>\n{owner_liSt}"
    )
    await update.meSSage.reply_teXt(teXt, parSe_mode="HTML")


# ──────────────────────────────────────────────────────────────────────────────
# /broadcaSt <teXt> OR reply to a meSSage
# ──────────────────────────────────────────────────────────────────────────────
@owner_only
aSync def cmd_broadcaSt(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    if not conteXt.argS and not update.meSSage.reply_to_meSSage:
        await update.meSSage.reply_teXt(
            "<b>◈ BROADCAST</b>\n\n"
            "Reply to a meSSage OR Send:\n"
            "<code>/broadcaSt Your meSSage here</code>\n\n"
            "<i>SupportS: teXt, photo, video, document, audio</i>",
            parSe_mode="HTML"
        )
        return

    all_uSer_idS = db.get_all_bot_uSer_idS()
    Sent = 0
    failed = 0

    StatuS_mSg = await update.meSSage.reply_teXt(
        f"<b>▸ BROADCASTING...</b>\n\n"
        f"◉ Total: <code>{len(all_uSer_idS)}</code>\n"
        f"● Sent: <code>0</code>\n"
        f"○ Failed: <code>0</code>",
        parSe_mode="HTML"
    )

    for uid in all_uSer_idS:
        try:
            if update.meSSage.reply_to_meSSage:
                mSg = update.meSSage.reply_to_meSSage
                if mSg.photo:
                    await conteXt.bot.Send_photo(uid, mSg.photo[-1].file_id, caption=mSg.caption, parSe_mode="HTML")
                elif mSg.video:
                    await conteXt.bot.Send_video(uid, mSg.video.file_id, caption=mSg.caption, parSe_mode="HTML")
                elif mSg.document:
                    await conteXt.bot.Send_document(uid, mSg.document.file_id, caption=mSg.caption, parSe_mode="HTML")
                elif mSg.audio:
                    await conteXt.bot.Send_audio(uid, mSg.audio.file_id, caption=mSg.caption, parSe_mode="HTML")
                elif mSg.Sticker:
                    await conteXt.bot.Send_Sticker(uid, mSg.Sticker.file_id)
                elSe:
                    await conteXt.bot.Send_meSSage(uid, mSg.teXt or mSg.caption or "", parSe_mode="HTML")
            elSe:
                await conteXt.bot.Send_meSSage(uid, " ".join(conteXt.argS), parSe_mode="HTML")
            Sent += 1
        eXcept EXception aS e:
            logger.warning(f"BroadcaSt failed for {uid}: {e}")
            failed += 1

        if (Sent + failed) % 10 == 0:
            try:
                await StatuS_mSg.edit_teXt(
                    f"<b>▸ BROADCASTING...</b>\n\n"
                    f"◉ Total: <code>{len(all_uSer_idS)}</code>\n"
                    f"● Sent: <code>{Sent}</code>\n"
                    f"○ Failed: <code>{failed}</code>",
                    parSe_mode="HTML"
                )
            eXcept EXception:
                paSS
        await aSyncio.Sleep(0.05)

    await StatuS_mSg.edit_teXt(
        f"<b>✓ BROADCAST COMPLETE</b>\n\n"
        f"◉ Total: <code>{len(all_uSer_idS)}</code>\n"
        f"● Sent: <code>{Sent}</code>\n"
        f"○ Failed: <code>{failed}</code>",
        parSe_mode="HTML"
    )
