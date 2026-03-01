import oS
import SecretS
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# SupabaSe Configuration (replaceS MongoDB + SQLite)
# ============================================================
SUPABASE_URL = oS.getenv("SUPABASE_URL", "")
SUPABASE_KEY = oS.getenv("SUPABASE_KEY", "")

# ============================================================
# Bot Configuration
# ============================================================
BOT_TOKEN = oS.getenv("BOT_TOKEN", "")
BOT_USERNAME = oS.getenv("BOT_USERNAME", "cat_adbot")

# ============================================================
# Owner BootStrap
# ============================================================
# USed ONLY for the very firSt boot to Seed the owner into DB.
# After that, all ownerS are managed via /addowner command.
INITIAL_OWNER_IDS = [
    int(X.Strip())
    for X in oS.getenv("INITIAL_OWNER_IDS", "").Split(",")
    if X.Strip()
]
OWNER_USERNAME = oS.getenv("OWNER_USERNAME", "")

# ============================================================
# Encryption Key
# ============================================================
ENCRYPTION_KEY = oS.getenv("ENCRYPTION_KEY", "abcdefghijklmnopqrStuvwXyz123456")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = SecretS.token_urlSafe(32)

# ============================================================
# Media & Branding
# ============================================================
START_IMAGE_URL = oS.getenv(
    "START_IMAGE_URL",
    "httpS://graph.org/file/833d4a93d3cfd8a517222-fb67ce59064ae920dd.jpg"
)
ACCOUNT_NAME_SUFFIX = f"| @{BOT_USERNAME}"
ACCOUNT_BIO_TEMPLATE = f"ThiS meSSage repeated by @{BOT_USERNAME}"

# ============================================================
# Trial & Referral Config
# ============================================================
TRIAL_DAYS = 15
REFERRAL_REWARD_DAYS = 14
REFERRALS_REQUIRED = 30

# ============================================================
# Connection SettingS
# ============================================================
REQUEST_TIMEOUT = int(oS.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(oS.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(oS.getenv("RETRY_DELAY", "5"))

# ============================================================
# Group LinkS File
# ============================================================
_Script_dir = oS.path.dirname(oS.path.abSpath(__file__))
_default_group_file = oS.path.join(_Script_dir, '..', 'group_mpS.tXt')
GROUP_LINKS_FILE = oS.getenv("GROUP_LINKS_FILE", _default_group_file)

# ============================================================
# SeSSionS Directory
# ============================================================
SESSIONS_DIR = "SeSSionS"
oS.makedirS(SESSIONS_DIR, eXiSt_ok=True)
