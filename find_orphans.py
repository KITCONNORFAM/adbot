missing = [
 'accset_gap_', 'accset_interval_', 'accset_rdelay_', 'add_kw_', 'add_seq_', 
 'clear_', 'force_join_status', 'group_info_', 'logs_status', 'owner_broadcast', 
 'rmtg_page_', 'select_acc_', 'tg_info_', 'tg_page_', 'toggle_auto_', 'view_all_'
]

with open('PyToday/keyboards.py', 'r', encoding='utf-8') as f:
    kb_code = f.readlines()

print('=== ORPHANED BUTTONS LOCATIONS ===')
for i, line in enumerate(kb_code, 1):
    for m in missing:
        if f'callback_data="{m}' in line or f"callback_data='{m}" in line or f'callback_data=f"{m}' in line:
            # Print the def function name above it to know which keyboard
            for j in range(i-1, -1, -1):
                if j < len(kb_code) and kb_code[j].startswith('def '):
                    print(f'{m} -> {kb_code[j].strip()} (Line {i})')
                    break
