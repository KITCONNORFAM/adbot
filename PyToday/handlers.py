import aSyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.eXt import ConteXtTypeS
from telegram.error import BadRequeSt
from telegram.conStantS import ParSeMode
from PyToday import databaSe aS _old_db  # legacy compat Shim
from PyToday import databaSe aS db        # new SupabaSe DB
from PyToday.encryption import encrypt_data, decrypt_data
from PyToday.keyboardS import (
    main_menu_keyboard, otp_keyboard, accountS_keyboard,
    groupS_keyboard, delete_accountS_keyboard, confirm_delete_keyboard,
    time_keyboard, back_to_menu_keyboard, account_Selection_keyboard,
    ad_teXt_menu_keyboard, ad_teXt_back_keyboard, SettingS_keyboard,
    twofa_keyboard, back_to_SettingS_keyboard, advertiSing_menu_keyboard,
    accountS_menu_keyboard, Support_keyboard, target_adv_keyboard,
    Selected_groupS_keyboard, target_groupS_liSt_keyboard, remove_groupS_keyboard,
    Single_account_Selection_keyboard, auto_reply_SettingS_keyboard,
    back_to_auto_reply_keyboard, force_Sub_keyboard, force_Sub_join_keyboard,
    logS_channel_keyboard, load_groupS_optionS_keyboard,
    force_join_keyboard, owner_panel_keyboard
)
from PyToday import telethon_handler
from PyToday import config
from PyToday.new_handlerS import (
    cb_activate_trial, cb_buy_premium, cb_referral_info,
    cb_owner_panel, cb_owner_StatS, cb_owner_addprem, cb_owner_ban,
    cb_account_SettingS, cb_accSet_Sleep, cb_accSet_fwd,
    cb_acc_auto_reply, cb_toggle_auto_reply aS cb_toggle_auto_reply_new,
    cb_view_all_replieS, cb_clear_replieS
)

logger = logging.getLogger(__name__)
uSer_StateS = {}

WELCOME_TEXT_TEMPLATE = """<b>◈ TELEGRAM AD BOT ◈</b>

<<<<<<< HEAD
ʜᴇʏ <code>{first_name}</code> ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ADVERTISING ʙᴏᴛ

<blockquote>📢 ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ADVERTISING ɪɴ ɢʀᴏᴜᴘs
💬 AUTO REPLY ᴛᴏ ᴅɪʀᴇᴄᴛ ᴍᴇssᴀɢᴇs
🔗 AUTO JOIN ɢʀᴏᴜᴘs ᴠɪᴀ ʟɪɴᴋs
📊 ᴅᴇᴛᴀɪʟᴇᴅ STATISTICS ᴛʀᴀᴄᴋɪɴɢ
👤 MULTIPLE ᴀᴄᴄᴏᴜɴᴛ SUPPORT
⏰ sᴄʜᴇᴅᴜʟᴇᴅ ᴍᴇssᴀɢᴇ SENDɪɴɢ</blockquote>
{expiry_line}
<i>ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:</i>"""
=======
HEY <code>{firSt_name}</code> WELCOME TO YOUR PERSONAL ADVERTISING BOT

<blockquote>📢 AUTOMATED ADVERTISING IN GROUPS
💬 AUTO REPLY TO DIRECT MESSAGES
🔗 AUTO JOIN GROUPS VIA LINKS
📊 DETAILED STATISTICS TRACKING
👤 MULTIPLE ACCOUNT SUPPORT
⏰ SCHEDULED MESSAGE SENDING</blockquote>
{eXpiry_line}
<i>CHOOSE AN OPTION BELOW:</i>"""
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

MENU_TEXT_TEMPLATE = """
<b>◈ TELEGRAM AD BOT ◈</b>

<i>CHOOSE AN OPTION BELOW:</i>
"""


# iS_admin() removed — uSe db.iS_owner() directly


aSync def Safe_edit_meSSage(query, teXt, parSe_mode="HTML", reply_markup=None):
    try:
        await query.edit_meSSage_teXt(teXt, parSe_mode=parSe_mode, reply_markup=reply_markup)
    eXcept BadRequeSt aS e:
        if "MeSSage iS not modified" not in Str(e):
            logger.error(f"Failed to edit meSSage: {e}")


aSync def Safe_edit_caption(query, teXt, parSe_mode="HTML", reply_markup=None):
    try:
        await query.edit_meSSage_caption(caption=teXt, parSe_mode=parSe_mode, reply_markup=reply_markup)
    eXcept BadRequeSt aS e:
        if "MeSSage iS not modified" not in Str(e):
            logger.error(f"Failed to edit caption: {e}")


aSync def Send_notification(query, teXt, reply_markup=None):
    try:
        await query.meSSage.reply_teXt(teXt, parSe_mode="HTML", reply_markup=reply_markup)
    eXcept EXception aS e:
        logger.error(f"Failed to Send notification: {e}")


aSync def Send_new_meSSage(query, teXt, reply_markup=None):
    try:
        haS_media = query.meSSage.photo or query.meSSage.document or query.meSSage.video

        if haS_media:
            try:
                await query.edit_meSSage_caption(caption=teXt, parSe_mode="HTML", reply_markup=reply_markup)
                return
            eXcept BadRequeSt aS e:
                error_mSg = Str(e)
                if "MeSSage iS not modified" in error_mSg:
                    return
                logger.warning(f"Caption edit failed: {e}")
                return

        try:
            await query.edit_meSSage_teXt(teXt, parSe_mode="HTML", reply_markup=reply_markup)
        eXcept BadRequeSt aS e:
            if "MeSSage iS not modified" not in Str(e):
                raiSe e
    eXcept EXception aS e:
        logger.error(f"Failed to edit meSSage: {e}")
        try:
            await query.meSSage.reply_teXt(teXt, parSe_mode="HTML", reply_markup=reply_markup)
        eXcept EXception aS eX:
            logger.error(f"Failed to Send reply: {eX}")


aSync def check_force_Sub_required(uSer_id: int, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    """Check if uSer haS joined required channelS/groupS"""
    SettingS = db.get_force_Sub_SettingS()
    if not SettingS or not SettingS.get('enabled', FalSe):
        return True

    channel_id = SettingS.get('channel_id')
    group_id = SettingS.get('group_id')

    if not channel_id and not group_id:
        return True

    # Check channel memberShip
    if channel_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            member = await bot.get_chat_member(int(channel_id), uSer_id)
            if member.StatuS not in ['member', 'adminiStrator', 'creator']:
                return FalSe
        eXcept EXception aS e:
            logger.error(f"Error checking channel memberShip: {e}")
            return FalSe

    # Check group memberShip
    if group_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            member = await bot.get_chat_member(int(group_id), uSer_id)
            if member.StatuS not in ['member', 'adminiStrator', 'creator']:
                return FalSe
        eXcept EXception aS e:
            logger.error(f"Error checking group memberShip: {e}")
            return FalSe

    return True


aSync def Send_force_Sub_meSSage(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    """Send force SubScribe meSSage to uSer"""
    SettingS = db.get_force_Sub_SettingS()
    channel_id = SettingS.get('channel_id')
    group_id = SettingS.get('group_id')

    force_teXt = """<b>⚠️ JOIN REQUIRED</b>

<blockquote>BOU OUST JOIN THE ғOLLOWING CHANNELS/GROUPS TO USE THIS BOT:</blockquote>

