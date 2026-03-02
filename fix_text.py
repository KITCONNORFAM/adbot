import os

replacements = {
    'ʙ ᴏ ᴜ ᴏ ᴜsᴛ': 'YOU MUST',
    'ᴀᴅᴏ ɪɴ': 'ADMIN',
    'ᴛɪᴏ ᴇ': 'TIME',
    'ᴏ ᴇɴᴜ': 'MENU',
    'ᴏ ᴏ ᴅᴇ': 'MODE',
    'sᴇᴛ ᴜᴘ ᴀɴᴅ ᴠᴇʀɪғʏ  ᴀ ʟᴏ ɢs ᴄʜᴀɴɴᴇʟ ʙᴇғᴏ ʀᴇ ᴀᴜᴛᴏ -ᴊᴏ ɪɴɪɴɢ ɢʀᴏ ᴜᴘs': 'SET UP A LOGS CHANNEL BEFORE STARTING ADVERTISING',
    'ʜᴏ ᴡ ᴛᴏ  sᴇᴛ ᴜᴘ': 'HOW TO SET UP',
    'ᴄʀᴇᴀᴛᴇ ᴀ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ': 'CREATE A NEW CHANNEL',
    'ᴀᴅᴅ ᴛʜɪs ʙᴏ ᴛ ᴀs': 'ADD THIS BOT AS',
    'sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴀɴᴅ ᴠᴇʀɪғʏ': 'SEND THE CHANNEL ID OR LINK',
    'SINGLE OODE': 'SINGLE MODE',
    'sɪɴɢʟᴇ ᴍᴏᴅᴇ': 'SINGLE MODE',
    'sɪɴɢʟᴇ ᴏ ᴏ ᴅᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ': 'SINGLE MODE ACTIVATED',
    'ʟᴏ ᴀᴅ ᴍʏ ɢʀᴏᴜᴘs': 'LOAD MY GROUPS',
    'ʟᴏᴀᴅ ᴍʏ ɢʀᴏᴜᴘs': 'LOAD MY GROUPS',
    'ᴍᴀʀᴋᴇᴛᴘʟᴀᴄᴇs': 'MARKETPLACES',
    'ᴀᴅ ᴛᴇxᴛ ᴍᴇɴᴜ': 'AD TEXT MENU',
    'ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ': 'YOUR ACCOUNT',
    'ᴄᴏᴍᴘʟᴇᴛᴇ': 'COMPLETE',
    'ᴀᴅᴠᴇʀᴛɪsɪɴɢ': 'ADVERTISING',
    'ᴀᴅ ᴛᴇxᴛ': 'AD TEXT',
    'ʟᴏ ɢs ᴄʜᴀɴɴᴇʟ': 'LOGS CHANNEL'
}

for file_name in ['PyToday/handlers.py', 'PyToday/keyboards.py', 'PyToday/new_handlers.py']:
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            text = f.read()
            
        for bad_text, good_text in replacements.items():
            text = text.replace(bad_text, good_text)
            
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(text)

print('Exact styling replacements finished successfully!')
