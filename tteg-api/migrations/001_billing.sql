-- tteg billing schema
-- Run once against the Supabase Postgres instance.

-- API keys issued to paid subscribers
CREATE TABLE IF NOT EXISTS api_keys (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    key                         TEXT        UNIQUE NOT NULL,
    email                       TEXT        NOT NULL,
    plan                        TEXT        NOT NULL DEFAULT 'pro',   -- 'pro' | 'team'
    stripe_subscription_id      TEXT,
    stripe_checkout_session_id  TEXT,
    active                      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key    ON api_keys (key);
CREATE INDEX IF NOT EXISTS idx_api_keys_sub_id ON api_keys (stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_session ON api_keys (stripe_checkout_session_id);

-- Daily usage counters for free-tier rate limiting (per IP)
CREATE TABLE IF NOT EXISTS daily_usage (
    id         UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    ip         TEXT    NOT NULL,
    date       DATE    NOT NULL,
    count      INTEGER NOT NULL DEFAULT 0,
    UNIQUE (ip, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_ip_date ON daily_usage (ip, date);

-- Auto-purge usage rows older than 7 days to keep the table small.
-- Run this periodically (e.g. via pg_cron or a weekly Cloud Scheduler job):
--
--   DELETE FROM daily_usage WHERE date < CURRENT_DATE - INTERVAL '7 days';
