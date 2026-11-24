-- SA-29: preserve guest history while transferring ownership to a candidate.
BEGIN;
ALTER TABLE visitor_session DROP CONSTRAINT visitor_session_status_check;
ALTER TABLE visitor_session ADD CONSTRAINT visitor_session_status_check
    CHECK (status IN ('active', 'expired', 'linked'));
ALTER TABLE visitor_session
    ADD COLUMN linked_user_id BIGINT REFERENCES app_user(id) ON DELETE RESTRICT,
    ADD COLUMN link_consent_at TIMESTAMPTZ,
    ADD COLUMN linked_at TIMESTAMPTZ,
    ADD CONSTRAINT visitor_session_link_complete CHECK (
        (linked_user_id IS NULL AND link_consent_at IS NULL AND linked_at IS NULL AND status <> 'linked')
        OR (linked_user_id IS NOT NULL AND link_consent_at IS NOT NULL AND linked_at IS NOT NULL AND status = 'linked')
    );
ALTER TABLE conversation ADD COLUMN user_id BIGINT REFERENCES app_user(id) ON DELETE RESTRICT;
CREATE INDEX conversation_candidate_created_idx ON conversation (user_id, created_at DESC, id DESC)
    WHERE user_id IS NOT NULL;
COMMIT;