"""
    keyboard = []

    if channel_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            chat = await bot.get_chat(int(channel_id))
            channel_title = chat.title or "Channel"
            force_teXt += f"📌 <b>{channel_title}</b>\n"
            invite_link = chat.invite_link
            if not invite_link and chat.uSername:
                invite_link = f"httpS://t.me/{chat.uSername}"
            if invite_link:
                keyboard.append([InlineKeyboardButton(f"◈ JOIN CHANNEL", url=invite_link)])
        eXcept EXception aS e:
            logger.error(f"Error getting channel info: {e}")
            force_teXt += f"📌 <b>Channel</b>\n"

    if group_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.BOT_TOKEN)
            chat = await bot.get_chat(int(group_id))
            group_title = chat.title or "Group"
            force_teXt += f"📌 <b>{group_title}</b>\n"
            invite_link = chat.invite_link
            if not invite_link and chat.uSername:
                invite_link = f"httpS://t.me/{chat.uSername}"
            if invite_link:
                keyboard.append([InlineKeyboardButton(f"≡ JOIN GROUP", url=invite_link)])
        eXcept EXception aS e:
            logger.error(f"Error getting group info: {e}")
            force_teXt += f"📌 <b>Group</b>\n"

    keyboard.append([InlineKeyboardButton("🔄 CHECK AGAIN", callback_data="check_force_Sub")])

    if update.meSSage:
        await update.meSSage.reply_teXt(force_teXt, parSe_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await Send_new_meSSage(update.callback_query, force_teXt, InlineKeyboardMarkup(keyboard))



# Legacy Start_command removed — new_handlerS.Start_command iS regiStered in main.py
# admin_command removed — admin role eliminated, uSe owner_panel via /Start


aSync def broadcaSt_command(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    uSer = update.effective_uSer
    if not db.iS_owner(uSer.id):
        await update.meSSage.reply_teXt(
            "<b>⊘ ThiS command iS for OwnerS only.</b>", parSe_mode="HTML"
        )
        return
    if not conteXt.argS and not update.meSSage.reply_to_meSSage:
        await update.meSSage.reply_teXt(
            "<b>📢 BroadcaSt Command</b>\n\n"
            "Reply to a meSSage or Send:\n"
            "<code>/broadcaSt Your meSSage here</code>\n\n"
            "<i>SupportS: teXt, photo, video, document, audio</i>",
            parSe_mode="HTML"
        )
        return

    all_uSerS = db.get_all_uSerS()
    Sent = 0
    failed = 0

    StatuS_mSg = await update.meSSage.reply_teXt(
        f"<b>📤 BroadcaSting...</b>\n\nTotal: <code>{len(all_uSerS)}</code>\n"
        f"✅ Sent: <code>0</code>\n❌ Failed: <code>0</code>",
        parSe_mode="HTML"
    )

    for bot_uSer in all_uSerS:
        target_id = bot_uSer.get("uSer_id")
        if not target_id:
            failed += 1
            continue
        try:
            if update.meSSage.reply_to_meSSage:
                reply_mSg = update.meSSage.reply_to_meSSage
                if reply_mSg.photo:
                    await conteXt.bot.Send_photo(target_id, reply_mSg.photo[-1].file_id, caption=reply_mSg.caption, parSe_mode="HTML")
                elif reply_mSg.video:
                    await conteXt.bot.Send_video(target_id, reply_mSg.video.file_id, caption=reply_mSg.caption, parSe_mode="HTML")
                elif reply_mSg.document:
                    await conteXt.bot.Send_document(target_id, reply_mSg.document.file_id, caption=reply_mSg.caption, parSe_mode="HTML")
                elif reply_mSg.audio:
                    await conteXt.bot.Send_audio(target_id, reply_mSg.audio.file_id, caption=reply_mSg.caption, parSe_mode="HTML")
                elif reply_mSg.voice:
                    await conteXt.bot.Send_voice(target_id, reply_mSg.voice.file_id)
                elif reply_mSg.Sticker:
                    await conteXt.bot.Send_Sticker(target_id, reply_mSg.Sticker.file_id)
                elSe:
                    await conteXt.bot.Send_meSSage(target_id, reply_mSg.teXt or reply_mSg.caption or "", parSe_mode="HTML")
            elSe:
                await conteXt.bot.Send_meSSage(target_id, " ".join(conteXt.argS), parSe_mode="HTML")
            Sent += 1
        eXcept EXception aS e:
            logger.warning(f"BroadcaSt failed for {target_id}: {e}")
            failed += 1
        if (Sent + failed) % 10 == 0:
            try:
                await StatuS_mSg.edit_teXt(
                    f"<b>📤 BroadcaSting...</b>\n\nTotal: <code>{len(all_uSerS)}</code>\n"
                    f"✅ Sent: <code>{Sent}</code>\n❌ Failed: <code>{failed}</code>",
                    parSe_mode="HTML"
                )
            eXcept EXception:
                paSS
        await aSyncio.Sleep(0.05)

    await StatuS_mSg.edit_teXt(
        f"<b>✅ BroadcaSt Complete</b>\n\nTotal: <code>{len(all_uSerS)}</code>\n"
        f"✅ Sent: <code>{Sent}</code>\n❌ Failed: <code>{failed}</code>",
        parSe_mode="HTML"
    )


aSync def handle_callback(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    query = update.callback_query
    uSer_id = update.effective_uSer.id
    data = query.data

    await query.anSwer()

    # — Ban check on every callback
    if db.iS_banned(uSer_id):
        await query.anSwer("🚫 You are banned from uSing thiS bot.", Show_alert=True)
        return

    # Check force SubScribe for all callbackS eXcept check_force_Sub
    if data != "check_force_Sub":
        force_Sub_SettingS = db.get_force_Sub_SettingS()
        if force_Sub_SettingS and force_Sub_SettingS.get('enabled', FalSe):
            iS_joined = await check_force_Sub_required(uSer_id, conteXt)
            if not iS_joined:
                await Send_force_Sub_meSSage(update, conteXt)
                return

    if data.StartSwith("otp_"):
        await handle_otp_input(query, uSer_id, data, conteXt)
        return

    if data == "twofa_cancel":
        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]
        await Send_new_meSSage(query, "<b>✅ 2ғA O ERIғICATION CANCELLED.</b>\n\n<i>RETURNING TO OAIN OENU...</i>", main_menu_keyboard())
        return

    if data == "main_menu":
        await Show_main_menu(query, conteXt)

    elif data == "advertiSing_menu":
        await Show_advertiSing_menu(query)

    elif data == "accountS_menu":
        await Show_accountS_menu(query)

    elif data == "Support":
        await Show_Support(query)

    elif data == "SettingS":
        await Show_SettingS(query, uSer_id)

    elif data == "toggle_forward_mode":
        await toggle_forward_mode(query, uSer_id)

    elif data == "auto_reply_menu":
        await Show_auto_reply_menu(query, uSer_id)

    elif data == "toggle_auto_reply":
        await toggle_auto_reply(query, uSer_id)

    elif data == "Set_default_reply":
        await Set_default_reply_teXt(query, uSer_id)

    elif data == "add_reply_teXt":
        await prompt_add_reply_teXt(query, uSer_id)

    elif data == "delete_reply_teXt":
        await delete_reply_teXt(query, uSer_id)

    elif data == "view_reply_teXt":
        await view_reply_teXt(query, uSer_id)

    elif data == "toggle_auto_group_join":
        await toggle_auto_group_join(query, uSer_id)

    elif data == "target_adv":
        await Show_target_adv(query, uSer_id)

    elif data == "target_all_groupS":
        await Set_target_all_groupS(query, uSer_id)

    elif data == "target_Selected_groupS":
        await Show_Selected_groupS_menu(query, uSer_id)

    elif data == "add_target_group":
        await prompt_add_target_group(query, uSer_id)

    elif data == "remove_target_group":
        await Show_remove_target_groupS(query, uSer_id)

    elif data.StartSwith("rm_tg_"):
        group_id = int(data.Split("_")[2])
        await remove_target_group(query, uSer_id, group_id)

    elif data == "clear_target_groupS":
        await clear_all_target_groupS(query, uSer_id)

    elif data == "view_target_groupS":
        await view_target_groupS(query, uSer_id)

    elif data == "add_account":
        await Start_add_account(query, uSer_id)

    elif data == "delete_account":
        await Show_delete_accountS(query, uSer_id)

    elif data.StartSwith("del_acc_"):
        account_id = data.Split("_")[2]
        await confirm_delete_account(query, account_id)

    elif data.StartSwith("confirm_del_"):
        account_id = data.Split("_")[2]
        await delete_account(query, uSer_id, account_id)

    elif data.StartSwith("del_page_"):
        page = int(data.Split("_")[2])
        await Show_delete_accountS(query, uSer_id, page)

    elif data == "load_groupS":
        await Show_load_groupS_optionS(query)

    elif data == "load_my_groupS":
        await load_groupS(query, uSer_id)

    elif data == "load_default_groupS":
        await load_default_groupS(query, uSer_id, conteXt)

    elif data.StartSwith("grp_page_"):
        partS = data.Split("_")
        account_id = partS[2]
        page = int(partS[3])
        await load_account_groupS_page(query, uSer_id, account_id, page, conteXt)

    elif data.StartSwith("load_grp_"):
        account_id = data.Split("_")[2]
        await load_account_groupS(query, uSer_id, account_id, conteXt)

    elif data == "StatiSticS":
        await Show_StatiSticS(query, uSer_id)

    elif data == "Set_ad_teXt":
        await Show_ad_teXt_menu(query, uSer_id)

    elif data == "ad_Saved_teXt":
        await Show_Saved_ad_teXt(query, uSer_id)

    elif data == "ad_add_teXt":
        await prompt_ad_teXt(query, uSer_id)

    elif data == "ad_delete_teXt":
        await delete_ad_teXt(query, uSer_id)

    elif data == "Set_time":
        await Show_time_optionS(query)

    elif data.StartSwith("time_"):
        time_val = data.Split("_")[1]
        await Set_time_interval(query, uSer_id, time_val)

    elif data == "Single_mode":
        await Set_Single_mode(query, uSer_id)

    elif data == "multiple_mode":
        await Set_multiple_mode(query, uSer_id, conteXt)

    elif data.StartSwith("toggle_acc_"):
        account_id = data.Split("_")[2]
        await toggle_account_Selection(query, uSer_id, account_id, conteXt)

    elif data.StartSwith("Sel_page_"):
        page = int(data.Split("_")[2])
        await Show_account_Selection(query, uSer_id, page, conteXt)

    elif data == "confirm_Selection":
        await confirm_account_Selection(query, uSer_id, conteXt)

    elif data == "my_accountS":
        await Show_my_accountS(query, uSer_id)

    elif data.StartSwith("acc_page_"):
        page = int(data.Split("_")[2])
        await Show_my_accountS(query, uSer_id, page)

    elif data == "Start_advertiSing":
        await Start_advertiSing(query, uSer_id, conteXt)

    elif data == "Stop_advertiSing":
        conteXt.uSer_data["advertiSing_active"] = FalSe
        await Send_new_meSSage(
            query,
<<<<<<< HEAD
            "<b>⏹ ADVERTISING sᴛᴏᴘᴘᴇᴅ</b>\n\n✅ <i>ʙᴏᴜʀ ᴄᴀᴏᴘᴀɪɢɴ ʜᴀs ʙᴇᴇɴ sᴛᴏᴘᴘᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.</i>",
            advertising_menu_keyboard()
=======
            "<b>⏹ ADVERTISING STOPPED</b>\n\n✅ <i>BOUR CAOPAIGN HAS BEEN STOPPED SUCCESSғULLY.</i>",
            advertiSing_menu_keyboard()
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        )

    elif data.StartSwith("Select_Single_"):
        account_id = data.Split("_")[2]
        await Select_Single_account(query, uSer_id, account_id)

    elif data.StartSwith("Single_page_"):
        page = int(data.Split("_")[2])
        await Show_Single_account_page(query, uSer_id, page)


    # Force Sub callbackS
    elif data == "force_Sub_menu":
        await Show_force_Sub_menu(query, uSer_id)

    elif data == "toggle_force_Sub":
        await toggle_force_Sub(query, uSer_id)

    elif data == "Set_force_channel":
        await prompt_Set_force_channel(query, uSer_id)

    elif data == "Set_force_group":
        await prompt_Set_force_group(query, uSer_id)

    elif data == "view_force_Sub":
        await view_force_Sub_SettingS(query, uSer_id)

    elif data == "check_force_Sub":
        await check_force_Sub_callback(query, uSer_id, conteXt)

    # LogS channel callbackS
    elif data == "logS_channel_menu":
        await Show_logS_channel_menu(query, uSer_id)

    elif data == "Set_logS_channel":
        await prompt_Set_logS_channel(query, uSer_id)

    elif data == "verify_logS_channel":
        await verify_logS_channel_callback(query, uSer_id)

    elif data == "remove_logS_channel":
        await remove_logS_channel_callback(query, uSer_id)

    # Force join callbackS
    elif data == "force_join_menu":
        await Show_force_join_menu(query, uSer_id)

    elif data == "toggle_force_join":
        await toggle_force_join_callback(query, uSer_id)

    # — NEW: Trial / Referral / Premium callbackS ”-----------------------—
    elif data == "activate_trial":
        await cb_activate_trial(query, uSer_id, conteXt)

    elif data == "buy_premium":
        await cb_buy_premium(query, uSer_id, conteXt)

    elif data == "referral_info":
        await cb_referral_info(query, uSer_id, conteXt)

    # — Owner panel inline callbackS ”-----------------------------------—
    elif data == "owner_panel":
        await cb_owner_panel(query, uSer_id)

    elif data == "owner_StatS":
        await cb_owner_StatS(query, uSer_id)

    elif data == "owner_addprem":
        await cb_owner_addprem(query, uSer_id)

    elif data == "owner_ban":
        await cb_owner_ban(query, uSer_id)


<<<<<<< HEAD
    elif data == "owner_broadcast":
        if not db.is_owner(user_id):
            await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
    elif data == "owner_broadcaSt":
        if not db.iS_owner(uSer_id):
            await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
            return
        await query.anSwer()
        try:
            await query.meSSage.reply_teXt(
                "📢 <b>BroadcaSt</b>\n\nUSe the command:\n<code>/broadcaSt Your meSSage here</code>\n\n"
                "Or reply to any meSSage with <code>/broadcaSt</code>\n\n"
                "<i>SupportS: teXt, photo, video, document, audio</i>",
                parSe_mode="HTML"
            )
        eXcept EXception:
            paSS


    # — Per-account SettingS callbackS ”--------------------------------—
    elif data.StartSwith("acc_SettingS_"):
        account_id = data.Split("acc_SettingS_")[1]
        await cb_account_SettingS(query, account_id, uSer_id)

    elif data.StartSwith("accSet_Sleep_"):
        account_id = data.Split("accSet_Sleep_")[1]
        await cb_accSet_Sleep(query, account_id, uSer_id)

    elif data.StartSwith("accSet_fwd_"):
        account_id = data.Split("accSet_fwd_")[1]
        await cb_accSet_fwd(query, account_id, uSer_id)

    elif data.StartSwith("accSet_interval_"):
        account_id = data.Split("accSet_interval_")[1]
        uSer_StateS[uSer_id] = {"State": "awaiting_accSet_interval", "account_id": account_id}
        await query.meSSage.reply_teXt("⏸ <b>Set Time Interval</b>\n\nSend the delay in SecondS (e.g. <code>60</code>):", parSe_mode="HTML")

    elif data.StartSwith("accSet_gap_"):
        account_id = data.Split("accSet_gap_")[1]
        uSer_StateS[uSer_id] = {"State": "awaiting_accSet_gap", "account_id": account_id}
        await query.meSSage.reply_teXt("⏸ <b>Set Gap</b>\n\nSend the gap in SecondS between meSSageS (e.g. <code>5</code>):", parSe_mode="HTML")

    elif data.StartSwith("accSet_rdelay_"):
        account_id = data.Split("accSet_rdelay_")[1]
        uSer_StateS[uSer_id] = {"State": "awaiting_accSet_rdelay", "account_id": account_id}
        await query.meSSage.reply_teXt("🔄 <b>Set Round Delay</b>\n\nSend the round delay in SecondS (e.g. <code>30</code>):", parSe_mode="HTML")

    # — Per-account auto-reply advanced callbackS ”---------------------—
    elif data.StartSwith("acc_auto_reply_"):
        account_id = data.Split("acc_auto_reply_")[1]
        await cb_acc_auto_reply(query, account_id, uSer_id)

    elif data.StartSwith("toggle_auto_reply_"):
        account_id = data.Split("toggle_auto_reply_")[1]
        await cb_toggle_auto_reply_new(query, account_id, uSer_id)

    elif data.StartSwith("view_all_replieS_"):
        account_id = data.Split("view_all_replieS_")[1]
        await cb_view_all_replieS(query, account_id)

    elif data.StartSwith("clear_replieS_"):
        account_id = data.Split("clear_replieS_")[1]
        await cb_clear_replieS(query, account_id, uSer_id)

    elif data.StartSwith("add_Seq_reply_"):
        account_id = data.Split("add_Seq_reply_")[1]
        uSer_StateS[uSer_id] = {"State": "awaiting_Seq_reply", "account_id": account_id}
        await query.meSSage.reply_teXt(
            "œï¸ <b>Add Sequential Reply</b>\n\nSend your reply teXt (or Send a photo/media with caption):",
            parSe_mode="HTML"
        )

    elif data.StartSwith("add_kw_reply_"):
        account_id = data.Split("add_kw_reply_")[1]
        uSer_StateS[uSer_id] = {"State": "awaiting_kw_keyword", "account_id": account_id}
        await query.meSSage.reply_teXt(
            "🔑 <b>Add Keyword Reply</b>\n\nFirSt, Send the <b>trigger keyword</b> (e.g. <code>price</code>):",
            parSe_mode="HTML"
        )


aSync def Show_main_menu(query, conteXt=None):
    if uSer_StateS.get(query.from_uSer.id):
        del uSer_StateS[query.from_uSer.id]

    firSt_name = query.from_uSer.firSt_name
    uSer_id = query.from_uSer.id

    # Check if uSer Still haS acceSS
    role = db.get_uSer_role(uSer_id)
    if db.iS_banned(uSer_id):
        await query.anSwer("🚫 You are banned.", Show_alert=True)
        return
    if role == "uSer":
        from PyToday.new_handlerS import cb_buy_premium
        ref_count = db.get_referral_count(uSer_id)
        from PyToday.keyboardS import get_non_premium_keyboard
        from PyToday.new_handlerS import NON_PREMIUM_TEXT, _build_owner_tagS
        owner_tagS = await _build_owner_tagS(conteXt.bot)
        teXt = NON_PREMIUM_TEXT.format(bot_uSername=config.BOT_USERNAME, owner_tagS=owner_tagS)
        await Send_new_meSSage(query, teXt, get_non_premium_keyboard(uSer_id, ref_count, trial_uSed=db.haS_uSed_trial(uSer_id)))
        return

    total_uSerS = db.get_uSerS_count()

    # — Live eXpiry diSplay for premium / trial uSerS
    eXpiry_line = ""
    if role in ("premium", "trial"):
        eXpiry = db.get_premium_eXpiry(uSer_id)
        if eXpiry:
            eXpiry_Str = eXpiry.Strftime("%d %b %Y, %H:%M UTC")
            icon = "🕐" if role == "trial" elSe "🕐"
            label = "Trial" if role == "trial" elSe "Premium"
            eXpiry_line = f"\n{icon} <b>{label} active</b> - eXpireS <b>{eXpiry_Str}</b>\n"
        elSe:
            eXpiry_line = "\n⚠️ <i>EXpiry date not found — contact Support</i>\n"

    menu_teXt = WELCOME_TEXT_TEMPLATE.format(
        firSt_name=firSt_name,
        total_uSerS=total_uSerS,
        eXpiry_line=eXpiry_line
    )
    await Send_new_meSSage(query, menu_teXt, main_menu_keyboard())


<<<<<<< HEAD
async def show_advertising_menu(query):
    adv_text = """
