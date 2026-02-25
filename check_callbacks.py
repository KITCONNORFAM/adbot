import re

# Read all relevant files
try:
    with open('PyToday/keyboards.py', 'r', encoding='utf-8') as f:
        keyboards_code = f.read()
    with open('PyToday/handlers.py', 'r', encoding='utf-8') as f:
        handlers_code = f.read()
    with open('PyToday/new_handlers.py', 'r', encoding='utf-8') as f:
        new_handlers_code = f.read()
except Exception as e:
    print(f"Error reading files: {e}")
    exit(1)

# Extract typical simple callback_data strings
callbacks_in_kb = re.findall(r'callback_data=["\']([^"\'{]+)["\']', keyboards_code)
# Extract f-string callback_data base (e.g., callback_data=f"del_acc_{account['id']}")
# We'll just look for the literal string prefix we passed.
# Let's extract all words that look like callback_data triggers.
prefixes = re.findall(r'callback_data=f["\']([a-zA-Z0-9_]+)_', keyboards_code)

unique_cbs = set(callbacks_in_kb + [p + '_' for p in prefixes])
print(f'Found {len(unique_cbs)} unique callback triggers in keyboards.py')

# Extract handle_callback routing in handlers.py
handled_in_main = re.findall(r'data == ["\']([^"\']+)["\']', handlers_code)
handled_startswith = re.findall(r'data\.startswith\((["\'].*?["\'])\)', handlers_code)
# clean the startswith strings
handled_start_clean = [s.strip('"\'') for s in handled_startswith]

# Extract routing in new_handlers.py
handled_in_new = re.findall(r'CallbackQueryHandler\([^,]+, pattern=["\']([^"\']+)["\']', new_handlers_code)
handled_in_new_clean = [p.replace('^', '') for p in handled_in_new]

all_handled_exact = set(handled_in_main + handled_in_new_clean)
all_handled_prefix = set(handled_start_clean)

missing = []
for cb in unique_cbs:
    if cb in all_handled_exact:
        continue
    
    handled = False
    for prefix in all_handled_prefix:
        if cb.startswith(prefix):
            handled = True
            break
            
    # Some new_handlers use regex starts with
    for new_cb in handled_in_new_clean:
         if cb.startswith(new_cb):
             handled = True
             break
             
    if not handled:
        missing.append(cb)

if missing:
    print('UNHANDLED CALLBACKS FOUND:')
    for m in sorted(missing):
        print(f' - {m}')
else:
    print('✅ All literal callbacks in keyboards.py are handled!')
