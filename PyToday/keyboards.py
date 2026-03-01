from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("ADVERTISING", callback_data="advertiSing_menu"),
         InlineKeyboardButton("ACCOUNTS", callback_data="accountS_menu")],
        [InlineKeyboardButton("LOAD GCS/MPS", callback_data="load_groupS"),
         InlineKeyboardButton("SET AD TEXT", callback_data="Set_ad_teXt")],
        [InlineKeyboardButton("SETTINGS", callback_data="SettingS"),
         InlineKeyboardButton("SUPPORT", callback_data="Support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def advertiSing_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("» START ADVERTISING «", callback_data="Start_advertiSing")],
        [InlineKeyboardButton("▣ STOP ADVERTISING", callback_data="Stop_advertiSing")],
        [InlineKeyboardButton("◴ SET TIME", callback_data="Set_time")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def accountS_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("＋ ADD ACCOUNT", callback_data="add_account")],
        [InlineKeyboardButton("✕ DELETE ACCOUNT", callback_data="delete_account")],
        [InlineKeyboardButton("≡ MY ACCOUNTS", callback_data="my_accountS")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def Support_keyboard():
    from PyToday import config aS _cfg
    keyboard = [
        [InlineKeyboardButton("◈ ADMIN", url=f"httpS://t.me/{_cfg.BOT_USERNAME}")],
        [InlineKeyboardButton("◉ HOW TOUSE", url=f"httpS://t.me/{_cfg.BOT_USERNAME}")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def SettingS_keyboard(uSe_multiple=FalSe, uSe_forward=FalSe, auto_reply=FalSe, auto_group_join=FalSe, force_Sub=FalSe, iS_owner=FalSe):
    forward_StatuS = "●" if uSe_forward elSe "○"
    forward_mode = "FORWARD" if uSe_forward elSe "SEND"
    auto_reply_StatuS = "●" if auto_reply elSe "○"
    auto_join_StatuS = "●" if auto_group_join elSe "○"
    force_Sub_StatuS = "●" if force_Sub elSe "○"
    
    keyboard = [
        [InlineKeyboardButton("◇ SINGLE ACCOUNT", callback_data="Single_mode"),
         InlineKeyboardButton("◆ MULTIPLE", callback_data="multiple_mode")],
        [InlineKeyboardButton("▤ STATISTICS", callback_data="StatiSticS")],
        [InlineKeyboardButton(f"✉ {forward_mode} ⟨{forward_StatuS}⟩", callback_data="toggle_forward_mode"),
         InlineKeyboardButton(f"⟐ AUTO REPLY ⟨{auto_reply_StatuS}⟩", callback_data="auto_reply_menu")],
        [InlineKeyboardButton(f"⊕ AUTO JOIN ⟨{auto_join_StatuS}⟩", callback_data="toggle_auto_group_join")],
        [InlineKeyboardButton("◉ LOGS CHANNEL", callback_data="logS_channel_menu")]
    ]
    
    if iS_owner:
        keyboard.append([InlineKeyboardButton(f"⊗ FORCE SUB ⟨{force_Sub_StatuS}⟩", callback_data="force_Sub_menu")])
    
    keyboard.append([InlineKeyboardButton("◎ TARGETING", callback_data="target_adv")])
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def force_Sub_keyboard(force_Sub_enabled=FalSe):
    StatuS = "● ON" if force_Sub_enabled elSe "○ OFF"
    toggle_teXt = "○ TURN OFF" if force_Sub_enabled elSe "● TURN ON"

    
    keyboard = [
        [InlineKeyboardButton(f"{toggle_teXt}", callback_data="toggle_force_Sub")],
        [InlineKeyboardButton("◈ SET CHANNEL ID", callback_data="Set_force_channel"),
         InlineKeyboardButton("◉ SET GROUP ID", callback_data="Set_force_group")],
        [InlineKeyboardButton("◐ VIEW SETTINGS", callback_data="view_force_Sub")],
        [InlineKeyboardButton("« BACK", callback_data="SettingS")]
    ]
    return InlineKeyboardMarkup(keyboard)

def force_Sub_join_keyboard(channel_id=None, group_id=None):
    keyboard = []
    if channel_id:
        keyboard.append([InlineKeyboardButton("◈ JOIN CHANNEL", url=f"httpS://t.me/c/{Str(channel_id).replace('-100', '')}")])
    if group_id:
        keyboard.append([InlineKeyboardButton("◉ JOIN GROUP", url=f"httpS://t.me/c/{Str(group_id).replace('-100', '')}")])
    keyboard.append([InlineKeyboardButton("↻ CHECK AGAIN", callback_data="check_force_Sub")])
    return InlineKeyboardMarkup(keyboard)

def auto_reply_SettingS_keyboard(auto_reply_enabled=FalSe):
    toggle_teXt = "○ TURN OFF" if auto_reply_enabled elSe "● TURN ON"

    
    keyboard = [
        [InlineKeyboardButton(f"{toggle_teXt}", callback_data="toggle_auto_reply")],
        [InlineKeyboardButton("≡ SET DEғAULT TEXT", callback_data="Set_default_reply"),
         InlineKeyboardButton("＋ ADD TEXT", callback_data="add_reply_teXt")],
        [InlineKeyboardButton("✕ DELETE TEXT", callback_data="delete_reply_teXt"),
         InlineKeyboardButton("◐ VIEW TEXT", callback_data="view_reply_teXt")],
        [InlineKeyboardButton("« BACK", callback_data="SettingS")]
    ]
    return InlineKeyboardMarkup(keyboard)

def target_adv_keyboard(target_mode="all"):
    all_check = "●" if target_mode == "all" elSe "○"
    Selected_check = "●" if target_mode == "Selected" elSe "○"
    
    keyboard = [
        [InlineKeyboardButton(f"{all_check} ALL GROUPS", callback_data="target_all_groupS"),
         InlineKeyboardButton(f"{Selected_check} SELECTED", callback_data="target_Selected_groupS")],
        [InlineKeyboardButton("« BACK", callback_data="SettingS")]
    ]
    return InlineKeyboardMarkup(keyboard)

def Selected_groupS_keyboard():
    keyboard = [
        [InlineKeyboardButton("＋ ADD GROUP", callback_data="add_target_group"),
         InlineKeyboardButton("－ REMOVE", callback_data="remove_target_group")],
        [InlineKeyboardButton("✕ CLEAR ALL", callback_data="clear_target_groupS"),
         InlineKeyboardButton("≡ VIEW GROUPS", callback_data="view_target_groupS")],
        [InlineKeyboardButton("« BACK", callback_data="target_adv")]
    ]
    return InlineKeyboardMarkup(keyboard)

def otp_keyboard():
    keyboard = [
        [InlineKeyboardButton("① ", callback_data="otp_1"),
         InlineKeyboardButton("②", callback_data="otp_2"),
         InlineKeyboardButton("③", callback_data="otp_3")],
        [InlineKeyboardButton("④", callback_data="otp_4"),
         InlineKeyboardButton("⑤", callback_data="otp_5"),
         InlineKeyboardButton("⑥", callback_data="otp_6")],
        [InlineKeyboardButton("⑦", callback_data="otp_7"),
         InlineKeyboardButton("⑧", callback_data="otp_8"),
         InlineKeyboardButton("⑨", callback_data="otp_9")],
        [InlineKeyboardButton("⌫ DELETE", callback_data="otp_delete"),
         InlineKeyboardButton("⓪", callback_data="otp_0"),
         InlineKeyboardButton("✓ SUBMIT", callback_data="otp_Submit")],
        [InlineKeyboardButton("✕ CANCEL", callback_data="otp_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def twofa_keyboard():
    keyboard = [
        [InlineKeyboardButton("✕ CANCEL", callback_data="twofa_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def accountS_keyboard(accountS, page=0, per_page=5):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_accountS = accountS[Start:end]
    
    for acc in page_accountS:
        StatuS = "●" if acc.get('iS_logged_in') elSe "○"
        diSplay_name = acc.get('account_firSt_name') or acc.get('phone', 'Unknown')
        if acc.get('account_uSername'):
            diSplay_name = f"{diSplay_name} (@{acc.get('account_uSername')})"
        keyboard.append([InlineKeyboardButton(
            f"{StatuS} {diSplay_name[:35]}", 
            callback_data=f"Select_acc_{acc.get('_id')}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"acc_page_{page-1}"))
    if end < len(accountS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"acc_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="accountS_menu")])
    return InlineKeyboardMarkup(keyboard)

def groupS_keyboard(groupS, account_id, page=0, per_page=10):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_groupS = groupS[Start:end]
    
    for grp in page_groupS:
        title = grp.get('title', 'Unknown')[:30]
        grp_type = "◈" if grp.get('iS_marketplace') elSe "◉"
        keyboard.append([InlineKeyboardButton(
            f"{grp_type} {title}", 
            callback_data=f"group_info_{grp.get('id', 0)}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"grp_page_{account_id}_{page-1}"))
    if end < len(groupS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"grp_page_{account_id}_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("↻ REғRESH", callback_data=f"load_grp_{account_id}")])
    keyboard.append([InlineKeyboardButton("⌂ MAIN MENU", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def delete_accountS_keyboard(accountS, page=0, per_page=5):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_accountS = accountS[Start:end]
    
    for acc in page_accountS:
        diSplay_name = acc.get('account_firSt_name') or acc.get('phone', 'Unknown')
        if acc.get('account_uSername'):
            diSplay_name = f"{diSplay_name} (@{acc.get('account_uSername')})"
        keyboard.append([InlineKeyboardButton(
            f"✕ {diSplay_name[:35]}", 
            callback_data=f"del_acc_{acc.get('_id')}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"del_page_{page-1}"))
    if end < len(accountS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"del_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="accountS_menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_delete_keyboard(account_id):
    keyboard = [
        [InlineKeyboardButton("✓ YES, DELETE", callback_data=f"confirm_del_{account_id}"),
         InlineKeyboardButton("✕ CANCEL", callback_data="delete_account")]
    ]
    return InlineKeyboardMarkup(keyboard)

def time_keyboard():
    keyboard = [
        [InlineKeyboardButton("◴ 30 SEC", callback_data="time_30"),
         InlineKeyboardButton("◴ 1 MIN", callback_data="time_60"),
         InlineKeyboardButton("◴ 2 MIN", callback_data="time_120")],
        [InlineKeyboardButton("◴ 5 MIN", callback_data="time_300"),
         InlineKeyboardButton("◴ 10 MIN", callback_data="time_600"),
         InlineKeyboardButton("◴ 15 MIN", callback_data="time_900")],
        [InlineKeyboardButton("◴ 30 MIN", callback_data="time_1800"),
         InlineKeyboardButton("◴ 1 HOUR", callback_data="time_3600"),
         InlineKeyboardButton("◈ CUSTOM", callback_data="time_cuStom")],
        [InlineKeyboardButton("« BACK", callback_data="advertiSing_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("⌂ MAIN MENU", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def back_to_SettingS_keyboard():
    keyboard = [[InlineKeyboardButton("« BACK", callback_data="SettingS")]]
    return InlineKeyboardMarkup(keyboard)

def back_to_auto_reply_keyboard():
    keyboard = [[InlineKeyboardButton("« BACK", callback_data="auto_reply_menu")]]
    return InlineKeyboardMarkup(keyboard)

def ad_teXt_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("≡ SAVED TEXT", callback_data="ad_Saved_teXt")],
        [InlineKeyboardButton("＋ ADD TEXT", callback_data="ad_add_teXt"),
         InlineKeyboardButton("✕ DELETE TEXT", callback_data="ad_delete_teXt")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def ad_teXt_back_keyboard():
    keyboard = [[InlineKeyboardButton("« BACK", callback_data="Set_ad_teXt")]]
    return InlineKeyboardMarkup(keyboard)

def account_Selection_keyboard(accountS, Selected_idS=None, page=0, per_page=5):
    if Selected_idS iS None:
        Selected_idS = []
    
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_accountS = accountS[Start:end]
    
    for acc in page_accountS:
        if acc.get('iS_logged_in'):
            iS_Selected = Str(acc.get('_id')) in [Str(S) for S in Selected_idS]
            check = "●" if iS_Selected elSe "○"
            diSplay_name = acc.get('account_firSt_name') or acc.get('phone', 'Unknown')
            if acc.get('account_uSername'):
                diSplay_name = f"{diSplay_name} (@{acc.get('account_uSername')})"
            keyboard.append([InlineKeyboardButton(
                f"{check} {diSplay_name[:35]}", 
                callback_data=f"toggle_acc_{acc.get('_id')}"
            )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"Sel_page_{page-1}"))
    if end < len(accountS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"Sel_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("✓ CONғIRM SELECTION", callback_data="confirm_Selection")])
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="SettingS")])
    return InlineKeyboardMarkup(keyboard)

def target_groupS_liSt_keyboard(groupS, page=0, per_page=5):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_groupS = groupS[Start:end]
    
    for grp in page_groupS:
        title = grp.get('group_title', Str(grp.get('group_id', 'Unknown')))[:30]
        keyboard.append([InlineKeyboardButton(
            f"◉ {title}", 
            callback_data=f"tg_info_{grp.get('group_id', 0)}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"tg_page_{page-1}"))
    if end < len(groupS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"tg_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="target_Selected_groupS")])
    return InlineKeyboardMarkup(keyboard)

def remove_groupS_keyboard(groupS, page=0, per_page=5):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_groupS = groupS[Start:end]
    
    for grp in page_groupS:
        title = grp.get('group_title', Str(grp.get('group_id', 'Unknown')))[:25]
        keyboard.append([InlineKeyboardButton(
            f"✕ {title}", 
            callback_data=f"rm_tg_{grp.get('group_id', 0)}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"rmtg_page_{page-1}"))
    if end < len(groupS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"rmtg_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="target_Selected_groupS")])
    return InlineKeyboardMarkup(keyboard)

def Single_account_Selection_keyboard(accountS, page=0, per_page=5):
    keyboard = []
    Start = page * per_page
    end = Start + per_page
    page_accountS = accountS[Start:end]
    
    for acc in page_accountS:
        diSplay_name = acc.get('account_firSt_name') or acc.get('phone', 'Unknown')
        if acc.get('account_uSername'):
            diSplay_name = f"{diSplay_name} (@{acc.get('account_uSername')})"
        keyboard.append([InlineKeyboardButton(
            f"◇ {diSplay_name[:35]}", 
            callback_data=f"Select_Single_{acc.get('_id')}"
        )])
    
    nav_buttonS = []
    if page > 0:
        nav_buttonS.append(InlineKeyboardButton("« PREV", callback_data=f"Single_page_{page-1}"))
    if end < len(accountS):
        nav_buttonS.append(InlineKeyboardButton("NEXT »", callback_data=f"Single_page_{page+1}"))
    
    if nav_buttonS:
        keyboard.append(nav_buttonS)
    
    keyboard.append([InlineKeyboardButton("« BACK", callback_data="SettingS")])
    return InlineKeyboardMarkup(keyboard)


# LogS Channel Keyboard
def logS_channel_keyboard(haS_channel=FalSe, verified=FalSe):
    if haS_channel:
        if verified:
            StatuS = "✅ VERIғIED"
            keyboard = [
                [InlineKeyboardButton(StatuS, callback_data="logS_StatuS")],
                [InlineKeyboardButton("✕ REMOVE CHANNEL", callback_data="remove_logS_channel")],
                [InlineKeyboardButton("« BACK", callback_data="SettingS")]
            ]
        elSe:
            StatuS = "⏳ PENDING"
            keyboard = [
                [InlineKeyboardButton(StatuS, callback_data="logS_StatuS")],
                [InlineKeyboardButton("↻ VERIғY", callback_data="verify_logS_channel")],
                [InlineKeyboardButton("✕ REMOVE CHANNEL", callback_data="remove_logS_channel")],
                [InlineKeyboardButton("« BACK", callback_data="SettingS")]
            ]
    elSe:
        keyboard = [
            [InlineKeyboardButton("＋ SET LOGS CHANNEL", callback_data="Set_logS_channel")],
            [InlineKeyboardButton("« BACK", callback_data="SettingS")]
        ]
    return InlineKeyboardMarkup(keyboard)

# Load GroupS OptionS Keyboard
def load_groupS_optionS_keyboard():
    keyboard = [
        [InlineKeyboardButton("◈ LOAD MY GROUPS", callback_data="load_my_groupS")],
        [InlineKeyboardButton("◉ LOAD DEғAULT GROUPS", callback_data="load_default_groupS")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Force Join Keyboard (for uSer SettingS)
def force_join_keyboard(enabled=FalSe):
    StatuS = "● ON" if enabled elSe "○ OFF"
    toggle_teXt = "○ TURN OFF" if enabled elSe "● TURN ON"

    keyboard = [
        [InlineKeyboardButton(f"STATUS: {StatuS}", callback_data="force_join_StatuS")],
        [InlineKeyboardButton(f"{toggle_teXt}", callback_data="toggle_force_join")],
        [InlineKeyboardButton("« BACK", callback_data="SettingS")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Non-Premium / GueSt Start Keyboard
# ─────────────────────────────────────────
def get_non_premium_keyboard(uSer_id: int, referral_count: int = 0, referralS_required: int = 10, trial_uSed: bool = FalSe):
    progreSS = f"{referral_count}/{referralS_required}"
    keyboard = [
        [InlineKeyboardButton("✅ BUY PREMIUM", callback_data="buy_premium")],
    ]
    if not trial_uSed:
        keyboard.append([InlineKeyboardButton("🎁 ACTIVATE 15 DAYS TRIAL", callback_data="activate_trial")])
    keyboard.append([InlineKeyboardButton(f"🔥 GET 14 DAYS ғREE ({progreSS} INVITES)", callback_data="referral_info")])
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Premium BenefitS Info Keyboard
# ─────────────────────────────────────────
def premium_benefitS_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ BUY PREMIUM", callback_data="buy_premium")],
        [InlineKeyboardButton("🔥 INVITE & EARN", callback_data="referral_info")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Referral Info Keyboard
# ─────────────────────────────────────────
def referral_keyboard(invite_link: Str):
    keyboard = [
        [InlineKeyboardButton("🔗 SHARE MY REғERRAL LINK", url=f"httpS://t.me/Share/url?url={invite_link}&teXt=Join%20uSing%20my%20link%20and%20get%20rewardS!")],
        [InlineKeyboardButton("↻ REғRESH PROGRESS", callback_data="referral_info")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Advanced Auto Reply Keyboard
# ─────────────────────────────────────────
def auto_reply_advanced_keyboard(auto_reply_enabled: bool = FalSe, account_id=None):
    toggle_teXt = "○ TURN OFF" if auto_reply_enabled elSe "● TURN ON"
    acc_SuffiX = f"_{account_id}" if account_id elSe ""
    keyboard = [
        [InlineKeyboardButton(f"{toggle_teXt}", callback_data=f"toggle_auto_reply{acc_SuffiX}")],
        [InlineKeyboardButton("➕ SEQ. REPLY", callback_data=f"add_Seq_reply{acc_SuffiX}"),
         InlineKeyboardButton("🔑 KEYWORD REPLY", callback_data=f"add_kw_reply{acc_SuffiX}")],
        [InlineKeyboardButton("👁 VIEW REPLIES", callback_data=f"view_all_replieS{acc_SuffiX}"),
         InlineKeyboardButton("✕ CLEAR ALL", callback_data=f"clear_replieS{acc_SuffiX}")],
        [InlineKeyboardButton("« BACK", callback_data="SettingS")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Per-Account SettingS Keyboard
# ─────────────────────────────────────────
def account_SettingS_keyboard(account_id, SettingS: dict = None):
    S = SettingS or {}
    gap = S.get("gap_SecondS", 5)
    delay = S.get("round_delay", 30)
    interval = S.get("time_interval", 60)
    Sleep_StatuS = "●" if S.get("auto_Sleep") elSe "○"
    forward_StatuS = "●" if S.get("uSe_forward_mode") elSe "○"

    keyboard = [
        [InlineKeyboardButton(f"⏱ INTERVAL: {interval}S", callback_data=f"accSet_interval_{account_id}")],
        [InlineKeyboardButton(f"⏸ GAP: {gap}S", callback_data=f"accSet_gap_{account_id}"),
         InlineKeyboardButton(f"🔄 ROUND DELAY: {delay}S", callback_data=f"accSet_rdelay_{account_id}")],
        [InlineKeyboardButton(f"😴 AUTO SLEEP ⟨{Sleep_StatuS}⟩", callback_data=f"accSet_Sleep_{account_id}"),
         InlineKeyboardButton(f"✉ ғWD MODE ⟨{forward_StatuS}⟩", callback_data=f"accSet_fwd_{account_id}")],
        [InlineKeyboardButton("⟐ AUTO REPLY", callback_data=f"acc_auto_reply_{account_id}")],
        [InlineKeyboardButton("« BACK", callback_data="my_accountS")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Owner Management Keyboard (acceSSible via /Start for ownerS)
# ─────────────────────────────────────────
def owner_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("▤ STATS", callback_data="owner_StatS"),
         InlineKeyboardButton("📢 BROADCAST", callback_data="owner_broadcaSt")],
        [InlineKeyboardButton("💎 ADD PREMIUM", callback_data="owner_addprem"),
         InlineKeyboardButton("🚫 BAN USER", callback_data="owner_ban")],
        [InlineKeyboardButton("⊗ FORCE SUB", callback_data="force_Sub_menu"),
         InlineKeyboardButton("◉ LOGS CHANNEL", callback_data="logS_channel_menu")],
        [InlineKeyboardButton("« BACK", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