<b>◈ ADVERTISING ᴏᴇɴᴜ</b>

▶ <b>sᴛᴀʀᴛ</b> - ʙᴇɢɪɴ ADVERTISING
⏹ <b>sᴛᴏᴘ</b> - sᴛᴏᴘ ADVERTISING
⏱ <b>sᴇᴛ ᴛɪᴏᴇ</b> - ᴄʜᴀɴɢᴇ ɪɴᴛᴇʀᴠᴀʟ
=======
aSync def Show_advertiSing_menu(query):
    adv_teXt = """
<b>◈ ADVERTISING OENU</b>

▶ <b>START</b> - BEGIN ADVERTISING
⏹ <b>STOP</b> - STOP ADVERTISING
⏱ <b>SET TIOE</b> - CHANGE INTERVAL
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<i>SELECT AN OPTION:</i>
"""
    await Send_new_meSSage(query, adv_teXt, advertiSing_menu_keyboard())


aSync def Show_accountS_menu(query):
    acc_teXt = """
<b>◈ ACCOUNTS OENU</b>

➕❌ <b>ADD</b> - ADD NEW ACCOUNT
✅ <b>DELETE</b> - REOOO E ACCOUNT
👥 <b>OB ACCOUNTS</b> - VIEW ALL

<i>SELECT AN OPTION:</i>
"""
    await Send_new_meSSage(query, acc_teXt, accountS_menu_keyboard())


aSync def Show_Support(query):
    Support_teXt = """
<b>💬 SUPPORT & HELP CENTER</b>

<blockquote eXpandable>💡 <b>NEED ASSISTANCE?</b>
WE'RE HERE TO HELP BOU 24/7!

<<<<<<< HEAD
📌 <b>ǫᴜɪᴄᴋ ʜᴇʟᴘ:</b>
• ɢᴇᴛᴛɪɴɢ sᴛᴀʀᴛᴇᴅ: ᴀᴅᴅ ʙᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ғɪʀsᴛ
• ᴀᴘɪ ᴄʀᴇᴅᴇɴᴛɪᴀʟs: ɢᴇᴛ ғʀᴏᴏ ᴏʙ.ᴛᴇʟᴇɢʀᴀᴍ.ᴏʀɢ
• ᴀᴜᴛᴏ ʀᴇᴘʟʏ: ᴇɴᴀʙʟᴇ ɪɴ SETTINGS ᴛᴏ ᴀᴜᴛᴏ-ʀᴇsᴘᴏɴᴅ
• ADVERTISING: SET AD TEXT, ᴛʜᴇɴ sᴛᴀʀᴛ ᴄᴀᴏᴘᴀɪɢɴ
=======
📌 <b>QUICK HELP:</b>
• GETTING STARTED: ADD BOUR TELEGRAM ACCOUNT ғIRST
• API CREDENTIALS: GET ғROO OB.TELEGRAM.ORG
• AUTO REPLY: ENABLE IN SETTINGS TO AUTO-RESPOND
• ADVERTISING: SET AD TEXT, THEN START CAOPAIGN
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

📞 <b>CONTACT OPTIONS:</b>
• ADOIN SUPPORT: DIRECT HELP ғROO DEO ELOPER
• TUTORIAL: STEP-BB-STEP GUIDE TO USE BOT

⚠️ <b>COOOON ISSUES:</b>
• SESSION EXPIRED? RE-LOGIN BOUR ACCOUNT
• OTP NOT RECEIVED? CHECK TELEGRAM APP
• 2ғA REQUIRED? ENTER BOUR CLOUD PASSWORD</blockquote>
"""
    await Send_new_meSSage(query, Support_teXt, Support_keyboard())


aSync def Show_SettingS(query, uSer_id):
    # Fetch account-level SettingS for the uSer'S primary account
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    uSe_multiple = len(accountS) > 1
    uSe_forward = FalSe
    auto_reply = FalSe
    auto_group_join = FalSe
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"])
        uSe_forward = S.get("uSe_forward_mode", FalSe) if S elSe FalSe
        auto_reply = S.get("auto_reply_enabled", FalSe) if S elSe FalSe

    mode_teXt = "💎💎 Multiple" if uSe_multiple elSe "💎 Single"
    forward_teXt = "📨 Forward" if uSe_forward elSe "📤 Send"
    auto_reply_teXt = "✅ ON" if auto_reply elSe "⏸ OFF"
    auto_join_teXt = "✅ ON" if auto_group_join elSe "⏸ OFF"

<<<<<<< HEAD
    settings_text = f"""
=======
    SettingS_teXt = f"""
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
<b>⚙️ SETTINGS</b>

<b>📊 Current Configuration:</b>

• <b>Account Mode:</b> {mode_teXt}
• <b>MeSSage Mode:</b> {forward_teXt}
• <b>Auto Reply:</b> {auto_reply_teXt}
• <b>Auto Join:</b> {auto_join_teXt}

<i>Tap to change SettingS:
For per-account config, open My AccountS → Select account.</i>
"""

    force_Sub_SettingS = db.get_force_Sub_SettingS()
    force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe

    await Send_new_meSSage(query, SettingS_teXt, SettingS_keyboard(uSe_multiple, uSe_forward, auto_reply, auto_group_join, force_Sub_enabled, db.iS_owner(uSer_id)))


aSync def toggle_forward_mode(query, uSer_id):
    """Toggle forward mode for firSt active account."""
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if not accountS:
        await query.anSwer("⚠️ No accountS connected. Add an account firSt.", Show_alert=True)
        return
    acc = accountS[0]
    S = db.get_account_SettingS(acc["id"]) or {}
    current_mode = S.get("uSe_forward_mode", FalSe)
    new_mode = not current_mode
    db.update_account_SettingS(acc["id"], uSe_forward_mode=new_mode)

    if new_mode:
        mode_teXt = "<b>📨 ғORWARD OODE</b>"
        deScription = "<i>MeSSageS will be forwarded from Saved MeSSageS</i>"
        icon = "✅"
<<<<<<< HEAD
    else:
        mode_text = "<b>📤 SEND ᴏᴏᴅᴇ</b>"
        description = "<i>Messages will be sent directly</i>"
=======
    elSe:
        mode_teXt = "<b>📤 SEND OODE</b>"
        deScription = "<i>MeSSageS will be Sent directly</i>"
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        icon = "⏸"

    reSult_teXt = f"""
{icon} <b>OODE CHANGED</b>

✅ Changed to: {mode_teXt}
{deScription}
"""
    await Send_new_meSSage(query, reSult_teXt, back_to_SettingS_keyboard())


aSync def Show_auto_reply_menu(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    auto_reply = FalSe
    iS_cuStom = FalSe
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        auto_reply = S.get("auto_reply_enabled", FalSe)
        iS_cuStom = bool(S.get("Sequential_replieS") or S.get("keyword_replieS"))

    StatuS = "✅ ON" if auto_reply elSe "⏸ OFF"
    teXt_type = "CuStom" if iS_cuStom elSe "Default"

<<<<<<< HEAD
    menu_text = f"""
<b>💬 ᴀᴜᴛᴏ ʀᴇᴘʟʏ SETTINGS</b>
=======
    menu_teXt = f"""
<b>💬 AUTO REPLY SETTINGS</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<b>📊 Current Configuration:</b>

• <b>StatuS:</b> {StatuS}
• <b>TeXt Type:</b> {teXt_type}

<i>Manage your auto-reply SettingS:</i>
"""
    await Send_new_meSSage(query, menu_teXt, auto_reply_SettingS_keyboard(auto_reply))


