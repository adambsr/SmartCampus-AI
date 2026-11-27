# SA-28: Account authentication and roles

Status: implemented in source; migration `0006_account_auth` and the private first-admin bootstrap were applied to the default Neon `DATABASE_URL` on 2026-11-24. The 10 existing users were preserved; one active admin now has an Argon2id password hash.

## Boundaries

- Visitor sessions and visitor-owned text conversations keep their SA-25/SA-26 Bearer JWT, refresh JSON body, lifetime, and ownership behavior. Account JWTs use a different signing secret, issuer, audience, kind, and database session.
- The active PostgreSQL/account roles are exclusively `candidate`, `interviewer`, and `admin`. Visitors remain anonymous. The professor decision of 2026-11-27 merges former academic-supervisor and Direction business responsibilities into Administrateur. Administrateur and Responsable entretiens et rendez-vous are independent actors. Default Neon has `0008_simplify_roles`, confirmed by read-only verification on 2026-11-27. Other environments require their own approved migration application before deploying this source version.
- Candidate account registration is public and always creates `candidate` plus `candidate_profile`. Staff creation, invitations, and role/status changes require an admin account. Existing passwordless demo users cannot claim their rows through registration.
- There is no email verification or automated invitation delivery in SA-28. Activation tokens are delivered manually by an admin. Password recovery is not included.

## Authorization matrix

| Identity | SA-28 access |
| --- | --- |
| Visitor | Own SA-25/SA-26 session and text conversation; public catalog. |
| Candidate | Own profile and application status reads. |
| Responsable entretiens et rendez-vous (`interviewer`) | Read-only candidate profile with an `interview_scheduled` application; no unrelated admin operations. |
| Administrateur (`admin`) | Any candidate profile across IIT/ISB; account list, pending interviewer/admin creation, activation invitations, staff-role and active-status changes. |

All checks run in the backend. A caller-supplied candidate ID is not proof of ownership. `is_active`, the current role, and session revocation are checked from PostgreSQL on every protected request. Effective role/institution/status changes revoke the affected user's account sessions and unused invitations; no-op updates preserve them. institution_id remains nullable for compatibility but staff assignment accepts only omitted/null values and grants no access. Candidate accounts cannot be converted to staff accounts; provision a separate staff identity. The last active admin with a password cannot be demoted or deactivated.

## Credentials and session lifetime

- Passwords use Argon2id (`argon2-cffi`) with 19 MiB memory, 2 iterations, and parallelism 1. The Argon2 hash contains its own salt and parameters. Passwords must have 12–128 characters. The login path rehashes a valid password if its stored parameters are outdated.
- Account access JWTs last 15 minutes. The access token is returned in JSON and the frontend keeps it in memory. The random refresh credential has a seven-day absolute lifetime and rotates on every use. Only its SHA-256 hash is stored in `account_session`.
- The account refresh cookie is HttpOnly, SameSite Strict, path `/`, and Secure by default. In development only, `AUTH_COOKIE_SECURE=false` allows loopback HTTP and uses an unprefixed cookie name. Keep `true` for production. Cookie-bearing refresh and logout requests require an allowed Origin.
- Failed logins are limited to five attempts per 15 minutes per email or peer IP. Registrations are limited to five per hour per peer IP. The attempt table contains keyed HMACs, never plaintext addresses or emails. The API uses the connection peer IP, not forwarded headers supplied by clients.
- The same generic 401 is used for unknown email, wrong password, inactive account, and an account with no password. A duplicate registration email receives 409.

## Account API

