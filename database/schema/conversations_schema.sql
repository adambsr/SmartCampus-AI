-- SA-26: text conversations owned by anonymous visitor sessions.
BEGIN;

CREATE TABLE conversation (
    id                  UUID PRIMARY KEY,
    visitor_session_id  UUID NOT NULL REFERENCES visitor_session(id) ON DELETE RESTRICT,
    channel             TEXT NOT NULL CHECK (channel = 'text'),
    language            TEXT CHECK (language IN ('fr', 'tn', 'arabizi')),
    status              TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'closed')),
    created_at          TIMESTAMPTZ NOT NULL
);
CREATE INDEX conversation_visitor_created_idx
    ON conversation (visitor_session_id, created_at, id);

CREATE TABLE conversation_message (
    id              UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    language        TEXT CHECK (language IN ('fr', 'tn', 'arabizi')),
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX conversation_message_history_idx
    ON conversation_message (conversation_id, created_at, id);

COMMIT;
