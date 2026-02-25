import re

with open('PyToday/handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# 1) Replace ALL is_admin( with db.is_owner(
count_admin = content.count('is_admin(')
content = content.replace('is_admin(', 'db.is_owner(')
print(f'Fixed is_admin -> db.is_owner: {count_admin} places')

# 2) Remove all remaining db.execute( raw SQL - replace with None
count_exec = content.count('db.execute(')
content = re.sub(r'db\.execute\([^)]+\)', 'None  # removed old SQL', content)
print(f'Fixed db.execute() raw SQL: {count_exec} places')

# 3) Remove old aiosqlite block references that remain
content = content.replace('database.aiosqlite', 'None  # removed aiosqlite')
content = content.replace('database.sqlite_db_path', "''")

# 4) Replace the entire old SQLite try block in show_admin_stats
# Find the pattern and replace
old_pattern = re.compile(
    r'    # Get total accounts\n'
    r'    total_accounts = 0\n'
    r'    logged_in_accounts = 0\n'
    r'    try:\n'
    r'        async with None.*?logger\.error\(f["\']Error getting account stats.*?\)\n',
    re.DOTALL
)
replacement = '''    # Get total accounts via Supabase
    try:
        total_accounts = db.count_accounts() or 0
        all_accs = db.get_accounts(None) or []
        logged_in_accounts = len([a for a in all_accs if a.get('is_logged_in')])
    except Exception as e:
        logger.error(f'Error getting account stats: {e}')
        total_accounts = 0
        logged_in_accounts = 0
'''
count_replaced = len(old_pattern.findall(content))
content = re.sub(old_pattern, replacement, content)
print(f'Fixed admin stats SQLite block: {count_replaced} replacements')

# 5) Verify no remaining issues
remaining_aiosql = content.count('aiosqlite')
remaining_db_execute = len(re.findall(r'db\.execute\(', content))
remaining_is_admin = content.count('is_admin(')
print(f'Remaining aiosqlite refs: {remaining_aiosql}')
print(f'Remaining db.execute() calls: {remaining_db_execute}')
print(f'Remaining is_admin() calls: {remaining_is_admin}')

with open('PyToday/handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)
print(f'File saved: {original_len} -> {len(content)} bytes')
