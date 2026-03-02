import os

file_path = "PyToday/handlers.py"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    # 1. show_selected_groups_menu target_groups
    (
        "    target_groups = db.get_target_groups(user_id)",
        """    accounts = db.get_accounts(user_id, logged_in_only=True)
    target_groups = db.get_target_groups(accounts[0]["id"]) if accounts else []"""
    ),
    # 2. remove_target_group
    (
        "    removed = db.remove_target_group(user_id, group_id)",
        """    accounts = db.get_accounts(user_id, logged_in_only=True)
    if not accounts: return
    removed = db.remove_target_group(accounts[0]["id"], group_id)"""
    ),
    # 3. clear_target_groups
    (
        "    count = db.clear_target_groups(user_id)",
        """    accounts = db.get_accounts(user_id, logged_in_only=True)
    count = db.clear_target_groups(accounts[0]["id"]) if accounts else 0"""
    ),
    # 4. prompt_add_target_group (no change needed here, just UI)
    # 5. awaiting_target_group_id
    (
        "            added = db.add_target_group(user_id, group_id, f\"Group {group_id}\")",
        """            accounts = db.get_accounts(user_id, logged_in_only=True)
            if not accounts: return
            added = db.add_target_group(accounts[0]["id"], group_id, f"Group {group_id}")"""
    ),
    # 6. missing columns: use_multiple_accounts
    (
        "    db.update_user(user_id, use_multiple_accounts=False)",
        "    pass  # Removed from schema"
    ),
    (
        "    db.update_user(user_id, use_multiple_accounts=True, selected_accounts=selected)",
        "    pass  # Removed from schema"
    ),
    (
        "    db.update_user(user_id, use_multiple_accounts=False, selected_single_account=account_id)",
        "    pass  # Removed from schema"
    ),
    # 7. missing columns: ad_text
    (
        "        db.update_user(user_id, ad_text=text)",
        """        accounts = db.get_accounts(user_id, logged_in_only=True)
        if accounts:
            db.update_account_settings(accounts[0]["id"], ad_text=text)"""
    ),
    # 8. missing columns: auto_reply_text
    (
        "        db.update_user(user_id, auto_reply_text='')",
        """        accounts = db.get_accounts(user_id, logged_in_only=True)
        if accounts:
            db.update_account_settings(accounts[0]["id"], auto_reply_text='')"""
    ),
    (
        "        db.update_user(user_id, auto_reply_text=text)",
        """        accounts = db.get_accounts(user_id, logged_in_only=True)
        if accounts:
            db.update_account_settings(accounts[0]["id"], auto_reply_text=text)"""
    )
]

for old, new in replacements:
    text = text.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("DB Logic replacements completed.")
