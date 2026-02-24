"""
database.py – Full Supabase-backed persistence layer.
Replaces all previous MongoDB (motor) and SQLite (aiosqlite) code.
All operations are synchronous Supabase REST calls wrapped in async contexts.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict

from supabase import create_client, Client
from PyToday import config

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Supabase client (singleton)
# ──────────────────────────────────────────────────────────────────────────────
_supabase: Optional[Client] = None


def get_client() -> Client:
    global _supabase
    if _supabase is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE INIT – Create tables via raw Supabase SQL (run once)
# ══════════════════════════════════════════════════════════════════════════════

SUPABASE_SCHEMA_SQL = """
-- USERS / ROLES -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       BIGINT PRIMARY KEY,
    first_name    TEXT,
    username      TEXT,
    role          TEXT NOT NULL DEFAULT 'user',   -- 'owner', 'premium', 'user', 'trial'
    trial_used    BOOLEAN NOT NULL DEFAULT FALSE,
    trial_expiry  TIMESTAMPTZ,
    premium_expiry TIMESTAMPTZ,
    banned        BOOLEAN NOT NULL DEFAULT FALSE,
    referred_by   BIGINT,
    referral_count INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TELEGRAM ACCOUNTS ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS telegram_accounts (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    phone           TEXT,
    api_id          TEXT,
    api_hash        TEXT,
    session_string  TEXT,
    is_logged_in    BOOLEAN NOT NULL DEFAULT FALSE,
    phone_code_hash TEXT,
    account_first_name TEXT,
    account_last_name  TEXT,
    account_username   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used       TIMESTAMPTZ
);

-- ACCOUNT SETTINGS (per-account, not per-user) ------------------------------
CREATE TABLE IF NOT EXISTS account_settings (
    account_id      BIGINT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    ad_text         TEXT,
    saved_message_id BIGINT,
    time_interval   INT NOT NULL DEFAULT 60,
    gap_seconds     INT NOT NULL DEFAULT 5,
    round_delay     INT NOT NULL DEFAULT 30,
    auto_sleep      BOOLEAN NOT NULL DEFAULT FALSE,
    use_forward_mode BOOLEAN NOT NULL DEFAULT FALSE,
    target_mode     TEXT NOT NULL DEFAULT 'all',
    selected_groups TEXT NOT NULL DEFAULT '[]'
);

-- ACCOUNT STATS (per-account) -----------------------------------------------
CREATE TABLE IF NOT EXISTS account_stats (
    account_id         BIGINT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    messages_sent      INT NOT NULL DEFAULT 0,
    messages_failed    INT NOT NULL DEFAULT 0,
    dms_received       INT NOT NULL DEFAULT 0,
    replies_triggered  INT NOT NULL DEFAULT 0,
    groups_joined      INT NOT NULL DEFAULT 0,
    active_status      BOOLEAN NOT NULL DEFAULT TRUE,
    last_broadcast     TIMESTAMPTZ
);

-- AUTO REPLIES (per-account, supports sequential + keyword + media) ----------
CREATE TABLE IF NOT EXISTS auto_replies (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    type            TEXT NOT NULL DEFAULT 'sequential',  -- 'sequential' | 'keyword'
    trigger_keyword TEXT,       -- NULL for sequential replies
    message_text    TEXT,
    media_file_id   TEXT,       -- Telegram file_id for media (image/video)
    reply_order     INT NOT NULL DEFAULT 0,  -- for sequential ordering
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AUTO REPLY STATE (tracks which sequential index was last sent per DM) ------
CREATE TABLE IF NOT EXISTS auto_reply_state (
    id          BIGSERIAL PRIMARY KEY,
    account_id  BIGINT NOT NULL,
    from_user_id BIGINT NOT NULL,
    next_index  INT NOT NULL DEFAULT 0,
    replied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, from_user_id)
);

-- TARGET GROUPS (per-account) -----------------------------------------------
CREATE TABLE IF NOT EXISTS target_groups (
    id          BIGSERIAL PRIMARY KEY,
    account_id  BIGINT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    group_id    BIGINT NOT NULL,
    group_title TEXT,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, group_id)
);

