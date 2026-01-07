CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS qr_links (
  code        TEXT PRIMARY KEY,
  owner_uid   TEXT NOT NULL,
  dest_url    TEXT NOT NULL,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS money_qr_links (
  code        TEXT PRIMARY KEY,
  owner_uid   TEXT NOT NULL,
  dest_url    TEXT NOT NULL,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS money_sessions (
  sid         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        TEXT NOT NULL REFERENCES money_qr_links(code) ON DELETE CASCADE,
  expires_at  TIMESTAMPTZ NOT NULL,
  used        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_money_sessions_code ON money_sessions(code);
CREATE INDEX IF NOT EXISTS idx_money_sessions_expires ON money_sessions(expires_at);

CREATE TABLE IF NOT EXISTS earnings (
  id          BIGSERIAL PRIMARY KEY,
  owner_uid   TEXT NOT NULL,
  code        TEXT NOT NULL,
  amount_usd  NUMERIC(12,6) NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_earnings_owner ON earnings(owner_uid);
CREATE INDEX IF NOT EXISTS idx_earnings_code ON earnings(code);
