from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("ᴀᴅᴠᴇʀᴛɪsɪɴɢ", callback_data="advertising_menu"),
         InlineKeyboardButton("ᴀᴄᴄᴏᴜɴᴛs", callback_data="accounts_menu")],
        [InlineKeyboardButton("ʟᴏᴀᴅ ɢᴄs/ᴍᴘs", callback_data="load_groups"),
         InlineKeyboardButton("sᴇᴛ ᴀᴅ ᴛᴇxᴛ", callback_data="set_ad_text")],
        [InlineKeyboardButton("sᴇᴛᴛɪɴɢs", callback_data="settings"),
         InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def advertising_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("» sᴛᴀʀᴛ ᴀᴅᴠᴇʀᴛɪsɪɴɢ «", callback_data="start_advertising")],
        [InlineKeyboardButton("▣ sᴛᴏᴘ ᴀᴅᴠᴇʀᴛɪsɪɴɢ", callback_data="stop_advertising")],
        [InlineKeyboardButton("◴ sᴇᴛ ᴛɪᴍᴇ", callback_data="set_time")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def accounts_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("＋ ᴀᴅᴅ ᴀᴄᴄᴏᴜɴᴛ", callback_data="add_account")],
        [InlineKeyboardButton("✕ ᴅᴇʟᴇᴛᴇ ᴀᴄᴄᴏᴜɴᴛ", callback_data="delete_account")],
        [InlineKeyboardButton("≡ ᴍʏ ᴀᴄᴄᴏᴜɴᴛs", callback_data="my_accounts")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def support_keyboard():
    keyboard = [
        [InlineKeyboardButton("◈ ᴀᴅᴍɪɴ", url="https://t.me/charliespringfam")],
        [InlineKeyboardButton("◉ ʜᴏᴡ ᴛᴏ ᴜsᴇ", url="https://t.me/charliespringfam")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_keyboard(use_multiple=False, use_forward=False, auto_reply=False, auto_group_join=False, force_sub=False, is_admin_user=False):
    forward_status = "●" if use_forward else "○"
    forward_mode = "ғᴏʀᴡᴀʀᴅ" if use_forward else "sᴇɴᴅ"
    auto_reply_status = "●" if auto_reply else "○"
    auto_join_status = "●" if auto_group_join else "○"
    force_sub_status = "●" if force_sub else "○"
    
    keyboard = [
        [InlineKeyboardButton("◇ sɪɴɢʟᴇ ᴀᴄᴄᴏᴜɴᴛ", callback_data="single_mode"),
         InlineKeyboardButton("◆ ᴍᴜʟᴛɪᴘʟᴇ", callback_data="multiple_mode")],
        [InlineKeyboardButton("▤ sᴛᴀᴛɪsᴛɪᴄs", callback_data="statistics")],
        [InlineKeyboardButton(f"✉ {forward_mode} ⟨{forward_status}⟩", callback_data="toggle_forward_mode"),
         InlineKeyboardButton(f"⟐ ᴀᴜᴛᴏ ʀᴇᴘʟʏ ⟨{auto_reply_status}⟩", callback_data="auto_reply_menu")],
        [InlineKeyboardButton(f"⊕ ᴀᴜᴛᴏ ᴊᴏɪɴ ⟨{auto_join_status}⟩", callback_data="toggle_auto_group_join")],
        [InlineKeyboardButton("◉ ʟᴏɢs ᴄʜᴀɴɴᴇʟ", callback_data="logs_channel_menu")]
    ]
    
    if is_admin_user:
        keyboard.append([InlineKeyboardButton(f"⊗ ғᴏʀᴄᴇ sᴜʙ ⟨{force_sub_status}⟩", callback_data="force_sub_menu")])
    
    keyboard.append([InlineKeyboardButton("◎ ᴛᴀʀɢᴇᴛɪɴɢ", callback_data="target_adv")])
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def force_sub_keyboard(force_sub_enabled=False):
    status = "● ᴏɴ" if force_sub_enabled else "○ ᴏғғ"
    toggle_text = "○ ᴛᴜʀɴ ᴏғғ" if force_sub_enabled else "● ᴛᴜʀɴ ᴏɴ"
    
    keyboard = [
        [InlineKeyboardButton(f"{toggle_text}", callback_data="toggle_force_sub")],
        [InlineKeyboardButton("◈ sᴇᴛ ᴄʜᴀɴɴᴇʟ ɪᴅ", callback_data="set_force_channel"),
         InlineKeyboardButton("◉ sᴇᴛ ɢʀᴏᴜᴘ ɪᴅ", callback_data="set_force_group")],
        [InlineKeyboardButton("◐ ᴠɪᴇᴡ sᴇᴛᴛɪɴɢs", callback_data="view_force_sub")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def force_sub_join_keyboard(channel_id=None, group_id=None):
    keyboard = []
    if channel_id:
        keyboard.append([InlineKeyboardButton("◈ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/c/{str(channel_id).replace('-100', '')}")])
    if group_id:
        keyboard.append([InlineKeyboardButton("◉ ᴊᴏɪɴ ɢʀᴏᴜᴘ", url=f"https://t.me/c/{str(group_id).replace('-100', '')}")])
    keyboard.append([InlineKeyboardButton("↻ ᴄʜᴇᴄᴋ ᴀɢᴀɪɴ", callback_data="check_force_sub")])
    return InlineKeyboardMarkup(keyboard)

def auto_reply_settings_keyboard(auto_reply_enabled=False):
    toggle_text = "○ ᴛᴜʀɴ ᴏғғ" if auto_reply_enabled else "● ᴛᴜʀɴ ᴏɴ"
    
    keyboard = [
        [InlineKeyboardButton(f"{toggle_text}", callback_data="toggle_auto_reply")],
        [InlineKeyboardButton("≡ sᴇᴛ ᴅᴇғᴀᴜʟᴛ ᴛᴇxᴛ", callback_data="set_default_reply"),
         InlineKeyboardButton("＋ ᴀᴅᴅ ᴛᴇxᴛ", callback_data="add_reply_text")],
        [InlineKeyboardButton("✕ ᴅᴇʟᴇᴛᴇ ᴛᴇxᴛ", callback_data="delete_reply_text"),
         InlineKeyboardButton("◐ ᴠɪᴇᴡ ᴛᴇxᴛ", callback_data="view_reply_text")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def target_adv_keyboard(target_mode="all"):
    all_check = "●" if target_mode == "all" else "○"
    selected_check = "●" if target_mode == "selected" else "○"
    
    keyboard = [
        [InlineKeyboardButton(f"{all_check} ᴀʟʟ ɢʀᴏᴜᴘs", callback_data="target_all_groups"),
         InlineKeyboardButton(f"{selected_check} sᴇʟᴇᴄᴛᴇᴅ", callback_data="target_selected_groups")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def selected_groups_keyboard():
    keyboard = [
        [InlineKeyboardButton("＋ ᴀᴅᴅ ɢʀᴏᴜᴘ", callback_data="add_target_group"),
         InlineKeyboardButton("－ ʀᴇᴍᴏᴠᴇ", callback_data="remove_target_group")],
        [InlineKeyboardButton("✕ ᴄʟᴇᴀʀ ᴀʟʟ", callback_data="clear_target_groups"),
         InlineKeyboardButton("≡ ᴠɪᴇᴡ ɢʀᴏᴜᴘs", callback_data="view_target_groups")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="target_adv")]
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
        [InlineKeyboardButton("⌫ ᴅᴇʟᴇᴛᴇ", callback_data="otp_delete"),
         InlineKeyboardButton("⓪", callback_data="otp_0"),
         InlineKeyboardButton("✓ sᴜʙᴍɪᴛ", callback_data="otp_submit")],
        [InlineKeyboardButton("✕ ᴄᴀɴᴄᴇʟ", callback_data="otp_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def twofa_keyboard():
    keyboard = [
        [InlineKeyboardButton("✕ ᴄᴀɴᴄᴇʟ", callback_data="twofa_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def accounts_keyboard(accounts, page=0, per_page=5):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_accounts = accounts[start:end]
    
    for acc in page_accounts:
        status = "●" if acc.get('is_logged_in') else "○"
        display_name = acc.get('account_first_name') or acc.get('phone', 'Unknown')
        if acc.get('account_username'):
            display_name = f"{display_name} (@{acc.get('account_username')})"
        keyboard.append([InlineKeyboardButton(
            f"{status} {display_name[:35]}", 
            callback_data=f"select_acc_{acc.get('_id')}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"acc_page_{page-1}"))
    if end < len(accounts):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"acc_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="accounts_menu")])
    return InlineKeyboardMarkup(keyboard)

def groups_keyboard(groups, account_id, page=0, per_page=10):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_groups = groups[start:end]
    
    for grp in page_groups:
        title = grp.get('title', 'Unknown')[:30]
        grp_type = "◈" if grp.get('is_marketplace') else "◉"
        keyboard.append([InlineKeyboardButton(
            f"{grp_type} {title}", 
            callback_data=f"group_info_{grp.get('id', 0)}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"grp_page_{account_id}_{page-1}"))
    if end < len(groups):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"grp_page_{account_id}_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("↻ ʀᴇғʀᴇsʜ", callback_data=f"load_grp_{account_id}")])
    keyboard.append([InlineKeyboardButton("⌂ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def delete_accounts_keyboard(accounts, page=0, per_page=5):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_accounts = accounts[start:end]
    
    for acc in page_accounts:
        display_name = acc.get('account_first_name') or acc.get('phone', 'Unknown')
        if acc.get('account_username'):
            display_name = f"{display_name} (@{acc.get('account_username')})"
        keyboard.append([InlineKeyboardButton(
            f"✕ {display_name[:35]}", 
            callback_data=f"del_acc_{acc.get('_id')}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"del_page_{page-1}"))
    if end < len(accounts):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"del_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="accounts_menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_delete_keyboard(account_id):
    keyboard = [
        [InlineKeyboardButton("✓ ʏᴇs, ᴅᴇʟᴇᴛᴇ", callback_data=f"confirm_del_{account_id}"),
         InlineKeyboardButton("✕ ᴄᴀɴᴄᴇʟ", callback_data="delete_account")]
    ]
    return InlineKeyboardMarkup(keyboard)

def time_keyboard():
    keyboard = [
        [InlineKeyboardButton("◴ 30 sᴇᴄ", callback_data="time_30"),
         InlineKeyboardButton("◴ 1 ᴍɪɴ", callback_data="time_60"),
         InlineKeyboardButton("◴ 2 ᴍɪɴ", callback_data="time_120")],
        [InlineKeyboardButton("◴ 5 ᴍɪɴ", callback_data="time_300"),
         InlineKeyboardButton("◴ 10 ᴍɪɴ", callback_data="time_600"),
         InlineKeyboardButton("◴ 15 ᴍɪɴ", callback_data="time_900")],
        [InlineKeyboardButton("◴ 30 ᴍɪɴ", callback_data="time_1800"),
         InlineKeyboardButton("◴ 1 ʜᴏᴜʀ", callback_data="time_3600"),
         InlineKeyboardButton("◈ ᴄᴜsᴛᴏᴍ", callback_data="time_custom")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="advertising_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton("⌂ ᴍᴀɪɴ ᴍᴇɴᴜ", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def back_to_settings_keyboard():
    keyboard = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]]
    return InlineKeyboardMarkup(keyboard)

def back_to_auto_reply_keyboard():
    keyboard = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="auto_reply_menu")]]
    return InlineKeyboardMarkup(keyboard)

def ad_text_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("≡ sᴀᴠᴇᴅ ᴛᴇxᴛ", callback_data="ad_saved_text")],
        [InlineKeyboardButton("＋ ᴀᴅᴅ ᴛᴇxᴛ", callback_data="ad_add_text"),
         InlineKeyboardButton("✕ ᴅᴇʟᴇᴛᴇ ᴛᴇxᴛ", callback_data="ad_delete_text")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def ad_text_back_keyboard():
    keyboard = [[InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="set_ad_text")]]
    return InlineKeyboardMarkup(keyboard)

def account_selection_keyboard(accounts, selected_ids=None, page=0, per_page=5):
    if selected_ids is None:
        selected_ids = []
    
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_accounts = accounts[start:end]
    
    for acc in page_accounts:
        if acc.get('is_logged_in'):
            is_selected = str(acc.get('_id')) in [str(s) for s in selected_ids]
            check = "●" if is_selected else "○"
            display_name = acc.get('account_first_name') or acc.get('phone', 'Unknown')
            if acc.get('account_username'):
                display_name = f"{display_name} (@{acc.get('account_username')})"
            keyboard.append([InlineKeyboardButton(
                f"{check} {display_name[:35]}", 
                callback_data=f"toggle_acc_{acc.get('_id')}"
            )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"sel_page_{page-1}"))
    if end < len(accounts):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"sel_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("✓ ᴄᴏɴғɪʀᴍ sᴇʟᴇᴄᴛɪᴏɴ", callback_data="confirm_selection")])
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")])
    return InlineKeyboardMarkup(keyboard)

def target_groups_list_keyboard(groups, page=0, per_page=5):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_groups = groups[start:end]
    
    for grp in page_groups:
        title = grp.get('group_title', str(grp.get('group_id', 'Unknown')))[:30]
        keyboard.append([InlineKeyboardButton(
            f"◉ {title}", 
            callback_data=f"tg_info_{grp.get('group_id', 0)}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"tg_page_{page-1}"))
    if end < len(groups):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"tg_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="target_selected_groups")])
    return InlineKeyboardMarkup(keyboard)

def remove_groups_keyboard(groups, page=0, per_page=5):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_groups = groups[start:end]
    
    for grp in page_groups:
        title = grp.get('group_title', str(grp.get('group_id', 'Unknown')))[:25]
        keyboard.append([InlineKeyboardButton(
            f"✕ {title}", 
            callback_data=f"rm_tg_{grp.get('group_id', 0)}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"rmtg_page_{page-1}"))
    if end < len(groups):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"rmtg_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="target_selected_groups")])
    return InlineKeyboardMarkup(keyboard)

def single_account_selection_keyboard(accounts, page=0, per_page=5):
    keyboard = []
    start = page * per_page
    end = start + per_page
    page_accounts = accounts[start:end]
    
    for acc in page_accounts:
        display_name = acc.get('account_first_name') or acc.get('phone', 'Unknown')
        if acc.get('account_username'):
            display_name = f"{display_name} (@{acc.get('account_username')})"
        keyboard.append([InlineKeyboardButton(
            f"◇ {display_name[:35]}", 
            callback_data=f"select_single_{acc.get('_id')}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("« ᴘʀᴇᴠ", callback_data=f"single_page_{page-1}"))
    if end < len(accounts):
        nav_buttons.append(InlineKeyboardButton("ɴᴇxᴛ »", callback_data=f"single_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")])
    return InlineKeyboardMarkup(keyboard)

# Admin Panel Keyboard
def admin_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("▤ sᴛᴀᴛs", callback_data="admin_stats"),
         InlineKeyboardButton("◈ ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⊗ ғᴏʀᴄᴇ sᴜʙ", callback_data="force_sub_menu"),
         InlineKeyboardButton("◉ ʟᴏɢs ᴄʜᴀɴɴᴇʟ", callback_data="logs_channel_menu")],
        [InlineKeyboardButton("≡ ᴜsᴇʀs", callback_data="admin_users"),
         InlineKeyboardButton("✕ ʙᴀɴ/ᴜɴʙᴀɴ", callback_data="admin_ban")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Logs Channel Keyboard
def logs_channel_keyboard(has_channel=False, verified=False):
    if has_channel:
        if verified:
            status = "✅ ᴠᴇʀɪғɪᴇᴅ"
            keyboard = [
                [InlineKeyboardButton(status, callback_data="logs_status")],
                [InlineKeyboardButton("✕ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ", callback_data="remove_logs_channel")],
                [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
            ]
        else:
            status = "⏳ ᴘᴇɴᴅɪɴɢ"
            keyboard = [
                [InlineKeyboardButton(status, callback_data="logs_status")],
                [InlineKeyboardButton("↻ ᴠᴇʀɪғʏ", callback_data="verify_logs_channel")],
                [InlineKeyboardButton("✕ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ", callback_data="remove_logs_channel")],
                [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
            ]
    else:
        keyboard = [
            [InlineKeyboardButton("＋ sᴇᴛ ʟᴏɢs ᴄʜᴀɴɴᴇʟ", callback_data="set_logs_channel")],
            [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
        ]
    return InlineKeyboardMarkup(keyboard)

# Load Groups Options Keyboard
def load_groups_options_keyboard():
    keyboard = [
        [InlineKeyboardButton("◈ ʟᴏᴀᴅ ᴍʏ ɢʀᴏᴜᴘs", callback_data="load_my_groups")],
        [InlineKeyboardButton("◉ ʟᴏᴀᴅ ᴅᴇғᴀᴜʟᴛ ɢʀᴏᴜᴘs", callback_data="load_default_groups")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Force Join Keyboard (for user settings)
def force_join_keyboard(enabled=False):
    status = "● ᴏɴ" if enabled else "○ ᴏғғ"
    toggle_text = "○ ᴛᴜʀɴ ᴏғғ" if enabled else "● ᴛᴜʀɴ ᴏɴ"

    keyboard = [
        [InlineKeyboardButton(f"sᴛᴀᴛᴜs: {status}", callback_data="force_join_status")],
        [InlineKeyboardButton(f"{toggle_text}", callback_data="toggle_force_join")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Non-Premium / Guest Start Keyboard
# ─────────────────────────────────────────
def get_non_premium_keyboard(user_id: int, referral_count: int = 0, referrals_required: int = 10):
    progress = f"{referral_count}/{referrals_required}"
    keyboard = [
        [InlineKeyboardButton("✅ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_premium")],
        [InlineKeyboardButton("🎁 ᴀᴄᴛɪᴠᴀᴛᴇ 1 ᴍᴏɴᴛʜ ᴛʀɪᴀʟ", callback_data="activate_trial")],
        [InlineKeyboardButton(f"🔥 ɢᴇᴛ 14 ᴅᴀʏs ғʀᴇᴇ ({progress} ɪɴᴠɪᴛᴇs)", callback_data="referral_info")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Premium Benefits Info Keyboard
# ─────────────────────────────────────────
def premium_benefits_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", callback_data="buy_premium")],
        [InlineKeyboardButton("🔥 ɪɴᴠɪᴛᴇ & ᴇᴀʀɴ", callback_data="referral_info")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Referral Info Keyboard
# ─────────────────────────────────────────
def referral_keyboard(invite_link: str):
    keyboard = [
        [InlineKeyboardButton("🔗 sʜᴀʀᴇ ᴍʏ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ", url=f"https://t.me/share/url?url={invite_link}&text=Join%20using%20my%20link%20and%20get%20rewards!")],
        [InlineKeyboardButton("↻ ʀᴇғʀᴇsʜ ᴘʀᴏɢʀᴇss", callback_data="referral_info")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Advanced Auto Reply Keyboard
# ─────────────────────────────────────────
def auto_reply_advanced_keyboard(auto_reply_enabled: bool = False, account_id=None):
    toggle_text = "○ ᴛᴜʀɴ ᴏғғ" if auto_reply_enabled else "● ᴛᴜʀɴ ᴏɴ"
    acc_suffix = f"_{account_id}" if account_id else ""
    keyboard = [
        [InlineKeyboardButton(f"{toggle_text}", callback_data=f"toggle_auto_reply{acc_suffix}")],
        [InlineKeyboardButton("➕ sᴇǫ. ʀᴇᴘʟʏ", callback_data=f"add_seq_reply{acc_suffix}"),
         InlineKeyboardButton("🔑 ᴋᴇʏᴡᴏʀᴅ ʀᴇᴘʟʏ", callback_data=f"add_kw_reply{acc_suffix}")],
        [InlineKeyboardButton("👁 ᴠɪᴇᴡ ʀᴇᴘʟɪᴇs", callback_data=f"view_all_replies{acc_suffix}"),
         InlineKeyboardButton("✕ ᴄʟᴇᴀʀ ᴀʟʟ", callback_data=f"clear_replies{acc_suffix}")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Per-Account Settings Keyboard
# ─────────────────────────────────────────
def account_settings_keyboard(account_id, settings: dict = None):
    s = settings or {}
    gap = s.get("gap_seconds", 5)
    delay = s.get("round_delay", 30)
    interval = s.get("time_interval", 60)
    sleep_status = "●" if s.get("auto_sleep") else "○"
    forward_status = "●" if s.get("use_forward_mode") else "○"

    keyboard = [
        [InlineKeyboardButton(f"⏱ ɪɴᴛᴇʀᴠᴀʟ: {interval}s", callback_data=f"accset_interval_{account_id}")],
        [InlineKeyboardButton(f"⏸ ɢᴀᴘ: {gap}s", callback_data=f"accset_gap_{account_id}"),
         InlineKeyboardButton(f"🔄 ʀᴏᴜɴᴅ ᴅᴇʟᴀʏ: {delay}s", callback_data=f"accset_rdelay_{account_id}")],
        [InlineKeyboardButton(f"😴 ᴀᴜᴛᴏ sʟᴇᴇᴘ ⟨{sleep_status}⟩", callback_data=f"accset_sleep_{account_id}"),
         InlineKeyboardButton(f"✉ ғᴡᴅ ᴍᴏᴅᴇ ⟨{forward_status}⟩", callback_data=f"accset_fwd_{account_id}")],
        [InlineKeyboardButton("⟐ ᴀᴜᴛᴏ ʀᴇᴘʟʏ", callback_data=f"acc_auto_reply_{account_id}")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="my_accounts")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ─────────────────────────────────────────
# Owner Management Keyboard (accessible via /start for owners)
# ─────────────────────────────────────────
def owner_panel_keyboard():
    keyboard = [
        [InlineKeyboardButton("▤ sᴛᴀᴛs", callback_data="owner_stats"),
         InlineKeyboardButton("📢 ʙʀᴏᴀᴅᴄᴀsᴛ", callback_data="owner_broadcast")],
        [InlineKeyboardButton("💎 ᴀᴅᴅ ᴘʀᴇᴍɪᴜᴍ", callback_data="owner_addprem"),
         InlineKeyboardButton("🚫 ʙᴀɴ ᴜsᴇʀ", callback_data="owner_ban")],
        [InlineKeyboardButton("⊗ ғᴏʀᴄᴇ sᴜʙ", callback_data="force_sub_menu"),
         InlineKeyboardButton("◉ ʟᴏɢs ᴄʜᴀɴɴᴇʟ", callback_data="logs_channel_menu")],
        [InlineKeyboardButton("« ʙᴀᴄᴋ", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