-- LOGS CHANNELS (per-user) --------------------------------------------------
CREATE TABLE IF NOT EXISTS logs_channels (
    user_id      BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    channel_id   TEXT,
    channel_link TEXT,
    verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- FORCE SUBSCRIBE (global setting) ------------------------------------------
CREATE TABLE IF NOT EXISTS force_sub (
    id         INT PRIMARY KEY DEFAULT 1,
    channel_id TEXT,
    group_id   TEXT,
    enabled    BOOLEAN NOT NULL DEFAULT FALSE
);

-- REFERRAL LOG ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS referral_log (
    id           BIGSERIAL PRIMARY KEY,
    referrer_id  BIGINT NOT NULL,
    referred_id  BIGINT NOT NULL UNIQUE,  -- each user referred only once
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MESSAGE LOGS ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS message_logs (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    account_id    BIGINT NOT NULL,
    chat_id       BIGINT,
    chat_title    TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed force_sub singleton ---------------------------------------------------
INSERT INTO force_sub (id, enabled) VALUES (1, FALSE) ON CONFLICT DO NOTHING;
"""


async def init_db():
    """Initialize the database. Call once at bot startup."""
    db = get_client()
    try:
        # Simple connectivity check – query users table (must exist via supabase_schema.sql)
        db.table("users").select("user_id").limit(1).execute()
        logger.info("\u2705 Supabase connected (schema already present)")
    except Exception as e:
        logger.error(
            f"Supabase connectivity check failed: {e}\n"
            "Make sure you have run supabase_schema.sql in your Supabase SQL Editor!"
        )
        raise

    # Seed initial owners from env into DB (idempotent)
    for owner_id in config.INITIAL_OWNER_IDS:
        _upsert_owner_bootstrap(db, owner_id)


def _upsert_owner_bootstrap(db: Client, user_id: int):
    try:
        existing = db.table("users").select("user_id, role").eq("user_id", user_id).single().execute()
        if existing.data and existing.data.get("role") != "owner":
            db.table("users").update({"role": "owner"}).eq("user_id", user_id).execute()
        elif not existing.data:
            db.table("users").insert({
                "user_id": user_id,
                "role": "owner",
                "created_at": _now_iso()
            }).execute()
        logger.info(f"Owner seeded: {user_id}")
    except Exception as e:
        logger.warning(f"Owner bootstrap error for {user_id}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# USER OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_user(user_id: int) -> Optional[Dict]:
    db = get_client()
    try:
        result = db.table("users").select("*").eq("user_id", user_id).single().execute()
        return result.data
    except Exception:
        return None


def create_or_update_user(user_id: int, first_name: str = None, username: str = None) -> Dict:
    db = get_client()
    existing = get_user(user_id)
    if not existing:
        data = {
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "role": "user",
            "created_at": _now_iso()
        }
        db.table("users").insert(data).execute()
    else:
        db.table("users").update({
            "first_name": first_name,
            "username": username
        }).eq("user_id", user_id).execute()
    return get_user(user_id)


def get_user_role(user_id: int) -> str:
    """Returns role string: 'owner', 'premium', 'trial', 'user', or 'banned'."""
    user = get_user(user_id)
    if not user:
        return "user"
    if user.get("banned"):
        return "banned"
    role = user.get("role", "user")
    # Check expiry for premium / trial
    if role in ("premium", "trial"):
        expiry_field = "premium_expiry" if role == "premium" else "trial_expiry"
        expiry_str = user.get(expiry_field)
        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expiry:
                # Auto-demote on read
                _expire_user(user_id)
                return "user"
    return role


def _expire_user(user_id: int):
    db = get_client()
    db.table("users").update({
        "role": "user",
        "premium_expiry": None,
        "trial_expiry": None
    }).eq("user_id", user_id).execute()


def is_owner(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user.get("role") == "owner")


def is_premium_or_above(user_id: int) -> bool:
    role = get_user_role(user_id)
    return role in ("owner", "premium")


def is_trial(user_id: int) -> bool:
    return get_user_role(user_id) == "trial"


def is_banned(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user.get("banned"))


def get_all_users() -> List[Dict]:
    db = get_client()
    result = db.table("users").select("*").execute()
    return result.data or []


def get_all_bot_user_ids() -> List[int]:
    users = get_all_users()
    return [u["user_id"] for u in users]


def get_users_count() -> int:
    return len(get_all_users())


# ══════════════════════════════════════════════════════════════════════════════
# OWNER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def add_owner(user_id: int) -> Dict:
    db = get_client()
    create_or_update_user(user_id)
    db.table("users").update({"role": "owner"}).eq("user_id", user_id).execute()
    return get_user(user_id)


def remove_owner(user_id: int) -> bool:
    db = get_client()
    if is_owner(user_id):
        db.table("users").update({"role": "user"}).eq("user_id", user_id).execute()
        return True
    return False


def get_all_owners() -> List[Dict]:
    db = get_client()
    result = db.table("users").select("*").eq("role", "owner").execute()
    return result.data or []


# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def add_premium(user_id: int, days: int) -> Dict:
    db = get_client()
    create_or_update_user(user_id)
    user = get_user(user_id)

    # Extend if already premium, otherwise set from now
    current_expiry_str = user.get("premium_expiry") if user else None
    if current_expiry_str:
        base = datetime.fromisoformat(current_expiry_str)
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        base = max(base, datetime.now(timezone.utc))  # extend from future expiry
    else:
        base = datetime.now(timezone.utc)

    new_expiry = base + timedelta(days=days)
    db.table("users").update({
        "role": "premium",
        "premium_expiry": new_expiry.isoformat(),
        "trial_expiry": None  # clear trial if any
    }).eq("user_id", user_id).execute()
    return get_user(user_id)


def remove_premium(user_id: int) -> bool:
    db = get_client()
    user = get_user(user_id)
    if user and user.get("role") == "premium":
        db.table("users").update({"role": "user", "premium_expiry": None}).eq("user_id", user_id).execute()
        return True
    return False


def get_premium_expiry(user_id: int) -> Optional[datetime]:
    user = get_user(user_id)
    if not user:
        return None
    val = user.get("premium_expiry") or user.get("trial_expiry")
    if val:
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return None


# ══════════════════════════════════════════════════════════════════════════════
# TRIAL SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def has_used_trial(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user.get("trial_used"))


def activate_trial(user_id: int) -> Dict:
    db = get_client()
    create_or_update_user(user_id)
    expiry = datetime.now(timezone.utc) + timedelta(days=config.TRIAL_DAYS)
    db.table("users").update({
        "role": "trial",
        "trial_used": True,
        "trial_expiry": expiry.isoformat(),
        "premium_expiry": None
    }).eq("user_id", user_id).execute()
    return get_user(user_id)


# ══════════════════════════════════════════════════════════════════════════════
# BAN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def ban_user(user_id: int) -> bool:
    db = get_client()
    create_or_update_user(user_id)
    db.table("users").update({"banned": True}).eq("user_id", user_id).execute()
    return True


def unban_user(user_id: int) -> bool:
    db = get_client()
    db.table("users").update({"banned": False}).eq("user_id", user_id).execute()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# REFERRAL SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def record_referral(referrer_id: int, referred_id: int) -> bool:
    """Returns True if referral was successfully recorded (not a duplicate)."""
    db = get_client()
    # Block self-referral
    if referrer_id == referred_id:
        return False
    # Block if already referred by someone
    user = get_user(referred_id)
    if user and user.get("referred_by"):
        return False
    try:
        db.table("referral_log").insert({
            "referrer_id": referrer_id,
            "referred_id": referred_id,
            "created_at": _now_iso()
        }).execute()
        # Increment referrer's count and mark referral on referred user
        db.table("users").update({
            "referred_by": referrer_id
        }).eq("user_id", referred_id).execute()

        db.rpc("increment_referral_count", {"uid": referrer_id}).execute()
        _check_referral_reward(referrer_id)
        return True
    except Exception as e:
        logger.warning(f"Referral already recorded or error: {e}")
        return False


def _check_referral_reward(referrer_id: int):
    user = get_user(referrer_id)
    if not user:
        return
    count = user.get("referral_count", 0)
    if count > 0 and count % config.REFERRALS_REQUIRED == 0:
        add_premium(referrer_id, config.REFERRAL_REWARD_DAYS)
        logger.info(f"🎁 Referral reward granted to {referrer_id} – +{config.REFERRAL_REWARD_DAYS} days")


def get_referral_count(user_id: int) -> int:
    user = get_user(user_id)
    return user.get("referral_count", 0) if user else 0


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM ACCOUNT OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_accounts(user_id: int, logged_in_only: bool = False) -> List[Dict]:
    db = get_client()
    query = db.table("telegram_accounts").select("*").eq("user_id", user_id)
    if logged_in_only:
        query = query.eq("is_logged_in", True)
    result = query.execute()
    return result.data or []


def get_account(account_id) -> Optional[Dict]:
    db = get_client()
    try:
        result = db.table("telegram_accounts").select("*").eq("id", int(account_id)).single().execute()
        return result.data
    except Exception:
        return None


def create_account(user_id: int, phone: str, api_id: str, api_hash: str) -> Dict:
    db = get_client()
    result = db.table("telegram_accounts").insert({
        "user_id": user_id,
        "phone": phone,
        "api_id": api_id,
        "api_hash": api_hash,
        "created_at": _now_iso()
    }).execute()
    acct = result.data[0]
    # Init settings and stats rows
    db.table("account_settings").insert({"account_id": acct["id"]}).execute()
    db.table("account_stats").insert({"account_id": acct["id"]}).execute()
    return acct


def update_account(account_id, **kwargs) -> bool:
    db = get_client()
    db.table("telegram_accounts").update(kwargs).eq("id", int(account_id)).execute()
    return True


def delete_account(account_id, user_id: int = None) -> bool:
    db = get_client()
    account_id = int(account_id)
    query = db.table("telegram_accounts").delete().eq("id", account_id)
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.execute()
    return bool(result.data)


def count_accounts(user_id: int, logged_in_only: bool = True) -> int:
    return len(get_accounts(user_id, logged_in_only=logged_in_only))


# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNT SETTINGS (per-account)
# ══════════════════════════════════════════════════════════════════════════════

def get_account_settings(account_id) -> Dict:
    db = get_client()
    try:
        result = db.table("account_settings").select("*").eq("account_id", int(account_id)).single().execute()
        return result.data or {}
    except Exception:
        return {}


def update_account_settings(account_id, **kwargs) -> bool:
    db = get_client()
    existing = get_account_settings(account_id)
    if existing:
        db.table("account_settings").update(kwargs).eq("account_id", int(account_id)).execute()
    else:
        db.table("account_settings").insert({"account_id": int(account_id), **kwargs}).execute()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNT STATS
# ══════════════════════════════════════════════════════════════════════════════

def get_account_stats(account_id) -> Dict:
    db = get_client()
    try:
        result = db.table("account_stats").select("*").eq("account_id", int(account_id)).single().execute()
        return result.data or {}
    except Exception:
        return {}


def increment_stat(account_id, field: str, amount: int = 1):
    db = get_client()
    stats = get_account_stats(account_id)
    if stats:
        new_val = (stats.get(field) or 0) + amount
        db.table("account_stats").update({field: new_val}).eq("account_id", int(account_id)).execute()
    else:
        db.table("account_stats").insert({"account_id": int(account_id), field: amount}).execute()


# ══════════════════════════════════════════════════════════════════════════════
# AUTO REPLY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def get_sequential_replies(account_id) -> List[Dict]:
    db = get_client()
    result = (db.table("auto_replies")
              .select("*")
              .eq("account_id", int(account_id))
              .eq("type", "sequential")
              .order("reply_order")
              .execute())
    return result.data or []


def get_keyword_replies(account_id) -> List[Dict]:
    db = get_client()
    result = (db.table("auto_replies")
              .select("*")
              .eq("account_id", int(account_id))
              .eq("type", "keyword")
              .execute())
    return result.data or []


def add_reply(account_id, reply_type: str, message_text: str = None,
              trigger_keyword: str = None, media_file_id: str = None, order: int = 0) -> Dict:
    db = get_client()
    result = db.table("auto_replies").insert({
        "account_id": int(account_id),
        "type": reply_type,
        "trigger_keyword": trigger_keyword,
        "message_text": message_text,
        "media_file_id": media_file_id,
        "reply_order": order,
        "created_at": _now_iso()
    }).execute()
    return result.data[0] if result.data else {}


def delete_reply(reply_id: int) -> bool:
    db = get_client()
    db.table("auto_replies").delete().eq("id", reply_id).execute()
    return True


def clear_replies(account_id, reply_type: str = None) -> bool:
    db = get_client()
    query = db.table("auto_replies").delete().eq("account_id", int(account_id))
    if reply_type:
        query = query.eq("type", reply_type)
    query.execute()
    return True


def get_next_sequential_reply(account_id, from_user_id: int) -> Optional[Dict]:
    """Gets the next sequential reply in rotation, cycling through all replies."""
    db = get_client()
    replies = get_sequential_replies(account_id)
    if not replies:
        return None

    result = (db.table("auto_reply_state")
              .select("*")
              .eq("account_id", int(account_id))
              .eq("from_user_id", from_user_id)
              .execute())
    state = result.data[0] if result.data else None
    next_idx = state["next_index"] if state else 0
    if next_idx >= len(replies):
        next_idx = 0

    reply = replies[next_idx]
    new_idx = (next_idx + 1) % len(replies)

    if state:
        db.table("auto_reply_state").update({
            "next_index": new_idx,
            "replied_at": _now_iso()
        }).eq("account_id", int(account_id)).eq("from_user_id", from_user_id).execute()
    else:
        db.table("auto_reply_state").insert({
            "account_id": int(account_id),
            "from_user_id": from_user_id,
            "next_index": new_idx,
            "replied_at": _now_iso()
        }).execute()
    return reply


def find_keyword_reply(account_id, text: str) -> Optional[Dict]:
    """Returns first matched keyword reply (case-insensitive)."""
    replies = get_keyword_replies(account_id)
    text_lower = text.lower()
    for reply in replies:
        kw = reply.get("trigger_keyword") or ""
        if kw.lower() in text_lower:
            return reply
    return None


# ══════════════════════════════════════════════════════════════════════════════
# TARGET GROUPS (per-account)
# ══════════════════════════════════════════════════════════════════════════════

def get_target_groups(account_id) -> List[Dict]:
    db = get_client()
    result = db.table("target_groups").select("*").eq("account_id", int(account_id)).execute()
    return result.data or []


def add_target_group(account_id, group_id: int, group_title: str = None) -> bool:
    db = get_client()
    try:
        db.table("target_groups").insert({
            "account_id": int(account_id),
            "group_id": group_id,
            "group_title": group_title,
            "added_at": _now_iso()
        }).execute()
        return True
    except Exception:
        return False  # UNIQUE constraint – already exists


def remove_target_group(account_id, group_id: int) -> bool:
    db = get_client()
    db.table("target_groups").delete().eq("account_id", int(account_id)).eq("group_id", group_id).execute()
    return True


def clear_target_groups(account_id) -> int:
    db = get_client()
    before = len(get_target_groups(account_id))
    db.table("target_groups").delete().eq("account_id", int(account_id)).execute()
    return before


# ══════════════════════════════════════════════════════════════════════════════
# LOGS CHANNELS
# ══════════════════════════════════════════════════════════════════════════════

def get_logs_channel(user_id: int) -> Optional[Dict]:
    db = get_client()
    try:
        result = db.table("logs_channels").select("*").eq("user_id", user_id).single().execute()
        return result.data
    except Exception:
        return None


def set_logs_channel(user_id: int, channel_id: str, channel_link: str = None) -> Dict:
    db = get_client()
    db.table("logs_channels").upsert({
        "user_id": user_id,
        "channel_id": channel_id,
        "channel_link": channel_link,
        "verified": False,
        "created_at": _now_iso()
    }).execute()
    return get_logs_channel(user_id)


def verify_logs_channel(user_id: int) -> Dict:
    db = get_client()
    db.table("logs_channels").update({"verified": True}).eq("user_id", user_id).execute()
    return get_logs_channel(user_id)


def delete_logs_channel(user_id: int):
    db = get_client()
    db.table("logs_channels").delete().eq("user_id", user_id).execute()


# ══════════════════════════════════════════════════════════════════════════════
# FORCE SUBSCRIBE (global)
# ══════════════════════════════════════════════════════════════════════════════

def get_force_sub_settings() -> Dict:
    db = get_client()
    result = db.table("force_sub").select("*").eq("id", 1).single().execute()
    return result.data or {"enabled": False, "channel_id": None, "group_id": None}


def update_force_sub_settings(**kwargs) -> bool:
    db = get_client()
    db.table("force_sub").update(kwargs).eq("id", 1).execute()
    return True


def toggle_force_sub() -> bool:
    settings = get_force_sub_settings()
    new_val = not settings.get("enabled", False)
    update_force_sub_settings(enabled=new_val)
    return new_val


# ══════════════════════════════════════════════════════════════════════════════
# MESSAGE LOGS
# ══════════════════════════════════════════════════════════════════════════════

def create_message_log(user_id: int, account_id, chat_id: int,
                       chat_title: str = None, status: str = "pending",
                       error_message: str = None):
    db = get_client()
    db.table("message_logs").insert({
        "user_id": user_id,
        "account_id": int(account_id),
        "chat_id": chat_id,
        "chat_title": chat_title,
        "status": status,
        "error_message": error_message,
        "created_at": _now_iso()
    }).execute()


# ══════════════════════════════════════════════════════════════════════════════
# STATS OVERVIEW (for /stats command)
# ══════════════════════════════════════════════════════════════════════════════

def get_global_stats() -> Dict:
    users = get_all_users()
    roles = {"owner": 0, "premium": 0, "trial": 0, "user": 0, "banned": 0}
    for u in users:
        if u.get("banned"):
            roles["banned"] += 1
        else:
            roles[u.get("role", "user")] = roles.get(u.get("role", "user"), 0) + 1
    return {
        "total_users": len(users),
        "owners": roles["owner"],
        "premium": roles["premium"],
        "trial": roles["trial"],
        "regular": roles["user"],
        "banned": roles["banned"]
    }


# ══════════════════════════════════════════════════════════════════════════════
# EXPIRY SCHEDULER HELPER (called by APScheduler cron job)
# ══════════════════════════════════════════════════════════════════════════════

def sweep_expired_roles():
    """Demote expired premium/trial users. Run as a scheduled cron job."""
    db = get_client()
    now_iso = _now_iso()

    # Premium expired
    expired_premium = (db.table("users")
                       .select("user_id")
                       .eq("role", "premium")
                       .lt("premium_expiry", now_iso)
                       .execute())
    for u in (expired_premium.data or []):
        db.table("users").update({"role": "user", "premium_expiry": None}).eq("user_id", u["user_id"]).execute()
        logger.info(f"Premium expired for user {u['user_id']}")

    # Trial expired
    expired_trial = (db.table("users")
                     .select("user_id")
                     .eq("role", "trial")
                     .lt("trial_expiry", now_iso)
                     .execute())
    for u in (expired_trial.data or []):
        db.table("users").update({"role": "user", "trial_expiry": None}).eq("user_id", u["user_id"]).execute()
        logger.info(f"Trial expired for user {u['user_id']}")
