-- SA-25: anonymous visitor sessions and minimal creation-rate records.
BEGIN;

CREATE TABLE visitor_session (
    id                  UUID PRIMARY KEY,
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'expired')),
    language            TEXT CHECK (language IN ('fr', 'tn', 'arabizi')),
    created_at          TIMESTAMPTZ NOT NULL,
    last_activity_at    TIMESTAMPTZ NOT NULL,
    idle_expires_at     TIMESTAMPTZ NOT NULL,
    absolute_expires_at TIMESTAMPTZ NOT NULL,
    refresh_token_hash  CHAR(64) NOT NULL UNIQUE,
    CHECK (created_at <= last_activity_at),
    CHECK (idle_expires_at <= absolute_expires_at),
    CHECK (created_at < absolute_expires_at)
);
CREATE INDEX visitor_session_active_expiry_idx
    ON visitor_session (status, idle_expires_at, absolute_expires_at);

-- Records exist only for the rolling creation quota window. IP addresses are
-- never stored; ip_hmac is keyed by VISITOR_SESSION_SECRET in the backend.
CREATE TABLE visitor_session_creation (
    id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ip_hmac  CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX visitor_session_creation_window_idx
    ON visitor_session_creation (ip_hmac, created_at);
CREATE INDEX visitor_session_creation_expiry_idx
    ON visitor_session_creation (created_at);

COMMIT;
