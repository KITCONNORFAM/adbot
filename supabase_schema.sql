-- ============================================================
-- AdBot Supabase Schema
-- Run this in your Supabase SQL Editor (project > SQL Editor)
-- ============================================================

-- 1. Users (all bot users)
CREATE TABLE IF NOT EXISTS bot_users (
    user_id        BIGINT PRIMARY KEY,
    username       TEXT,
    first_name     TEXT,
    last_name      TEXT,
    role           TEXT NOT NULL DEFAULT 'user',   -- 'owner' | 'premium' | 'trial' | 'user'
    premium_expiry TIMESTAMPTZ,
    trial_used     BOOLEAN NOT NULL DEFAULT FALSE,
    is_banned      BOOLEAN NOT NULL DEFAULT FALSE,
    referred_by    BIGINT,
    total_referrals INT NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Referrals log
CREATE TABLE IF NOT EXISTS referrals (
    id           SERIAL PRIMARY KEY,
    referrer_id  BIGINT NOT NULL REFERENCES bot_users(user_id),
    referred_id  BIGINT NOT NULL REFERENCES bot_users(user_id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (referred_id)   -- each user can only be referred once
);

-- 3. Telegram Accounts (per user, premium = multiple)
CREATE TABLE IF NOT EXISTS telegram_accounts (
    id                  SERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES bot_users(user_id),
    phone               TEXT,
    api_id              TEXT,
    api_hash            TEXT,
    session_string      TEXT,
    is_logged_in        BOOLEAN NOT NULL DEFAULT FALSE,
    phone_code_hash     TEXT,
    account_first_name  TEXT,
    account_last_name   TEXT,
    account_username    TEXT,
    saved_message_id    BIGINT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used           TIMESTAMPTZ
);

-- 4. Per-Account Settings
CREATE TABLE IF NOT EXISTS account_settings (
    account_id          INT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    ad_text             TEXT,
    time_interval       INT NOT NULL DEFAULT 60,
    gap_seconds         INT NOT NULL DEFAULT 5,
    round_delay         INT NOT NULL DEFAULT 30,
    use_forward_mode    BOOLEAN NOT NULL DEFAULT FALSE,
    auto_reply_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    auto_sleep          BOOLEAN NOT NULL DEFAULT FALSE,
    target_mode         TEXT NOT NULL DEFAULT 'all',
    logs_channel_id     TEXT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Per-Account Stats
CREATE TABLE IF NOT EXISTS account_stats (
    account_id          INT PRIMARY KEY REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    messages_sent       INT NOT NULL DEFAULT 0,
    messages_failed     INT NOT NULL DEFAULT 0,
    replies_triggered   INT NOT NULL DEFAULT 0,
    dms_received        INT NOT NULL DEFAULT 0,
    groups_joined       INT NOT NULL DEFAULT 0,
    last_broadcast      TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT FALSE
);

-- 6. Target Groups
CREATE TABLE IF NOT EXISTS target_groups (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES bot_users(user_id),
    group_id    BIGINT NOT NULL,
    group_title TEXT,
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, group_id)
);

-- 7. Sequential Auto-Replies (per account, ordered by position)
CREATE TABLE IF NOT EXISTS sequential_replies (
    id           SERIAL PRIMARY KEY,
    account_id   INT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    position     INT NOT NULL,
    message_text TEXT,
    media_file_id TEXT,   -- Telegram file_id for photos/docs/etc
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (account_id, position)
);

-- 8. Keyword Auto-Replies (per account)
CREATE TABLE IF NOT EXISTS keyword_replies (
    id               SERIAL PRIMARY KEY,
    account_id       INT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    trigger_keyword  TEXT NOT NULL,
    message_text     TEXT,
    media_file_id    TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (account_id, trigger_keyword)
);

-- 9. Sequential reply state per user per account (tracks which reply index each user is on)
CREATE TABLE IF NOT EXISTS seq_reply_state (
    account_id      INT NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    from_user_id    BIGINT NOT NULL,
    next_index      INT NOT NULL DEFAULT 0,
    PRIMARY KEY (account_id, from_user_id)
);

-- 10. Bot-global settings (force_sub, misc)
CREATE TABLE IF NOT EXISTS bot_settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- Seed defaults
INSERT INTO bot_settings (key, value)
VALUES
    ('force_sub_enabled', 'false'),
    ('force_sub_channel_id', ''),
    ('force_sub_group_id', '')
ON CONFLICT (key) DO NOTHING;

-- 11. Auto-reply logs
CREATE TABLE IF NOT EXISTS auto_reply_logs (
    id           SERIAL PRIMARY KEY,
    account_id   INT REFERENCES telegram_accounts(id),
    from_user_id BIGINT,
    from_username TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_bot_users_role        ON bot_users(role);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer    ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_user         ON telegram_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_seq_replies_account   ON sequential_replies(account_id, position);
CREATE INDEX IF NOT EXISTS idx_kw_replies_account    ON keyword_replies(account_id);
CREATE INDEX IF NOT EXISTS idx_target_groups_user    ON target_groups(user_id);
