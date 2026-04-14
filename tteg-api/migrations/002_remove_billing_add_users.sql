-- Remove dead Stripe billing table
DROP TABLE IF EXISTS api_keys;

-- Track authenticated user requests
CREATE TABLE IF NOT EXISTS user_requests (
    id         UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    TEXT    NOT NULL,
    query      TEXT    NOT NULL,
    date       DATE    NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_requests_user_id ON user_requests (user_id);
CREATE INDEX IF NOT EXISTS idx_user_requests_date ON user_requests (date);
