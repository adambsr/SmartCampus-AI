# SA-13: Users and applications tables

Status: schema documentation updated for the approved professor decision, 2026-11-27. Owner: Member A.
Historical SQL: `database/schema/users_applications_schema.sql`. Install through the complete Alembic chain; current roles additionally require `role_simplification_schema.sql` in revision `0008_simplify_roles`. Do not edit or directly replay historical SQL on an existing database.

## Tables (5)

| Table | Purpose | Key columns |
| --- | --- | --- |
| app_user | Authenticated account; visitors are anonymous | email (unique, case-insensitive), password_hash, full_name, phone, role, institution_id, is_active, last_login_at |
| candidate_profile | Profile built by the conversation agent | user_id (PK), current_level, bac_section, bac_year, bac_average, last_diploma, last_diploma_specialty, favorite_subjects[], interests[], career_goal, constraints, preferred_language |
| application | The pre-registration to one program in one campaign | user_id, program_id, campaign_id, status, consent_at, source, submitted_at |
| application_history | Every status change | application_id, from_status, to_status, changed_by, note, changed_at |
| recommendation | A program suggested to a candidate | user_id, program_id, score (0-100), rank, justification, source (agent, staff), status, reviewed_by, reviewed_at |

## Decisions

1. **Active account roles:** candidate, interviewer, admin. Visiteur is anonymous; Candidat, Responsable entretiens et rendez-vous and Administrateur are the authenticated actors. The two professional actors are independent. The former academic institution constraint is removed by 0008; institution_id remains nullable compatibility metadata and grants no authorization.
2. **Email is unique ignoring case**, so `Ali@x.tn` and `ali@x.tn` can't create two accounts.
3. **Consent is enforced:** an application can't leave `draft` without `consent_at`, as the spec requires recording consent before pre-registration.
4. **History is automatic:** a trigger writes a row in `application_history` on creation and on every status change. The backend can record who made the change with `SET LOCAL app.user_id = '<id>'` in the same transaction.
5. **Profile fields cover both entry routes:** bac data for licences and prépa, `last_diploma` + specialty for engineering and mastères, matching `accepted_background` in SA-12.
6. **One application per user, program and campaign.**

## For Member B (auth, SA-28 / SA-29)

- Auth builds on `app_user` (`password_hash`, `role`, `is_active`, `last_login_at`).
- SA-29 already records the candidate in visitor_session.linked_user_id and conversation.user_id after explicit consent and ownership proof. Preserve these fields and all guest/conversation IDs and messages.

## Historical verification

On PostgreSQL 16: tables create cleanly after SA-12, the trigger logs draft → submitted with the user id, and the duplicate email, staff without institution, and submit without consent cases are all rejected.

## Historical roles and migration

The old five-role enum in applied SA-13/SA-28 SQL is historical input, not the current authorization catalogue. Revision 0008 preserves old audit role strings as checked text, records system migration entries with migration_reason, and moves academic_staff/direction accounts to inactive interviewer pending explicit administrator review. Original institution and active state remain in the audit, with account IDs and all application/recommendation/history references intact. No automatic promotion, account deletion or password reset occurs. See SA-17 and SA-28 for rollout and restoration.

Default Neon application status: 0008_simplify_roles was applied by the project owner and confirmed at repository head by authorized read-only verification on 2026-11-27. Three former-role accounts are inactive interviewers; original identities and historical references remain valid. See SA-17 for the verification counts.