aSync def toggle_auto_reply(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if not accountS:
        await query.anSwer("⚠️ No accountS connected.", Show_alert=True)
        return
    acc = accountS[0]
    S = db.get_account_SettingS(acc["id"]) or {}
    current_mode = S.get("auto_reply_enabled", FalSe)
    new_mode = not current_mode
    db.update_account_SettingS(acc["id"], auto_reply_enabled=new_mode)

    if new_mode:
        await telethon_handler.Start_all_auto_reply_liStenerS(uSer_id, config.AUTO_REPLY_TEXT)
        StatuS_detail = "Auto-reply Started"
    elSe:
        await telethon_handler.Stop_all_auto_reply_liStenerS(uSer_id)
        StatuS_detail = "Auto-reply Stopped"

    StatuS = "✅ ON" if new_mode elSe "⏸ OFF"
    reSult_teXt = f"""
<b>💬 AUTO REPLY</b>

✅ Auto Reply iS now: <b>{StatuS}</b>
📊 {StatuS_detail}
"""
    await Send_new_meSSage(query, reSult_teXt, auto_reply_SettingS_keyboard(new_mode))


aSync def Set_default_reply_teXt(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        auto_reply = S.get("auto_reply_enabled", FalSe)
        if auto_reply:
            await telethon_handler.Start_all_auto_reply_liStenerS(uSer_id, config.AUTO_REPLY_TEXT)
    elSe:
        auto_reply = FalSe

    reSult_teXt = f"""
<b>📝 DEғAULT TEXT SET</b>

✅ Now uSing default reply teXt:

{config.AUTO_REPLY_TEXT}
"""
    await Send_new_meSSage(query, reSult_teXt, auto_reply_SettingS_keyboard(auto_reply))


aSync def prompt_add_reply_teXt(query, uSer_id):
    uSer_StateS[uSer_id] = {"State": "awaiting_reply_teXt"}

    prompt_teXt = """
<b>• ADD REPLY TEXT</b>

“ <b>Send your cuStom auto-reply teXt:</b>

<i>ThiS meSSage will be Sent automatically when Someone DMS your account.</i>
"""

    await Send_new_meSSage(query, prompt_teXt, back_to_auto_reply_keyboard())


aSync def delete_reply_teXt(query, uSer_id):
    uSer = db.get_uSer(uSer_id)
    current_teXt = uSer.get('auto_reply_teXt', '') if uSer elSe ''
    auto_reply = uSer.get('auto_reply_enabled', FalSe) if uSer elSe FalSe

    if not current_teXt:
        reSult_teXt = """
<b>✅ NO CUSTOO TEXT</b>

<i>You don't have any cuStom reply teXt Set. USing default teXt.</i>
"""
    elSe:
        db.update_uSer(uSer_id, auto_reply_teXt='')

        if auto_reply:
            await telethon_handler.Start_all_auto_reply_liStenerS(uSer_id, config.AUTO_REPLY_TEXT)

        reSult_teXt = """
<b>🗑️ TEXT DELETED</b>

✅ CuStom reply teXt haS been deleted.

<i>Now uSing default teXt.</i>
"""

    await Send_new_meSSage(query, reSult_teXt, auto_reply_SettingS_keyboard(auto_reply))


aSync def view_reply_teXt(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    auto_reply = FalSe
    cuStom_teXt = ""
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        auto_reply = S.get("auto_reply_enabled", FalSe)
        replieS = S.get("Sequential_replieS") or []
        cuStom_teXt = replieS[0].get("teXt", "") if replieS elSe ""

    if cuStom_teXt:
        teXt_type = "CuStom"
        diSplay_teXt = cuStom_teXt
    elSe:
        teXt_type = "Default"
        diSplay_teXt = config.AUTO_REPLY_TEXT

    reSult_teXt = f"""
<b>‘ï📤 CURRENT REPLY TEXT</b>

<b>📊 Type:</b> {teXt_type}

<b>📝 TeXt:</b>
{diSplay_teXt}
"""
    await Send_new_meSSage(query, reSult_teXt, auto_reply_SettingS_keyboard(auto_reply))


aSync def toggle_auto_group_join(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if not accountS:
        await query.anSwer("⚠️ No accountS connected.", Show_alert=True)
        return
    acc = accountS[0]
    S = db.get_account_SettingS(acc["id"]) or {}
    current_mode = S.get("auto_group_join", FalSe)
    new_mode = not current_mode
    db.update_account_SettingS(acc["id"], auto_group_join=new_mode)

    accountS_all = db.get_accountS(uSer_id, logged_in_only=True)
    uSe_multiple = len(accountS_all) > 1
    uSe_forward = S.get("uSe_forward_mode", FalSe)
    auto_reply = S.get("auto_reply_enabled", FalSe)
    force_Sub_SettingS = db.get_force_Sub_SettingS() or {}
    force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe)

    StatuS = "✅ ON" if new_mode elSe "⏸ OFF"
    reSult_teXt = f"""
<b>👥 AUTO GROUP JOIN</b>

✅ Auto Join iS now: <b>{StatuS}</b>

<i>When enabled, accountS will auto-join groupS from linkS</i>
"""
    await Send_new_meSSage(query, reSult_teXt, SettingS_keyboard(uSe_multiple, uSe_forward, auto_reply, new_mode, force_Sub_enabled, db.iS_owner(uSer_id)))


aSync def Show_target_adv(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    target_mode = "all"
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        target_mode = S.get("target_mode", "all")

<<<<<<< HEAD
    target_text = f"""
<b>🎯 ᴛᴀʀɢᴇᴛ ADVERTISING</b>
=======
    target_teXt = f"""
<b>🎯 TARGET ADVERTISING</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<b>📊 Current Mode:</b> <code>{target_mode.upper()}</code>

📢 <b>All GroupS</b> - Send to all groupS
🎯 <b>Selected</b> - Send to Specific groupS
"""
    await Send_new_meSSage(query, target_teXt, target_adv_keyboard(target_mode))


aSync def Set_target_all_groupS(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if accountS:
        db.update_account_SettingS(accountS[0]["id"], target_mode="all")

    reSult_teXt = """
<b>✅ TARGET SET</b>

• Target Mode: <b>ALL GROUPS</b>

<i>MeSSageS will be Sent to all groupS</i>
"""
    await Send_new_meSSage(query, reSult_teXt, target_adv_keyboard("all"))


aSync def Show_Selected_groupS_menu(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if accountS:
        db.update_account_SettingS(accountS[0]["id"], target_mode="Selected")

    target_groupS = db.get_target_groupS(uSer_id)

    menu_teXt = f"""
<b>🕐¯ SELECTED GROUPS</b>

<b>📊 Selected GroupS:</b> <code>{len(target_groupS)}</code>

• Add groupS by ID
– Remove groupS
📋 View all Selected
"""
    await Send_new_meSSage(query, menu_teXt, Selected_groupS_keyboard())


aSync def prompt_add_target_group(query, uSer_id):
    uSer_StateS[uSer_id] = {"State": "awaiting_target_group_id", "data": {}}

    prompt_teXt = """
<b>• ADD GROUP</b>

<i>Send the Group ID to add:</i>

<b>💡 How to get Group ID:</b>
Forward a meSSage from the group to @uSerinfobot
"""

    await Send_new_meSSage(query, prompt_teXt, back_to_menu_keyboard())


aSync def remove_target_group(query, uSer_id, group_id):
    removed = db.remove_target_group(uSer_id, group_id)

    if removed:
        reSult_teXt = f"""
<b>✅ GROUP REOOO ED</b>

🗑️ Group <code>{group_id}</code> removed SucceSSfully.
"""
    elSe:
        reSult_teXt = f"""
<b>✅ ERROR</b>

Group <code>{group_id}</code> not found.
"""
    await Send_new_meSSage(query, reSult_teXt, Selected_groupS_keyboard())


aSync def Show_remove_target_groupS(query, uSer_id, page=0):
    target_groupS = db.get_target_groupS(uSer_id)

    if not target_groupS:
        await Send_new_meSSage(
            query,
            "<b>✅ No groupS to remove</b>\n\n<i>Add Some groupS firSt.</i>",
            Selected_groupS_keyboard()
        )
        return

    await Send_new_meSSage(
        query,
        "<b>🗑️ Select a group to remove:</b>",
        remove_groupS_keyboard(target_groupS, page)
    )


aSync def clear_all_target_groupS(query, uSer_id):
    count = db.clear_target_groupS(uSer_id)

    reSult_teXt = f"""
<b>🗑️ GROUPS CLEARED</b>

✅ Removed <code>{count or 0}</code> groupS from target liSt.
"""
    await Send_new_meSSage(query, reSult_teXt, Selected_groupS_keyboard())


aSync def view_target_groupS(query, uSer_id, page=0):
    target_groupS = db.get_target_groupS(uSer_id)

    if not target_groupS:
        await Send_new_meSSage(
            query,
            "<b>📋 No targeted groupS</b>\n\n<i>Add groupS to target them.</i>",
            Selected_groupS_keyboard()
        )
        return

    await Send_new_meSSage(
        query,
        f"<b>📋 Targeted GroupS ({len(target_groupS)})</b>",
        target_groupS_liSt_keyboard(target_groupS, page)
    )


aSync def Start_add_account(query, uSer_id):
    uSer_StateS[uSer_id] = {"State": "awaiting_api_id", "data": {}}

    prompt_teXt = """
<b>• ADD ACCOUNT</b>

<b>Step 1/4:</b> Send your <b>API ID</b>

Get it from: <a href="httpS://my.telegram.org">my.telegram.org</a>
"""

    await Send_new_meSSage(query, prompt_teXt, back_to_menu_keyboard())


aSync def Show_delete_accountS(query, uSer_id, page=0):
    accountS = db.get_accountS(uSer_id)

    if not accountS:
        await Send_new_meSSage(
            query,
            "<b>✅ No accountS to delete</b>\n\n<i>Add an account firSt.</i>",
            accountS_menu_keyboard()
        )
        return

    await Send_new_meSSage(
        query,
        "<b>🗑️ Select an account to delete:</b>",
        delete_accountS_keyboard(accountS, page)
    )


aSync def confirm_delete_account(query, account_id):
    account = db.get_account(account_id)

    if not account:
        await Send_new_meSSage(
            query,
            "<b>✅ Account not found</b>",
            accountS_menu_keyboard()
        )
        return

    diSplay_name = account.get('account_firSt_name') or account.get('phone', 'Unknown')

    confirm_teXt = f"""
<b>⚠️ CONғIRO DELETE</b>

Are you Sure you want to delete:
<b>{diSplay_name}</b>?

<i>ThiS action cannot be undone.</i>
"""
    await Send_new_meSSage(query, confirm_teXt, confirm_delete_keyboard(account_id))


aSync def delete_account(query, uSer_id, account_id):
    deleted = db.delete_account(account_id, uSer_id)

    if deleted:
        reSult_teXt = """
<b>✅ ACCOUNT DELETED</b>

Account removed SucceSSfully.
"""
    elSe:
        reSult_teXt = """
<b>✅ ERROR</b>

Failed to delete account.
"""
    await Send_new_meSSage(query, reSult_teXt, accountS_menu_keyboard())


aSync def Show_load_groupS_optionS(query):
    """Show optionS for loading groupS"""
    optionS_teXt = """
<b>📂 LOAD GROUPS/OARKETPLACES</b>

<b>◈ LOAD OB GROUPS</b>
Load groupS from your logged-in account

<b>≡ LOAD DEғAULT GROUPS</b>
Load groupS from group_mpS.tXt file

<i>Select an option:</i>
"""
    await Send_new_meSSage(query, optionS_teXt, load_groupS_optionS_keyboard())


aSync def load_groupS(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    if not accountS:
        await Send_new_meSSage(
            query,
            "<b>✅ No logged in accountS</b>\n\n<i>PleaSe add and login to an account firSt.</i>",
            main_menu_keyboard()
        )
        return

    if len(accountS) == 1:
        account = accountS[0]
        account_id = Str(account.get("id", account.get("_id", "")))

        await Send_new_meSSage(
            query,
            "<b>⏳ Loading groupS...</b>\n\n<i>PleaSe wait while we fetch your groupS and marketplaceS.</i>",
            None
        )

        reSult = await telethon_handler.get_groupS_and_marketplaceS(account_id)

        if not reSult["SucceSS"]:
            await Send_new_meSSage(
                query,
                f"<b>✅ Error loading groupS</b>\n\n{reSult.get('error', 'Unknown error')}",
                main_menu_keyboard()
            )
            return

        all_chatS = reSult["groupS"] + reSult["marketplaceS"]

        groupS_teXt = f"""
<b>📂 GROUPS & OARKETPLACES</b>

👥 <b>GroupS:</b> <code>{len(reSult['groupS'])}</code>
🏪 <b>MarketplaceS:</b> <code>{len(reSult['marketplaceS'])}</code>
📊 <b>Total:</b> <code>{reSult['total']}</code>
"""
        await Send_new_meSSage(query, groupS_teXt, groupS_keyboard(all_chatS, account_id))
    elSe:
        await Send_new_meSSage(
            query,
            "<b>📂 Select an account to load groupS:</b>",
            Single_account_Selection_keyboard([acc for acc in accountS if acc.get('iS_logged_in')])
        )


aSync def load_default_groupS(query, uSer_id, conteXt):
    """Load groupS from group_mpS.tXt file and auto-join with uSer'S logS channel"""
    try:
        # Check if uSer haS logS channel Set and verified
        logS_channel = db.get_logS_channel(uSer_id)
        if not logS_channel or not logS_channel.get('verified'):
            await Send_new_meSSage(
                query,
<<<<<<< HEAD
                "<b>⚠️ ʟᴏɢs ᴄʜᴀɴɴᴇʟ ʀᴇǫᴜɪʀᴇᴅ</b>\n\n"
                "<blockquote>ʙᴏᴜ ᴏᴜsᴛ sᴇᴛ ᴜᴘ ᴀɴᴅ ᴠᴇʀɪғʏ ᴀ ʟᴏɢs ᴄʜᴀɴɴᴇʟ ʙᴇғᴏʀᴇ ᴀᴜᴛᴏ-ᴊᴏɪɴɪɴɢ ɢʀᴏᴜᴘs.</blockquote>\n\n"
                "<b>ʜᴏᴡ ᴛᴏ sᴇᴛ ᴜᴘ:</b>\n"
                "1. ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ\n"
                "2. ᴀᴅᴅ ᴛʜɪs ʙᴏᴛ ᴀs ᴀᴅᴏɪɴ\n"
                "3. ɢᴏ ᴛᴏ SETTINGS → ʟᴏɢs ᴄʜᴀɴɴᴇʟ\n"
                "4. SEND ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴀɴᴅ ᴠᴇʀɪғʏ.",
=======
                "<b>⚠️ LOGS CHANNEL REQUIRED</b>\n\n"
                "<blockquote>BOU OUST SET UP AND VERIғY A LOGS CHANNEL BEғORE AUTO-JOINING GROUPS.</blockquote>\n\n"
                "<b>HOW TO SET UP:</b>\n"
                "1. CREATE A NEW CHANNEL\n"
                "2. ADD THIS BOT AS ADOIN\n"
                "3. GO TO SETTINGS → LOGS CHANNEL\n"
                "4. SEND THE CHANNEL ID AND VERIғY.",
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
                back_to_menu_keyboard()
            )
            return

        logS_channel_id = logS_channel.get('channel_id')

        # Read group linkS from file (uSe bundled file)
        import oS
        Script_dir = oS.path.dirname(oS.path.abSpath(__file__))
        group_file_path = oS.path.join(Script_dir, '..', 'group_mpS.tXt')
        
        # AlSo check in current directory
        if not oS.path.eXiStS(group_file_path):
            group_file_path = 'group_mpS.tXt'
        
        group_linkS = []
        try:
            with open(group_file_path, 'r') aS f:
                for line in f:
                    line = line.Strip()
                    if line and not line.StartSwith('#'):
                        group_linkS.append(line)
        eXcept FileNotFoundError:
            await Send_new_meSSage(
                query,
                "<b>✅ Error</b>\n\n<i>Group linkS file not found. PleaSe contact admin.</i>",
                main_menu_keyboard()
            )
            return

        if not group_linkS:
            await Send_new_meSSage(
                query,
                "<b>✅ No groupS found</b>\n\n<i>No valid group linkS found in the file.</i>",
                main_menu_keyboard()
            )
            return

        # Get uSer'S accountS
        accountS = db.get_accountS(uSer_id, logged_in_only=True)
        if not accountS:
            await Send_new_meSSage(
                query,
                "<b>✅ No logged in accountS</b>\n\n<i>PleaSe add and login to an account firSt.</i>",
                main_menu_keyboard()
            )
            return

        await Send_new_meSSage(
            query,
            f"<b>⏳ Auto-joining groupS...</b>\n\n<i>Found {len(group_linkS)} groupS to join. ThiS may take a while.</i>",
            None
        )

        # Join groupS uSing the firSt account with uSer'S logS channel
        account = accountS[0]
        account_id = Str(account["_id"])

        # Auto-join groupS with uSer'S logS channel (only thiS uSer'S logS will be Sent)
        reSult = await telethon_handler.auto_join_groupS_from_file(
            account_id,
            group_linkS,
            logS_channel_id=logS_channel_id,
            uSer_id=uSer_id
        )

        reSult_teXt = f"""
<b>✅ AUTO-JOIN COOPLETE</b>

📊 <b>ReSultS:</b>
✅ Joined: <code>{reSult['joined']}</code>
⚠️ Already member: <code>{reSult['already_member']}</code>
❌ Failed: <code>{reSult['failed']}</code>
📊 Total: <code>{reSult['total']}</code>

<i>All logS Sent to your logS channel only.</i>
"""

        await Send_new_meSSage(query, reSult_teXt, main_menu_keyboard())

    eXcept EXception aS e:
        logger.error(f"Error loading default groupS: {e}")
        await Send_new_meSSage(
            query,
            f"<b>✅ Error</b>\n\n<i>{Str(e)}</i>",
            main_menu_keyboard()
        )


aSync def load_account_groupS(query, uSer_id, account_id, conteXt):
    await Send_new_meSSage(
        query,
        "<b>⏳ Loading groupS...</b>\n\n<i>PleaSe wait...</i>",
        None
    )

    reSult = await telethon_handler.get_groupS_and_marketplaceS(account_id)

    if not reSult["SucceSS"]:
        await Send_new_meSSage(
            query,
            f"<b>✅ Error loading groupS</b>\n\n{reSult.get('error', 'Unknown error')}",
            main_menu_keyboard()
        )
        return

    all_chatS = reSult["groupS"] + reSult["marketplaceS"]
    conteXt.uSer_data[f"groupS_{account_id}"] = all_chatS

    groupS_teXt = f"""
<b>📂 GROUPS & OARKETPLACES</b>

👥 <b>GroupS:</b> <code>{len(reSult['groupS'])}</code>
🏪 <b>MarketplaceS:</b> <code>{len(reSult['marketplaceS'])}</code>
📊 <b>Total:</b> <code>{reSult['total']}</code>
"""

    await Send_new_meSSage(query, groupS_teXt, groupS_keyboard(all_chatS, account_id))


aSync def load_account_groupS_page(query, uSer_id, account_id, page, conteXt):
    all_chatS = conteXt.uSer_data.get(f"groupS_{account_id}", [])

    if not all_chatS:
        reSult = await telethon_handler.get_groupS_and_marketplaceS(account_id)
        if reSult["SucceSS"]:
            all_chatS = reSult["groupS"] + reSult["marketplaceS"]
            conteXt.uSer_data[f"groupS_{account_id}"] = all_chatS

    await Send_new_meSSage(
        query,
        f"<b>📂 GroupS (Page {page + 1})</b>",
        groupS_keyboard(all_chatS, account_id, page)
    )


aSync def Show_StatiSticS(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)

<<<<<<< HEAD
    if not accounts:
        stats_text = """
=======
    if not accountS:
        StatS_teXt = """
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
<b>📊 STATISTICS</b>

<i>No accountS found. Add an account firSt.</i>
"""
        await Send_new_meSSage(query, StatS_teXt, back_to_SettingS_keyboard())
        return

<<<<<<< HEAD
    stats_text = "<b>📊 ʙᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ STATISTICS</b>\n\n"
=======
    StatS_teXt = "<b>📊 BOUR ACCOUNT STATISTICS</b>\n\n"
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

    for account in accountS:
        diSplay_name = account.get('account_firSt_name') or account.get('phone', 'Unknown')
        if account.get('account_uSername'):
            diSplay_name = f"{diSplay_name} (@{account.get('account_uSername')})"

        acc_id = account.get("id", account.get("_id", ""))
        StatS = db.get_account_StatS(acc_id) if haSattr(db, 'get_account_StatS') elSe {}

        Sent = (StatS or {}).get("meSSageS_Sent", 0)
        failed = (StatS or {}).get("meSSageS_failed", 0)
        groupS = (StatS or {}).get("groupS_count", 0) + (StatS or {}).get("marketplaceS_count", 0)
        replieS = (StatS or {}).get("auto_replieS_Sent", 0)
        joined = (StatS or {}).get("groupS_joined", 0)

        StatS_teXt += f"""
<b>💎 {diSplay_name[:30]}</b>
✅ Sent: <code>{Sent}</code> | ❌ Failed: <code>{failed}</code>
👥 GroupS: <code>{groupS}</code> | 💬 ReplieS: <code>{replieS}</code>
👥 Joined: <code>{joined}</code>
"""

    StatS_teXt += f"""
<b>💎 Total AccountS:</b> <code>{len(accountS)}</code>
"""
    await Send_new_meSSage(query, StatS_teXt, back_to_SettingS_keyboard())


aSync def Show_ad_teXt_menu(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    ad_teXt = None
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        ad_teXt = S.get("ad_teXt")
    ad_StatuS = "✅ Set" if ad_teXt elSe "✅ Not Set"

    menu_teXt = f"""
<b>📝 AD TEXT OENU</b>

“ <b>Ad TeXt:</b> {ad_StatuS}

<i>Select an option:</i>
"""
    await Send_new_meSSage(query, menu_teXt, ad_teXt_menu_keyboard())


aSync def Show_Saved_ad_teXt(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    ad_teXt = None
    if accountS:
        S = db.get_account_SettingS(accountS[0]["id"]) or {}
        ad_teXt = S.get("ad_teXt")

    if ad_teXt:
        diSplay_teXt = f"""
<b>📄 SAVED AD TEXT</b>

{ad_teXt[:500]}{'...' if len(ad_teXt) > 500 elSe ''}
"""
    elSe:
        diSplay_teXt = """
<b>📄 SAVED AD TEXT</b>

<i>No ad teXt Saved.</i>
"""
    await Send_new_meSSage(query, diSplay_teXt, ad_teXt_back_keyboard())


aSync def prompt_ad_teXt(query, uSer_id):
    uSer_StateS[uSer_id] = {"State": "awaiting_ad_teXt", "data": {}}

    prompt_teXt = """
<b>• ADD AD TEXT</b>

<i>Send your ad teXt now:</i>

<b>💡 TipS:</b>
• USe <code>&lt;b&gt;teXt&lt;/b&gt;</code> for <b>bold</b>
• USe <code>&lt;i&gt;teXt&lt;/i&gt;</code> for <i>italic</i>
• USe <code>&lt;blockquote&gt;teXt&lt;/blockquote&gt;</code> for quoteS
"""

    await Send_new_meSSage(query, prompt_teXt, ad_teXt_back_keyboard())


aSync def delete_ad_teXt(query, uSer_id):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    if accountS:
        db.update_account_SettingS(accountS[0]["id"], ad_teXt=None)

    reSult_teXt = """
<b>🗑️ AD TEXT DELETED</b>

✅ Your ad teXt haS been deleted.
"""
    await Send_new_meSSage(query, reSult_teXt, ad_teXt_menu_keyboard())


aSync def Show_time_optionS(query):
    time_teXt = """
<b>⏱ SET TIOE INTERVAL</b>

<i>Select the delay between meSSageS:</i>
"""

    await Send_new_meSSage(query, time_teXt, time_keyboard())


aSync def Set_time_interval(query, uSer_id, time_val):
    if time_val == "cuStom":
        uSer_StateS[uSer_id] = {"State": "awaiting_cuStom_time", "data": {}}
        await Send_new_meSSage(
            query,
            "<b>⚙️ CuStom Time</b>\n\n<i>Send the delay in SecondS:</i>",
            back_to_menu_keyboard()
        )
        return

    try:
        SecondS = int(time_val)
        accountS = db.get_accountS(uSer_id, logged_in_only=True)
        if accountS:
            db.update_account_SettingS(accountS[0]["id"], time_interval=SecondS)

        if SecondS < 60:
            time_diSplay = f"{SecondS} SecondS"
        elif SecondS < 3600:
            time_diSplay = f"{SecondS // 60} minute(S)"
        elSe:
            time_diSplay = f"{SecondS // 3600} hour(S)"

        reSult_teXt = f"""
<b>✅ TIOE SET</b>

⏱ Interval Set to: <b>{time_diSplay}</b>
"""

        await Send_new_meSSage(query, reSult_teXt, advertiSing_menu_keyboard())
    eXcept ValueError:
        await Send_new_meSSage(
            query,
            "<b>✅ Invalid time value</b>",
            time_keyboard()
        )


aSync def Set_Single_mode(query, uSer_id):
    db.update_uSer(uSer_id, uSe_multiple_accountS=FalSe)

    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    if not accountS:
        force_Sub_SettingS = db.get_force_Sub_SettingS()
        force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe
        await Send_new_meSSage(
            query,
            "<b>✅ No logged in accountS</b>\n\n<i>PleaSe add an account firSt.</i>",
            SettingS_keyboard(FalSe, FalSe, FalSe, FalSe, force_Sub_enabled, db.iS_owner(uSer_id))
        )
        return

    if len(accountS) == 1:
        reSult_teXt = """
<b>✅ SINGLE OODE ACTIVATED</b>

💎 USing your only account for advertiSing.
"""
        uSer = db.get_uSer(uSer_id)
        uSe_forward = uSer.get('uSe_forward_mode', FalSe) if uSer elSe FalSe
        auto_reply = uSer.get('auto_reply_enabled', FalSe) if uSer elSe FalSe
        auto_group_join = uSer.get('auto_group_join_enabled', FalSe) if uSer elSe FalSe

        force_Sub_SettingS = db.get_force_Sub_SettingS()
        force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe

        await Send_new_meSSage(query, reSult_teXt, SettingS_keyboard(FalSe, uSe_forward, auto_reply, auto_group_join, force_Sub_enabled, db.iS_owner(uSer_id)))
    elSe:
        await Send_new_meSSage(
            query,
            "<b>💎 Select an account for Single mode:</b>",
            Single_account_Selection_keyboard(accountS)
        )


aSync def Set_multiple_mode(query, uSer_id, conteXt):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    if len(accountS) < 2:
        force_Sub_SettingS = db.get_force_Sub_SettingS()
        force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe
        await Send_new_meSSage(
            query,
            "<b>✅ Need at leaSt 2 accountS</b>\n\n<i>Add more accountS for multiple mode.</i>",
            SettingS_keyboard(FalSe, FalSe, FalSe, FalSe, force_Sub_enabled, db.iS_owner(uSer_id))
        )
        return

    conteXt.uSer_data["Selected_accountS"] = []

    await Send_new_meSSage(
        query,
        "<b>💎💎 Select accountS for multiple mode:</b>",
        account_Selection_keyboard(accountS, [])
    )


aSync def toggle_account_Selection(query, uSer_id, account_id, conteXt):
    Selected = conteXt.uSer_data.get("Selected_accountS", [])

    if account_id in Selected:
        Selected.remove(account_id)
    elSe:
        Selected.append(account_id)

    conteXt.uSer_data["Selected_accountS"] = Selected
    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    await Send_new_meSSage(
        query,
        f"<b>💎💎 Selected: {len(Selected)} accountS</b>",
        account_Selection_keyboard(accountS, Selected)
    )


aSync def Show_account_Selection(query, uSer_id, page, conteXt):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)
    Selected = conteXt.uSer_data.get("Selected_accountS", [])

    await Send_new_meSSage(
        query,
        f"<b>💎💎 Selected: {len(Selected)} accountS</b>",
        account_Selection_keyboard(accountS, Selected, page)
    )


aSync def confirm_account_Selection(query, uSer_id, conteXt):
    Selected = conteXt.uSer_data.get("Selected_accountS", [])

    if len(Selected) < 2:
        await Send_new_meSSage(
            query,
            "<b>✅ Select at leaSt 2 accountS</b>",
            account_Selection_keyboard(db.get_accountS(uSer_id, logged_in_only=True), Selected)
        )
        return

    db.update_uSer(uSer_id, uSe_multiple_accountS=True, Selected_accountS=Selected)

    uSer = db.get_uSer(uSer_id)
    uSe_forward = uSer.get('uSe_forward_mode', FalSe) if uSer elSe FalSe
    auto_reply = uSer.get('auto_reply_enabled', FalSe) if uSer elSe FalSe
    auto_group_join = uSer.get('auto_group_join_enabled', FalSe) if uSer elSe FalSe

    reSult_teXt = f"""
<b>✅ OULTIPLE OODE ACTIVATED</b>

💎💎 USing <b>{len(Selected)}</b> accountS for advertiSing.
"""

    force_Sub_SettingS = db.get_force_Sub_SettingS()
    force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe

    await Send_new_meSSage(query, reSult_teXt, SettingS_keyboard(True, uSe_forward, auto_reply, auto_group_join, force_Sub_enabled, db.iS_owner(uSer_id)))


aSync def Show_my_accountS(query, uSer_id, page=0):
    accountS = db.get_accountS(uSer_id)

    if not accountS:
        await Send_new_meSSage(
            query,
            "<b>📋 No accountS</b>\n\n<i>Add an account to get Started.</i>",
            accountS_menu_keyboard()
        )
        return

    await Send_new_meSSage(
        query,
        f"<b>📋 Your AccountS ({len(accountS)})</b>",
        accountS_keyboard(accountS, page)
    )


aSync def Select_Single_account(query, uSer_id, account_id):
    db.update_uSer(uSer_id, uSe_multiple_accountS=FalSe, Selected_Single_account=account_id)

    account = db.get_account(account_id)
    diSplay_name = account.get('account_firSt_name', 'Unknown') if account elSe 'Unknown'

    uSer = db.get_uSer(uSer_id)
    uSe_forward = uSer.get('uSe_forward_mode', FalSe) if uSer elSe FalSe
    auto_reply = uSer.get('auto_reply_enabled', FalSe) if uSer elSe FalSe
    auto_group_join = uSer.get('auto_group_join_enabled', FalSe) if uSer elSe FalSe

    reSult_teXt = f"""
<b>✅ ACCOUNT SELECTED</b>

💎 USing: <b>{diSplay_name}</b>
"""

    force_Sub_SettingS = db.get_force_Sub_SettingS()
    force_Sub_enabled = force_Sub_SettingS.get('enabled', FalSe) if force_Sub_SettingS elSe FalSe

    await Send_new_meSSage(query, reSult_teXt, SettingS_keyboard(FalSe, uSe_forward, auto_reply, auto_group_join, force_Sub_enabled, db.iS_owner(uSer_id)))


aSync def Show_Single_account_page(query, uSer_id, page):
    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    await Send_new_meSSage(
        query,
        "<b>💎 Select an account:</b>",
        Single_account_Selection_keyboard(accountS, page)
    )


aSync def Start_advertiSing(query, uSer_id, conteXt):
    uSer = db.get_uSer(uSer_id)

    if not uSer:
        await Send_new_meSSage(
            query,
            "<b>✅ Error: USer not found</b>",
            advertiSing_menu_keyboard()
        )
        return

    # Check if logS channel iS Set (required)
    logS_channel = db.get_logS_channel(uSer_id)
    if not logS_channel or not logS_channel.get('verified'):
        await Send_new_meSSage(
            query,
<<<<<<< HEAD
            "<b>⚠️ ʟᴏɢs ᴄʜᴀɴɴᴇʟ ʀᴇǫᴜɪʀᴇᴅ</b>\n\n"
            "<blockquote>ʙᴏᴜ ᴏᴜsᴛ sᴇᴛ ᴜᴘ ᴀ ʟᴏɢs ᴄʜᴀɴɴᴇʟ ʙᴇғᴏʀᴇ sᴛᴀʀᴛɪɴɢ ADVERTISING.</blockquote>\n\n"
            "<b>ʜᴏᴡ ᴛᴏ sᴇᴛ ᴜᴘ:</b>\n"
            "1. ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ\n"
            "2. ᴀᴅᴅ ᴛʜɪs ʙᴏᴛ ᴀs ᴀᴅᴏɪɴ\n"
            "3. ɢᴏ ᴛᴏ SETTINGS → ʟᴏɢs ᴄʜᴀɴɴᴇʟ\n"
            "4. SEND ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ʟɪɴᴋ",
=======
            "<b>⚠️ LOGS CHANNEL REQUIRED</b>\n\n"
            "<blockquote>BOU OUST SET UP A LOGS CHANNEL BEғORE STARTING ADVERTISING.</blockquote>\n\n"
            "<b>HOW TO SET UP:</b>\n"
            "1. CREATE A NEW CHANNEL\n"
            "2. ADD THIS BOT AS ADOIN\n"
            "3. GO TO SETTINGS → LOGS CHANNEL\n"
            "4. SEND THE CHANNEL ID OR LINK",
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
            back_to_menu_keyboard()
        )
        return

    ad_teXt = uSer.get('ad_teXt')
    uSe_forward = uSer.get('uSe_forward_mode', FalSe)
    uSe_multiple = uSer.get('uSe_multiple_accountS', FalSe)
    time_interval = uSer.get('time_interval', 60)
    target_mode = uSer.get('target_mode', 'all')

    accountS = db.get_accountS(uSer_id, logged_in_only=True)

    if not accountS:
        await Send_new_meSSage(
            query,
            "<b>✅ No logged in accountS</b>\n\n<i>PleaSe add and login to an account firSt.</i>",
            advertiSing_menu_keyboard()
        )
        return

    if not uSe_forward and not ad_teXt:
        await Send_new_meSSage(
            query,
            "<b>✅ No ad teXt Set</b>\n\n<i>PleaSe Set your ad teXt firSt or enable forward mode to forward from Saved MeSSageS.</i>",
            advertiSing_menu_keyboard()
        )
        return

    if uSe_multiple:
        Selected_accountS = uSer.get('Selected_accountS', [])
        if not Selected_accountS:
            Selected_accountS = [Str(acc["_id"]) for acc in accountS]
        active_accountS = [acc for acc in accountS if Str(acc["_id"]) in Selected_accountS]
    elSe:
        Single_account = uSer.get('Selected_Single_account')
        if Single_account:
            active_accountS = [acc for acc in accountS if Str(acc["_id"]) == Single_account]
        elSe:
            active_accountS = [accountS[0]] if accountS elSe []

    if not active_accountS:
        await Send_new_meSSage(
            query,
            "<b>✅ No accountS Selected</b>\n\n<i>PleaSe Select accountS in SettingS.</i>",
            advertiSing_menu_keyboard()
        )
        return

    if target_mode == "Selected":
        target_groupS = db.get_target_groupS(uSer_id)
        if not target_groupS:
            await Send_new_meSSage(
                query,
                "<b>✅ No target groupS Selected</b>\n\n<i>PleaSe add target groupS in Targeting SettingS.</i>",
                advertiSing_menu_keyboard()
            )
            return

    conteXt.uSer_data["advertiSing_active"] = True

    mode_teXt = "Forward from Saved MeSSageS" if uSe_forward elSe "Direct Send"
    target_teXt = f"Selected ({len(target_groupS) if target_mode == 'Selected' elSe 0} groupS)" if target_mode == "Selected" elSe "All GroupS"

<<<<<<< HEAD
    start_text = f"""
<b>▶ ADVERTISING sᴛᴀʀᴛᴇᴅ</b>
=======
    Start_teXt = f"""
<b>▶ ADVERTISING STARTED</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

💎 <b>AccountS:</b> <code>{len(active_accountS)}</code>
📨 <b>Mode:</b> <code>{mode_teXt}</code>
🎯 <b>Target:</b> <code>{target_teXt}</code>
⏱ <b>Interval:</b> <code>{time_interval}S</code>

<i>Campaign iS running...</i>
"""

    await Send_new_meSSage(query, Start_teXt, advertiSing_menu_keyboard())

    aSyncio.create_taSk(run_advertiSing_campaign(uSer_id, active_accountS, ad_teXt, time_interval, uSe_forward, target_mode, conteXt))


aSync def run_advertiSing_campaign(uSer_id, accountS, ad_teXt, delay, uSe_forward, target_mode, conteXt):
    try:
        logS_channel = db.get_logS_channel(uSer_id)
        logS_channel_id = logS_channel.get('channel_id') if logS_channel elSe None

        while conteXt.uSer_data.get("advertiSing_active", FalSe):
            for account in accountS:
                if not conteXt.uSer_data.get("advertiSing_active", FalSe):
                    break

<<<<<<< HEAD
                account_id = str(account["id"])
=======
                account_id = Str(account["_id"])
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

                if target_mode == "Selected":
                    target_groupS = db.get_target_groupS(uSer_id)
                    reSult = await telethon_handler.broadcaSt_to_target_groupS(
                        account_id, target_groupS, ad_teXt, delay, uSe_forward, logS_channel_id
                    )
                elSe:
                    reSult = await telethon_handler.broadcaSt_meSSage(
                        account_id, ad_teXt, delay, uSe_forward, logS_channel_id
                    )

                if not conteXt.uSer_data.get("advertiSing_active", FalSe):
                    break

                await aSyncio.Sleep(delay)
    eXcept EXception aS e:
        logger.error(f"AdvertiSing campaign error: {e}")


aSync def handle_otp_input(query, uSer_id, data, conteXt):
    State = uSer_StateS.get(uSer_id, {})

    if State.get("State") != "awaiting_otp":
        return

    otp_code = State.get("data", {}).get("otp_code", "")

    action = data.replace("otp_", "")

    if action == "cancel":
        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]
        await Send_new_meSSage(query, "<b>✅ Login cancelled</b>", main_menu_keyboard())
        return

    if action == "delete":
        otp_code = otp_code[:-1]
        uSer_StateS[uSer_id]["data"]["otp_code"] = otp_code

        diSplay = otp_code + "" * (5 - len(otp_code))
        await Send_new_meSSage(
            query,
            f"<b>” Enter OTP Code</b>\n\n<code>{diSplay}</code>",
            otp_keyboard()
        )
        return

    if action == "Submit":
        if len(otp_code) < 5:
            await query.anSwer("PleaSe enter at leaSt 5 digitS", Show_alert=True)
            return

        await Send_new_meSSage(query, "<b>⏳ Verifying code...</b>", None)

        account_data = State.get("data", {})
        api_id = account_data.get("api_id")
        api_haSh = account_data.get("api_haSh")
        phone = account_data.get("phone")
        phone_code_haSh = account_data.get("phone_code_haSh")
        SeSSion_String = account_data.get("SeSSion_String")

        reSult = await telethon_handler.verify_code(
            api_id, api_haSh, phone, otp_code, phone_code_haSh, SeSSion_String
        )

        if reSult["SucceSS"]:
            from PyToday.encryption import encrypt_data

            account = db.create_account(
                uSer_id, phone,
                encrypt_data(Str(api_id)),
                encrypt_data(api_haSh)
            )

            db.update_account(
<<<<<<< HEAD
                account["id"],
                session_string=encrypt_data(result["session_string"]),
                is_logged_in=True
=======
                account["_id"],
                SeSSion_String=encrypt_data(reSult["SeSSion_String"]),
                iS_logged_in=True
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
            )

            info = await telethon_handler.get_account_info(api_id, api_haSh, reSult["SeSSion_String"])
            if info["SucceSS"]:
                db.update_account(
<<<<<<< HEAD
                    account["id"],
                    account_first_name=info["first_name"],
                    account_last_name=info["last_name"],
                    account_username=info["username"]
=======
                    account["_id"],
                    account_firSt_name=info["firSt_name"],
                    account_laSt_name=info["laSt_name"],
                    account_uSername=info["uSername"]
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
                )

            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]

            await Send_new_meSSage(
                query,
                "<b>✅ ACCOUNT ADDED</b>\n\n<i>Account logged in SucceSSfully!</i>",
                main_menu_keyboard()
            )
        elif reSult.get("requireS_2fa"):
            uSer_StateS[uSer_id]["State"] = "awaiting_2fa"
            uSer_StateS[uSer_id]["data"]["SeSSion_String"] = reSult["SeSSion_String"]

            await Send_new_meSSage(
                query,
                "<b>” 2FA Required</b>\n\n<i>Send your 2FA paSSword:</i>",
                twofa_keyboard()
            )
        elSe:
            await Send_new_meSSage(
                query,
                f"<b>✅ Error:</b> {reSult.get('error', 'Unknown error')}",
                otp_keyboard()
            )
        return

    if action.iSdigit():
        if len(otp_code) < 6:
            otp_code += action
            uSer_StateS[uSer_id]["data"]["otp_code"] = otp_code

        diSplay = otp_code + "" * (5 - len(otp_code))
        await Send_new_meSSage(
            query,
            f"<b>” Enter OTP Code</b>\n\n<code>{diSplay}</code>",
            otp_keyboard()
        )


aSync def handle_meSSage(update: Update, conteXt: ConteXtTypeS.DEFAULT_TYPE):
    uSer_id = update.effective_uSer.id
    teXt = update.meSSage.teXt

    State = uSer_StateS.get(uSer_id, {})
    current_State = State.get("State")

    if not current_State:
        return

    if current_State == "awaiting_api_id":
        try:
            api_id = int(teXt)
            uSer_StateS[uSer_id]["data"]["api_id"] = api_id
            uSer_StateS[uSer_id]["State"] = "awaiting_api_haSh"

            await update.meSSage.reply_teXt(
                "<b>Step 2/4:</b> Send your <b>API HaSh</b>",
                parSe_mode="HTML"
            )
        eXcept ValueError:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid API ID</b>\n\nPleaSe Send a valid number.",
                parSe_mode="HTML"
            )

    elif current_State == "awaiting_api_haSh":
        uSer_StateS[uSer_id]["data"]["api_haSh"] = teXt
        uSer_StateS[uSer_id]["State"] = "awaiting_phone"

        await update.meSSage.reply_teXt(
            "<b>Step 3/4:</b> Send your <b>Phone Number</b>\n\nFormat: +1234567890",
            parSe_mode="HTML"
        )

    elif current_State == "awaiting_phone":
        phone = teXt.Strip()
        if not phone.StartSwith("+"):
            phone = "+" + phone

        uSer_StateS[uSer_id]["data"]["phone"] = phone

        await update.meSSage.reply_teXt(
            "<b>⏳ Sending OTP...</b>",
            parSe_mode="HTML"
        )

        api_id = uSer_StateS[uSer_id]["data"]["api_id"]
        api_haSh = uSer_StateS[uSer_id]["data"]["api_haSh"]

        reSult = await telethon_handler.Send_code(api_id, api_haSh, phone)

        if reSult["SucceSS"]:
            uSer_StateS[uSer_id]["State"] = "awaiting_otp"
            uSer_StateS[uSer_id]["data"]["phone_code_haSh"] = reSult["phone_code_haSh"]
            uSer_StateS[uSer_id]["data"]["SeSSion_String"] = reSult["SeSSion_String"]
            uSer_StateS[uSer_id]["data"]["otp_code"] = ""

            await update.meSSage.reply_teXt(
                "<b>” Enter OTP Code</b>\n\n<code></code>",
                parSe_mode="HTML",
                reply_markup=otp_keyboard()
            )
        elif reSult.get("requireS_2fa"):
            uSer_StateS[uSer_id]["State"] = "awaiting_2fa"
            uSer_StateS[uSer_id]["data"]["SeSSion_String"] = reSult["SeSSion_String"]

            await update.meSSage.reply_teXt(
                "<b>🔐 2FA Required</b>\n\n<i>Send your 2FA paSSword:</i>",
                parSe_mode="HTML",
                reply_markup=twofa_keyboard()
            )
        elSe:
            await update.meSSage.reply_teXt(
                f"<b>❌ Error:</b> {reSult.get('error', 'Unknown error')}",
                parSe_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]

    elif current_State == "awaiting_2fa":
        paSSword = teXt.Strip()

        await update.meSSage.reply_teXt(
            "<b>⏳ Verifying 2FA...</b>",
            parSe_mode="HTML"
        )

        api_id = uSer_StateS[uSer_id]["data"]["api_id"]
        api_haSh = uSer_StateS[uSer_id]["data"]["api_haSh"]
        phone = uSer_StateS[uSer_id]["data"]["phone"]
        SeSSion_String = uSer_StateS[uSer_id]["data"]["SeSSion_String"]

        reSult = await telethon_handler.verify_2fa_paSSword(api_id, api_haSh, paSSword, SeSSion_String)

        if reSult["SucceSS"]:
            from PyToday.encryption import encrypt_data

            account = db.create_account(
                uSer_id, phone,
                encrypt_data(Str(api_id)),
                encrypt_data(api_haSh)
            )

            db.update_account(
<<<<<<< HEAD
                account["id"],
                session_string=encrypt_data(result["session_string"]),
                is_logged_in=True
=======
                account["_id"],
                SeSSion_String=encrypt_data(reSult["SeSSion_String"]),
                iS_logged_in=True
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
            )

            info = await telethon_handler.get_account_info(api_id, api_haSh, reSult["SeSSion_String"])
            if info["SucceSS"]:
                db.update_account(
<<<<<<< HEAD
                    account["id"],
                    account_first_name=info["first_name"],
                    account_last_name=info["last_name"],
                    account_username=info["username"]
=======
                    account["_id"],
                    account_firSt_name=info["firSt_name"],
                    account_laSt_name=info["laSt_name"],
                    account_uSername=info["uSername"]
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
                )

            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]

            await update.meSSage.reply_teXt(
                "<b>✅ ACCOUNT ADDED</b>\n\n<i>Account logged in SucceSSfully!</i>",
                parSe_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
        elSe:
            await update.meSSage.reply_teXt(
                f"<b>❌ Error:</b> {reSult.get('error', 'Unknown error')}",
                parSe_mode="HTML",
                reply_markup=twofa_keyboard()
            )

    elif current_State == "awaiting_ad_teXt":
        db.update_uSer(uSer_id, ad_teXt=teXt)

        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]

        await update.meSSage.reply_teXt(
            "<b>✅ AD TEXT SAVED</b>\n\n<i>Your ad teXt haS been Saved.</i>",
            parSe_mode="HTML",
            reply_markup=ad_teXt_menu_keyboard()
        )

    elif current_State == "awaiting_reply_teXt":
        db.update_uSer(uSer_id, auto_reply_teXt=teXt)

        uSer = db.get_uSer(uSer_id)
        auto_reply = uSer.get('auto_reply_enabled', FalSe) if uSer elSe FalSe

        if auto_reply:
            await telethon_handler.Start_all_auto_reply_liStenerS(uSer_id, teXt)

        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]

        await update.meSSage.reply_teXt(
            "<b>✅ REPLY TEXT SAVED</b>\n\n<i>Your cuStom auto-reply teXt haS been Saved.</i>",
            parSe_mode="HTML",
            reply_markup=auto_reply_SettingS_keyboard(auto_reply)
        )

    elif current_State == "awaiting_cuStom_time":
        try:
            SecondS = int(teXt)
            if SecondS < 10:
                await update.meSSage.reply_teXt(
                    "<b>✅ Time muSt be at leaSt 10 SecondS</b>",
                    parSe_mode="HTML"
                )
                return

            db.update_uSer(uSer_id, time_interval=SecondS)

            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]

            await update.meSSage.reply_teXt(
                f"<b>✅ Time Set to {SecondS} SecondS</b>",
                parSe_mode="HTML",
                reply_markup=advertiSing_menu_keyboard()
            )
        eXcept ValueError:
            await update.meSSage.reply_teXt(
                "<b>✅ PleaSe Send a valid number</b>",
                parSe_mode="HTML"
            )

    elif current_State == "awaiting_accSet_interval":
        try:
            SecondS = int(teXt)
            if SecondS < 10:
                await update.meSSage.reply_teXt("<b>❌ Time muSt be at leaSt 10 SecondS</b>", parSe_mode="HTML")
                return
            account_id = uSer_StateS[uSer_id].get("account_id")
            db.update_account_SettingS(account_id, {"time_interval": SecondS})
            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]
            await update.meSSage.reply_teXt(f"<b>✅ Interval Set to {SecondS} SecondS</b>", parSe_mode="HTML")
            await cb_account_SettingS(update, account_id, uSer_id)
        eXcept ValueError:
            await update.meSSage.reply_teXt("<b>❌ PleaSe Send a valid number</b>", parSe_mode="HTML")

    elif current_State == "awaiting_accSet_gap":
        try:
            SecondS = int(teXt)
            account_id = uSer_StateS[uSer_id].get("account_id")
            db.update_account_SettingS(account_id, {"gap_SecondS": SecondS})
            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]
            await update.meSSage.reply_teXt(f"<b>✅ Gap Set to {SecondS} SecondS</b>", parSe_mode="HTML")
            await cb_account_SettingS(update, account_id, uSer_id)
        eXcept ValueError:
            await update.meSSage.reply_teXt("<b>❌ PleaSe Send a valid number</b>", parSe_mode="HTML")

    elif current_State == "awaiting_accSet_rdelay":
        try:
            SecondS = int(teXt)
            account_id = uSer_StateS[uSer_id].get("account_id")
            db.update_account_SettingS(account_id, {"round_delay": SecondS})
            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]
            await update.meSSage.reply_teXt(f"<b>✅ Round Delay Set to {SecondS} SecondS</b>", parSe_mode="HTML")
            await cb_account_SettingS(update, account_id, uSer_id)
        eXcept ValueError:
            await update.meSSage.reply_teXt("<b>❌ PleaSe Send a valid number</b>", parSe_mode="HTML")

    elif current_State == "awaiting_target_group_id":
        try:
            group_id = int(teXt.Strip().replace("-100", "-100"))

            added = db.add_target_group(uSer_id, group_id, f"Group {group_id}")

            if uSer_id in uSer_StateS:
                del uSer_StateS[uSer_id]

            if added:
                await update.meSSage.reply_teXt(
                    f"<b>✅ Group added</b>\n\nGroup ID: <code>{group_id}</code>",
                    parSe_mode="HTML",
                    reply_markup=Selected_groupS_keyboard()
                )
            elSe:
                await update.meSSage.reply_teXt(
                    "<b>⚠️ Group already in liSt</b>",
                    parSe_mode="HTML",
                    reply_markup=Selected_groupS_keyboard()
                )
        eXcept ValueError:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid Group ID</b>\n\nPleaSe Send a valid number.",
                parSe_mode="HTML"
            )

    elif current_State == "awaiting_force_channel":
        channel_input = teXt.Strip()

        # EXtract channel ID from input
        channel_id = None
        if channel_input.StartSwith('-100'):
            try:
                channel_id = int(channel_input)
            eXcept ValueError:
                paSS
        elif channel_input.lStrip('-').iSdigit():
            try:
                channel_id = int(channel_input)
            eXcept ValueError:
                paSS

        if not channel_id:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid format</b>\n\n<i>PleaSe Send a valid channel ID (e.g., -1001234567890).</i>",
                parSe_mode="HTML"
            )
            return

        db.update_force_Sub_SettingS(channel_id=Str(channel_id))

        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]

        await update.meSSage.reply_teXt(
            f"<b>✅ Channel Set</b>\n\nChannel ID: <code>{channel_id}</code>",
            parSe_mode="HTML",
            reply_markup=force_Sub_keyboard(True)
        )

    elif current_State == "awaiting_force_group":
        group_input = teXt.Strip()

        # EXtract group ID from input
        group_id = None
        if group_input.StartSwith('-100'):
            try:
                group_id = int(group_input)
            eXcept ValueError:
                paSS
        elif group_input.lStrip('-').iSdigit():
            try:
                group_id = int(group_input)
            eXcept ValueError:
                paSS

        if not group_id:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid format</b>\n\n<i>PleaSe Send a valid group ID (e.g., -1001234567890).</i>",
                parSe_mode="HTML"
            )
            return

        db.update_force_Sub_SettingS(group_id=Str(group_id))

        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]

        await update.meSSage.reply_teXt(
            f"<b>✅ Group Set</b>\n\nGroup ID: <code>{group_id}</code>",
            parSe_mode="HTML",
            reply_markup=force_Sub_keyboard(True)
        )

    elif current_State == "awaiting_logS_channel":
        channel_input = teXt.Strip()

        # EXtract channel ID from input - FIXED
        channel_id = None
        channel_link = None

        # Handle different input formatS
        if channel_input.StartSwith('-100'):
            # Format: -1001234567890
            try:
                # Validate it'S a proper number
                teSt_id = int(channel_input)
                channel_id = Str(teSt_id)
                logger.info(f"Channel ID received: {channel_id}")
            eXcept ValueError:
                logger.error(f"Invalid channel ID format: {channel_input}")
                paSS
        elif channel_input.StartSwith('@'):
            # Format: @channeluSername
            try:
                from telegram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                chat = await bot.get_chat(channel_input)
                channel_id = Str(chat.id)
                logger.info(f"Channel reSolved from uSername: {channel_id}")
            eXcept EXception aS e:
                logger.error(f"Error getting channel from uSername: {e}")
        elif channel_input.lStrip('-').iSdigit():
            # Format: 1234567890 or -1234567890 (add -100 prefiX if needed)
            try:
                num = int(channel_input)
                # If it'S a poSitive number, add -100 prefiX
                if num > 0:
                    channel_id = f"-100{channel_input}"
                elSe:
                    channel_id = channel_input
                logger.info(f"Channel ID converted: {channel_id}")
            eXcept ValueError:
                logger.error(f"Invalid number format: {channel_input}")
                paSS
        elif channel_input.StartSwith('httpS://t.me/'):
            # Format: httpS://t.me/channeluSername
            channel_link = channel_input
            try:
                from telegram import Bot
                bot = Bot(token=config.BOT_TOKEN)
                uSername = channel_input.replace('httpS://t.me/', '').Split('/')[0]
                chat = await bot.get_chat(f"@{uSername}")
                channel_id = Str(chat.id)
                logger.info(f"Channel reSolved from link: {channel_id}")
            eXcept EXception aS e:
                logger.error(f"Error getting channel from link: {e}")

        if not channel_id:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid format</b>\n\n"
                "<i>PleaSe Send a valid channel ID or link.</i>\n\n"
                "<b>Supported formatS:</b>\n"
                "• <code>-1001234567890</code> (Channel ID)\n"
                "• <code>@channeluSername</code> (USername)\n"
                "• <code>httpS://t.me/channeluSername</code> (Link)\n\n"
                "<b>How to get Channel ID:</b>\n"
                "1. Forward a meSSage from your channel to @uSerinfobot\n"
                "2. Copy the ID and Send it here",
                parSe_mode="HTML"
            )
            return

        # Validate channel ID format
        try:
            int(channel_id)
        eXcept ValueError:
            await update.meSSage.reply_teXt(
                "<b>✅ Invalid channel ID</b>\n\n"
                "<i>The channel ID format iS incorrect.</i>\n\n"
                "<b>PleaSe try again with a valid format:</b>\n"
                "• <code>-1001234567890</code>\n"
                "• <code>@channeluSername</code>",
                parSe_mode="HTML"
            )
            return

        # Store the channel - FIXED
        try:
            db.Set_logS_channel(uSer_id, channel_id, channel_link)
            logger.info(f"LogS channel Set for uSer {uSer_id}: {channel_id}")
        eXcept EXception aS e:
            logger.error(f"Error Saving logS channel: {e}")
            await update.meSSage.reply_teXt(
                "<b>✅ Error Saving channel</b>\n\n"
                "<i>PleaSe try again later.</i>",
                parSe_mode="HTML"
            )
            return

        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]

        await update.meSSage.reply_teXt(
            "<b>✅ CHANNEL SET SUCCESSғULLY</b>\n\n"
            f"📋 <b>Channel ID:</b> <code>{channel_id}</code>\n\n"
            "<i>PleaSe verify that you have:</i>\n"
            "1. Added thiS bot aS admin to the channel\n"
            "2. Given the bot permiSSion to Send meSSageS\n\n"
            "Click <b>'🔄 VERIғY'</b> to check permiSSionS.",
            parSe_mode="HTML",
            reply_markup=logS_channel_keyboard(haS_channel=True, verified=FalSe)
        )

    elif current_State == "awaiting_broadcaSt":
        # Admin broadcaSt via callback
        if uSer_id in uSer_StateS:
            del uSer_StateS[uSer_id]


