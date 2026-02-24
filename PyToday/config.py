import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Supabase Configuration (replaces MongoDB + SQLite)
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ============================================================
# Bot Configuration
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "cat_adbot")

# ============================================================
# Owner Bootstrap
# ============================================================
# Used ONLY for the very first boot to seed the owner into DB.
# After that, all owners are managed via /addowner command.
INITIAL_OWNER_IDS = [
    int(x.strip())
    for x in os.getenv("INITIAL_OWNER_IDS", "").split(",")
    if x.strip()
]

# ============================================================
# Encryption Key
# ============================================================
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "abcdefghijklmnopqrstuvwxyz123456")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = secrets.token_urlsafe(32)

# ============================================================
# Media & Branding
# ============================================================
START_IMAGE_URL = os.getenv(
    "START_IMAGE_URL",
    "https://graph.org/file/833d4a93d3cfd8a517222-fb67ce59064ae920dd.jpg"
)
ACCOUNT_NAME_SUFFIX = f"| @{BOT_USERNAME}"
ACCOUNT_BIO_TEMPLATE = f"This message repeated by @{BOT_USERNAME}"

# ============================================================
# Trial & Referral Config
# ============================================================
TRIAL_DAYS = 15
REFERRAL_REWARD_DAYS = 14
REFERRALS_REQUIRED = 10

# ============================================================
# Connection Settings
# ============================================================
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# ============================================================
# Group Links File
# ============================================================
_script_dir = os.path.dirname(os.path.abspath(__file__))
_default_group_file = os.path.join(_script_dir, '..', 'group_mps.txt')
GROUP_LINKS_FILE = os.getenv("GROUP_LINKS_FILE", _default_group_file)

# ============================================================
# Sessions Directory
# ============================================================
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)
