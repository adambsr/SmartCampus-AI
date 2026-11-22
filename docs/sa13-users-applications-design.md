# SA-13: Users and applications tables

Status: draft for team review, 2026-11-21. Owner: Member A.
SQL: `database/schema/users_applications_schema.sql` (apply after `catalog_schema.sql`).

## Tables (5)

| Table | Purpose | Key columns |
| --- | --- | --- |
| app_user | One account per actor | email (unique, case-insensitive), password_hash, full_name, phone, role, institution_id, is_active, last_login_at |
| candidate_profile | Profile built by the conversation agent | user_id (PK), current_level, bac_section, bac_year, bac_average, last_diploma, last_diploma_specialty, favorite_subjects[], interests[], career_goal, constraints, preferred_language |
| application | The pre-registration to one program in one campaign | user_id, program_id, campaign_id, status, consent_at, source, submitted_at |
| application_history | Every status change | application_id, from_status, to_status, changed_by, note, changed_at |
| recommendation | A program suggested to a candidate | user_id, program_id, score (0-100), rank, justification, source (agent, staff), status, reviewed_by, reviewed_at |

## Decisions

1. **Roles match the spec's actors:** candidate, academic_staff, interviewer, direction, admin. IIT and ISB academic staff share one role; `institution_id` says which school they supervise, and a check makes it mandatory for academic_staff.
2. **Email is unique ignoring case**, so `Ali@x.tn` and `ali@x.tn` can't create two accounts.
3. **Consent is enforced:** an application can't leave `draft` without `consent_at`, as the spec requires recording consent before pre-registration.
4. **History is automatic:** a trigger writes a row in `application_history` on creation and on every status change. The backend can record who made the change with `SET LOCAL app.user_id = '<id>'` in the same transaction.
5. **Profile fields cover both entry routes:** bac data for licences and prépa, `last_diploma` + specialty for engineering and mastères, matching `accepted_background` in SA-12.
6. **One application per user, program and campaign.**

## For Member B (auth, SA-28 / SA-29)

- Auth builds on `app_user` (`password_hash`, `role`, `is_active`, `last_login_at`).
- Guest sessions and conversation messages are B's and C's tables (SA-25, SA-26). To link a guest conversation to an account (SA-29), add a nullable `user_id` FK to `app_user` on the guest session table.

## Tested

On PostgreSQL 16: tables create cleanly after SA-12, the trigger logs draft → submitted with the user id, and the duplicate email, staff without institution, and submit without consent cases are all rejected.