| Route | Purpose |
| --- | --- |
| `POST /api/v1/auth/register` | Candidate signup, account access token, refresh cookie. |
| `POST /api/v1/auth/login` | Candidate/staff sign-in. |
| `POST /api/v1/auth/refresh` | Rotate the account refresh cookie and return a new access token. |
| `POST /api/v1/auth/logout` | Revoke the account session and clear the cookie. |
| `GET /api/v1/auth/me` | Read current account and effective role. |
| `POST /api/v1/auth/activate` | Consume a one-time first-password invitation. |
| `GET /api/v1/candidates/me` | Read the candidate's own profile. |
| `GET /api/v1/candidates/me/applications` | Read the candidate's application statuses. |
| `GET /api/v1/candidates/{candidate_id}` | Scoped staff dossier read; IDs are `BIGINT`. |
| `GET/POST /api/v1/admin/users` | List accounts or create a pending staff account. |
| `PATCH /api/v1/admin/users/{user_id}` | Change staff role or account active status; audit and revoke sessions and unused invitations. |
| `POST /api/v1/admin/users/{user_id}/invitations` | Issue a 24-hour, single-use activation token shown once. |

Errors use the shared `{ "error": { "code", "message", "details", "request_id" } }` envelope. The SA-5 YAML now distinguishes account and visitor Bearer schemes. SA-5's candidate UUIDs were replaced with the implemented `BIGINT` account IDs. Profile editing, documents, audio and assistant replies remain future scope. SA-29 session-wide conversation transfer and candidate conversation APIs are implemented and remain unchanged.

## Deployment preparation

1. A distinct random `ACCOUNT_JWT_SECRET` is configured in the gitignored local `backend/.env`. Development HTTP uses `AUTH_COOKIE_SECURE=false` there. Other deployments must set their own secret, approved frontend Origin in `CORS_ORIGINS`, HTTPS, and secure cookies.
2. The additive migration `0006_account_auth` has been applied to the default Neon branch through `DATABASE_URL`. It did not alter or delete existing users or records. Other environments need their own migration review.
3. The initial admin password has been set privately. `uv run python -m scripts.bootstrap_admin` now refuses to run again because a usable admin exists. The command never prints the password or connection string.
4. Sign in as admin, issue activation invitations to passwordless demo users or create pending staff users and invite them. Deliver each token manually. The recipient enters it at `/activate`, sets a password, and signs in at `/login`.

Never run the demo seed for this work: it truncates tables. Do not use `TEST_DATABASE_URL` or `smartcampus-test`. Keep real `.env` values out of source control and logs.

## SA-29 hand-off

The SA-29 transfer is implemented in source and documented in `sa29-guest-account-link.md`. Its additive migration `0007_guest_account_link` was applied to default Neon on 2026-11-27, and remains included in the verified 0008 migration chain. The subsequent authorized verification was read-only. Signing in or registering alone still does not link a guest conversation; explicit consent and separate visitor ownership proof are required.

## Professor scope change and legacy accounts

Migration `0008_simplify_roles` was applied by the project owner to default Neon and verified in an authorized read-only transaction on 2026-11-27. Two former academic_staff accounts and one former direction account are inactive interviewers, with three migration audit entries. There were no affected account sessions or unused invitations at migration time; zero remain unrevoked. It preserves account IDs, password hashes and historical references. Every obsolete-role account becomes an inactive interviewer, with its original role/institution/active state preserved in a system audit entry. Sessions and unused invitations are revoked. Existing candidate/interviewer/admin accounts retain their roles and sessions. No account is promoted automatically.

An administrator must review each disabled account before choosing interviewer or admin and reactivating it. For passwordless accounts, issue a new invitation only after reviewing the intended role; activation sets the account active. Already activated accounts keep their password and use the existing status update. There is no new recovery or scheduling workflow.

Audit role fields are historical text restricted to the five historical names. Normal audit entries require actor_user_id; only a system entry marked migration_reason=0008_simplify_roles may omit it. Legacy names in audit history do not authorize accounts.

Appointment invitations are future interview functionality and are distinct from the existing manually delivered account activation invitations. Candidate listings, conversation summaries, QCM, interview results, appointment assignment, recommendation review, formation management, RAG/configuration tools, AI supervision and statistical dashboards are target UML responsibilities, not implemented modules. Staff cannot read private transcripts, hashes, or refresh credentials.

See [SA-17](sa17-migrations.md) for the migration and rollout procedure.
