# SA-29: Transfer visitor conversations to a candidate

Status: implemented in source. Migration `0007_guest_account_link` was applied to default Neon on 2026-11-27, as supplied by the project owner. Subsequent authorized read-only verification on 2026-11-27 confirmed default Neon at 0008_simplify_roles, including intact SA-29 conversation ownership references; no verification writes were performed.

## Requirement and behavior

The SA-29 task requires a visitor who registers or signs in to retain prior conversation history only after identification, explicit consent, and verification that the temporary visitor session belongs to them. The chosen scope is the entire session. SA-5 originally proposed an individual conversation link route; the updated OpenAPI contract uses a session-level route to reflect this approved decision.

`POST /api/v1/visitor-sessions/{session_id}/link` requires a candidate account Bearer JWT, a separate visitor JWT in `X-Visitor-Session-Token`, and `{ "consent": true }`. The server validates the active visitor session and atomically assigns all its existing conversations to the candidate. It records candidate ID and consent/link times, marks the visitor session `linked`, and replaces its refresh hash. Old visitor access and refresh credentials then fail. The session cannot create more guest conversations; anonymous browsing can start a fresh session.

The original visitor session ID stays on each conversation for provenance. Conversation IDs, messages, and history remain intact. The candidate can list, retrieve, and append text messages at `/api/v1/candidates/me/conversations` and its `{conversation_id}` subroutes, including after the visitor session's original expiry. Other candidates and staff cannot read them. AI responses, audio, and profile extraction remain separate work.

## Frontend

The `/chat` page provides minimal text conversation storage using SA-25/SA-26; it does not generate assistant replies. Visitor credentials are kept in tab `sessionStorage` through registration or login. The candidate page then displays an unchecked consent prompt explaining the permanent transfer and loss of visitor access. On success, it clears visitor credentials and displays the linked history for continuation.

## Deployment

Default Neon already has `0007_guest_account_link`. Other environments require their own approved migration application through `DATABASE_URL`. The migration is additive and has no backfill or deletion. Do not run the destructive demo seeder. No actual `.env` changes are required.
