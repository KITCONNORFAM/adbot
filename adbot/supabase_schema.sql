-- ============================================================
-- AdBot Supabase Schema
-- 📌 Paste this ENTIRE file in Supabase → SQL Editor → Run
-- ============================================================

-- USERS / ROLES -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id        BIGINT PRIMARY KEY,
    first_name     TEXT,
    username       TEXT,
    role           TEXT NOT NULL DEFAULT 'user',   -- 'owner' | 'premium' | 'trial' | 'user'
    trial_used     BOOLEAN NOT NULL DEFAULT FALSE,
    trial_expiry   TIMESTAMPTZ,
    premium_expiry TIMESTAMPTZ,
    banned         BOOLEAN NOT NULL DEFAULT FALSE,
    referred_by    BIGINT,
    referral_count INT NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TELEGRAM ACCOUNTS ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS telegram_accounts (
    id                 BIGSERIAL PRIMARY KEY,
    user_id            BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    phone              TEXT,
    api_id             TEXT,
    api_hash           TEXT,
    session_string     TEXT,
    is_logged_in       BOOLEAN NOT NULL DEFAULT FALSE,
    phone_code_hash    TEXT,
    account_first_name TEXT,
    account_last_name  TEXT,
    account_username   TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used          TIMESTAMPTZ
);

-- ACCOUNT SETTINGS (per-account, not per-user) ------------------------------
CREATE TABLE IF NOT EXISTS account_settings (
    account_id       BIGINT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    ad_text          TEXT,
    saved_message_id BIGINT,
    time_interval    INT NOT NULL DEFAULT 60,
    gap_seconds      INT NOT NULL DEFAULT 5,
    round_delay      INT NOT NULL DEFAULT 30,
    auto_sleep       BOOLEAN NOT NULL DEFAULT FALSE,
    use_forward_mode BOOLEAN NOT NULL DEFAULT FALSE,
    target_mode      TEXT NOT NULL DEFAULT 'all',
    selected_groups  TEXT NOT NULL DEFAULT '[]'
);

-- ACCOUNT STATS (per-account) -----------------------------------------------
CREATE TABLE IF NOT EXISTS account_stats (
    account_id        BIGINT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    messages_sent     INT NOT NULL DEFAULT 0,
    messages_failed   INT NOT NULL DEFAULT 0,
    dms_received      INT NOT NULL DEFAULT 0,
    replies_triggered INT NOT NULL DEFAULT 0,
    groups_joined     INT NOT NULL DEFAULT 0,
    active_status     BOOLEAN NOT NULL DEFAULT TRUE,
    last_broadcast    TIMESTAMPTZ
);

-- AUTO REPLIES (per-account, supports sequential + keyword + media) ----------
CREATE TABLE IF NOT EXISTS auto_replies (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    type            TEXT NOT NULL DEFAULT 'sequential',  -- 'sequential' | 'keyword'
    trigger_keyword TEXT,       -- NULL for sequential replies
    message_text    TEXT,
    media_file_id   TEXT,       -- Telegram file_id for media (image/video)
    reply_order     INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AUTO REPLY STATE (tracks sequential index per DM sender) ------------------
CREATE TABLE IF NOT EXISTS auto_reply_state (
    id           BIGSERIAL PRIMARY KEY,
    account_id   BIGINT NOT NULL,
    from_user_id BIGINT NOT NULL,
    next_index   INT NOT NULL DEFAULT 0,
    replied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
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
    id          BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
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

-- Indexes -------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_role        ON users(role);
CREATE INDEX IF NOT EXISTS idx_accounts_user     ON telegram_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_auto_replies_acct ON auto_replies(account_id);
CREATE INDEX IF NOT EXISTS idx_target_grp_acct   ON target_groups(account_id);
CREATE INDEX IF NOT EXISTS idx_referral_referrer  ON referral_log(referrer_id);