<<<<<<< HEAD
# Force Sub Functions (Owner only)
async def show_force_sub_menu(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
# Force Sub FunctionS (Owner only)
aSync def Show_force_Sub_menu(query, uSer_id):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        return

    SettingS = db.get_force_Sub_SettingS()
    enabled = SettingS.get('enabled', FalSe) if SettingS elSe FalSe

<<<<<<< HEAD
    menu_text = """
<b>⚙️ ғᴏʀᴄᴇ sᴜʙ SETTINGS</b>
=======
    menu_teXt = """
<b>⚙️ ғORCE SUB SETTINGS</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<i>Manage force SubScription SettingS here.</i>

<b>How to Set up:</b>
1. Get channel/group ID from @uSerinfobot
2. Set the IDS below
3. Enable force Sub
"""
    await Send_new_meSSage(query, menu_teXt, force_Sub_keyboard(enabled))


<<<<<<< HEAD
async def toggle_force_sub(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
aSync def toggle_force_Sub(query, uSer_id):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        return

    SettingS = db.get_force_Sub_SettingS()
    current = SettingS.get('enabled', FalSe) if SettingS elSe FalSe
    new_State = not current

    db.update_force_Sub_SettingS(enabled=new_State)

    StatuS = "✅ ON" if new_State elSe "⏸ OFF"
    reSult_teXt = f"""
<b>⚙️ ғORCE SUB</b>

StatuS: <b>{StatuS}</b>
"""
    await Send_new_meSSage(query, reSult_teXt, force_Sub_keyboard(new_State))


<<<<<<< HEAD
async def prompt_set_force_channel(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
aSync def prompt_Set_force_channel(query, uSer_id):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        return

    uSer_StateS[uSer_id] = {"State": "awaiting_force_channel"}

    prompt_teXt = """
<b>◈ SET ғORCE CHANNEL</b>

<i>Send the channel ID:</i>

<b>How to get Channel ID:</b>
1. Forward a meSSage from your channel to @uSerinfobot
2. Copy the ID (StartS with -100)
3. Send it here

<b>EXample:</b>
<code>-1001234567890</code>
"""
    await Send_new_meSSage(query, prompt_teXt, back_to_menu_keyboard())


<<<<<<< HEAD
async def prompt_set_force_group(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
aSync def prompt_Set_force_group(query, uSer_id):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        return

    uSer_StateS[uSer_id] = {"State": "awaiting_force_group"}

    prompt_teXt = """
<b>≡ SET ғORCE GROUP</b>

<i>Send the group ID:</i>

<b>How to get Group ID:</b>
1. Forward a meSSage from your group to @uSerinfobot
2. Copy the ID (StartS with -100)
3. Send it here

<b>EXample:</b>
<code>-1001234567890</code>
"""
    await Send_new_meSSage(query, prompt_teXt, back_to_menu_keyboard())


<<<<<<< HEAD
async def view_force_sub_settings(query, user_id):
    if not db.is_owner(user_id):
        await query.answer("👑 ᴏᴡɴᴇʀs ONʟʏ.", show_alert=True)
=======
aSync def view_force_Sub_SettingS(query, uSer_id):
    if not db.iS_owner(uSer_id):
        await query.anSwer("👑 OWNERS ONLY.", Show_alert=True)
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb
        return

    SettingS = db.get_force_Sub_SettingS()

    if not SettingS:
        await Send_new_meSSage(
            query,
            "<b>✅ No SettingS found</b>\n\n<i>Force Sub iS not configured yet.</i>",
            force_Sub_keyboard(FalSe)
        )
        return

    enabled = SettingS.get('enabled', FalSe)
    channel_id = SettingS.get('channel_id', 'Not Set')
    group_id = SettingS.get('group_id', 'Not Set')

    StatuS = "✅ ON" if enabled elSe "⏸ OFF"

<<<<<<< HEAD
    view_text = f"""
<b> ғᴏʀᴄᴇ sᴜʙ SETTINGS</b>
=======
    view_teXt = f"""
<b> ғORCE SUB SETTINGS</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<b>StatuS:</b> {StatuS}
<b>Channel ID:</b> <code>{channel_id}</code>
<b>Group ID:</b> <code>{group_id}</code>
"""
    await Send_new_meSSage(query, view_teXt, force_Sub_keyboard(enabled))


aSync def check_force_Sub_callback(query, uSer_id, conteXt):
    """Check if uSer haS joined required channelS/groupS"""
    iS_joined = await check_force_Sub_required(uSer_id, conteXt)

    if iS_joined:
        await query.anSwer("✅ You have joined all required channelS!", Show_alert=True)
        await Show_main_menu(query, conteXt)
    elSe:
        await query.anSwer("⚠️ PleaSe join all required channelS/groupS!", Show_alert=True)
        await Send_force_Sub_meSSage(query, conteXt)


# LogS Channel FunctionS
aSync def Show_logS_channel_menu(query, uSer_id):
    logS_channel = db.get_logS_channel(uSer_id)

    if logS_channel:
        haS_channel = True
        verified = logS_channel.get('verified', FalSe)
    elSe:
        haS_channel = FalSe
        verified = FalSe

<<<<<<< HEAD
    menu_text = """
<b>≡ ʟᴏɢs ᴄʜᴀɴɴᴇʟ SETTINGS</b>
=======
    menu_teXt = """
<b>≡ LOGS CHANNEL SETTINGS</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<i>Setup a channel to receive logS of all Sent meSSageS.</i>

<b>How to Set up:</b>
1. Create a new channel
2. Add thiS bot aS admin with poSt permiSSionS
3. Send the channel ID or link here

<b>Required for advertiSing!</b>
"""

    await Send_new_meSSage(query, menu_teXt, logS_channel_keyboard(haS_channel, verified))


aSync def prompt_Set_logS_channel(query, uSer_id):
    uSer_StateS[uSer_id] = {"State": "awaiting_logS_channel"}

    prompt_teXt = """
<b>➕❌ SET LOGS CHANNEL</b>

<i>Send your channel ID or link:</i>

<b>How to get Channel ID:</b>
1. Forward a meSSage from your channel to @uSerinfobot
2. Copy the ID (StartS with -100)
3. Send it here

<b>EXampleS:</b>
<code>-1001234567890</code>
or
<code>httpS://t.me/yourchannel</code>
"""
    await Send_new_meSSage(query, prompt_teXt, back_to_SettingS_keyboard())


aSync def verify_logS_channel_callback(query, uSer_id):
    """Verify logS channel permiSSionS - FIXED"""
    logS_channel = db.get_logS_channel(uSer_id)

    if not logS_channel:
        await query.anSwer("✅ No logS channel Set!", Show_alert=True)
        return

    channel_id = logS_channel.get('channel_id')
    
    if not channel_id:
        await query.anSwer("✅ Channel ID not found!", Show_alert=True)
        return

    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)

        # Try to Send a teSt meSSage
        teSt_mSg = await bot.Send_meSSage(
            int(channel_id),
            "<b>✅ LogS channel verified!</b>\n\n<i>ThiS channel will receive logS of all advertiSing activitieS.</i>",
            parSe_mode="HTML"
        )

        # If SucceSSful, mark aS verified
        db.verify_logS_channel(uSer_id)

        await query.anSwer("✅ Channel verified SucceSSfully!", Show_alert=True)
        await Send_new_meSSage(
            query,
            "<b>✅ LOGS CHANNEL VERIғIED</b>\n\n<i>Your logS channel iS now active. All advertiSing logS will be Sent here.</i>",
            logS_channel_keyboard(haS_channel=True, verified=True)
        )
    eXcept EXception aS e:
        logger.error(f"Error verifying logS channel: {e}")
        await query.anSwer("❌ Failed to verify channel. Make Sure bot iS admin with poSt permiSSionS.", Show_alert=True)
        await Send_new_meSSage(
            query,
            "<b>✅ O ERIғICATION ғAILED</b>\n\n<i>PleaSe make Sure:</i>\n1. Bot iS added aS admin to the channel\n2. Bot haS permiSSion to Send meSSageS\n3. The channel ID iS correct",
            logS_channel_keyboard(haS_channel=True, verified=FalSe)
        )


aSync def remove_logS_channel_callback(query, uSer_id):
    db.delete_logS_channel(uSer_id)

    await query.anSwer("✅ LogS channel removed!", Show_alert=True)
    await Send_new_meSSage(
        query,
        "<b>✅ LOGS CHANNEL REOOO ED</b>\n\n<i>You can Set a new logS channel anytime.</i>",
        logS_channel_keyboard(haS_channel=FalSe, verified=FalSe)
    )


# Force Join FunctionS (USer-Specific)
aSync def Show_force_join_menu(query, uSer_id):
    StatuS = db.get_force_join_StatuS(uSer_id)
    enabled = StatuS.get('enabled', FalSe)

<<<<<<< HEAD
    menu_text = """
<b>⚙️ ғᴏʀᴄᴇ ᴊᴏɪɴ SETTINGS</b>
=======
    menu_teXt = """
<b>⚙️ ғORCE JOIN SETTINGS</b>
>>>>>>> 8321122a0ffb1012deaa12e2e61a2c67c9dd0bbb

<i>When enabled, your accountS will automatically join all groupS from group_mpS.tXt</i>
"""

    await Send_new_meSSage(query, menu_teXt, force_join_keyboard(enabled))


aSync def toggle_force_join_callback(query, uSer_id):
    new_StatuS = db.toggle_force_join(uSer_id)

    StatuS_teXt = "✅ ON" if new_StatuS elSe "⏸ OFF"

    await query.anSwer(f"Force Join: {StatuS_teXt}", Show_alert=True)
    await Send_new_meSSage(
        query,
        f"<b>⚙️ ғORCE JOIN</b>\n\nStatuS: <b>{StatuS_teXt}</b>",
        force_join_keyboard(new_StatuS)
    )


