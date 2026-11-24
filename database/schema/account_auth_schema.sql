-- SA-28: account authentication. Additive; existing users and passwords are untouched.
BEGIN;

CREATE TABLE account_session (
    id                 UUID PRIMARY KEY,
    user_id            BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    refresh_token_hash CHAR(64) NOT NULL UNIQUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at         TIMESTAMPTZ NOT NULL,
    revoked_at         TIMESTAMPTZ,
    CHECK (created_at < expires_at)
);
CREATE INDEX account_session_user_active_idx ON account_session (user_id, expires_at)
    WHERE revoked_at IS NULL;

CREATE TABLE account_invitation (
    id         UUID PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    created_by BIGINT REFERENCES app_user(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at    TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    CHECK (created_at < expires_at)
);
CREATE INDEX account_invitation_user_idx ON account_invitation (user_id, expires_at);

CREATE TABLE account_role_audit (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id      BIGINT NOT NULL REFERENCES app_user(id),
    target_user_id     BIGINT NOT NULL REFERENCES app_user(id),
    old_role           user_role NOT NULL,
    new_role           user_role NOT NULL,
    old_institution_id BIGINT,
    new_institution_id BIGINT,
    old_is_active      BOOLEAN NOT NULL,
    new_is_active      BOOLEAN NOT NULL,
    changed_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX account_role_audit_target_idx ON account_role_audit (target_user_id, changed_at);

CREATE TABLE account_auth_attempt (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scope         TEXT NOT NULL CHECK (scope IN ('login', 'register')),
    identity_hmac CHAR(64) NOT NULL,
    ip_hmac       CHAR(64) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX account_auth_attempt_identity_idx
    ON account_auth_attempt (scope, identity_hmac, created_at);
CREATE INDEX account_auth_attempt_ip_idx
    ON account_auth_attempt (scope, ip_hmac, created_at);
CREATE INDEX account_auth_attempt_created_idx ON account_auth_attempt (created_at);

COMMIT;
