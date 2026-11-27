# SmartCampus AI — Agent instructions

## Project context

SmartCampus AI is an agentic university orientation and admissions platform for IIT and ISB. It supports visitors, candidates and admissions staff, with conversational assistance in French, Tunisian dialect and Arabizi. Official academic decisions remain with authorized humans.

The repository uses FastAPI, Python, uv, Psycopg 3, PostgreSQL (Neon), Alembic, PyJWT, and a React/Vite frontend. Inspect the current manifests and code before assuming dependencies or architecture. Follow existing conventions rather than introducing a parallel stack.

## Sources of truth

For each SA task, read the relevant documents and inspect the actual implementation before planning. Start with:

- `docs/Source of Truth/Projet SmartCampus AI.pdf`
- `docs/Source of Truth/SMART_CAMPUS_AI_ADAM_SOURCE_OF_TRUTH.md`
- `docs/Source of Truth/Sprint1_Task_Distribution.docx`
- `docs/SA-3 Acteurs & Processus Métier.docx`
- `docs/SA-4 Architecture Technique.docx`
- `docs/SA-5 Les API et les Règles d’Accès.docx`
- `docs/SA-5_OpenAPI.yaml`
- Relevant technical design and API documents under `docs/`, especially SA-12, SA-13, SA-14, SA-17, SA-18 and SA-28.

Verify actual paths and read document contents, not just filenames. Distinguish official requirements, approved project decisions, proposed parameters and engineering recommendations. Flag conflicts between documents and implementation; do not silently resolve incompatible contracts. Preserve original source-of-truth documents unless explicitly asked to edit them. Update affected API contracts and technical documentation when behavior changes.

## Planning and implementation

- For substantial tasks, begin with repository inspection and a concrete plan. In Plan Mode, remain read-only; do not implement until the user approves.
- Identify the SA task scope, dependencies, existing reusable code, affected files, API/schema changes, tests and genuine unresolved decisions. Resolve routine questions by inspecting the workspace rather than asking the user to paste files or repeat known information.
- Keep changes focused on the requested task. Preserve completed features and avoid unrelated refactors. Do not invent requirements or implement future SA tasks prematurely.
- Follow existing FastAPI router/service/schema organization, dependency injection, Psycopg connection pooling and parameterized SQL, Pydantic validation, shared `AppError` responses and request IDs.
- Keep backend and database dependencies separate. Use `uv` and maintain the relevant manifest and lockfile when dependencies change. Database tools are declared in `database/requirements.txt`.
- Report actual results, including failed or skipped tests and unresolved blockers. Never claim a command, migration or test succeeded unless it was actually executed successfully. Do not repeatedly review already accepted work without a concrete reason.

## Git workflow

- Inspect the current Git branch and working tree. Work on the branch selected by the user for the task; do not infer the intended working branch from the repository's default branch.
- Leave `main` untouched unless the user explicitly authorizes work there. Git branches and Neon database branches are independent.
- Preserve existing local changes and untracked files. Never discard, overwrite, stash, reset or clean the user's work without authorization.
- Do not switch branches, merge, rebase, commit or push without explicit approval. Do not force-push.
- Follow the commit convention `SA-XX: concise imperative description` (for example, `SA-28: implement authentication and roles`). Stage only intended changes and never include secrets.

## Database and migrations

- Current shared database target: the default Neon branch, through `DATABASE_URL` only. Do not use `TEST_DATABASE_URL` or connect to `smartcampus-test` unless the user explicitly changes this policy.
- Treat the default Neon database as shared, persistent data. Preserve all existing records. Never reset, truncate, reseed, drop or downgrade it without explicit authorization and an appropriate recovery plan. The demo seed script is destructive; do not run it against the shared database.
- Inspect the migration chain and verify the configured target safely before applying migrations. Account for environment-variable precedence; never display connection strings or credentials.
- Do not edit already-applied migrations or their historical SQL files. Add a new migration following the existing SQL-first Alembic convention, using the actual current head as its down revision.
- Prefer additive, backward-compatible schema changes. Explain any required backfill, constraints, locking risks or data-loss implications.
- Creating a migration does not authorize applying it. Obtain explicit approval for database writes/migration execution. Do not use `alembic stamp` to hide schema drift.
- Run Alembic from the repository root using its separate dependency environment. For example, inspect the current revision with:
  ```powershell
  uv run --with-requirements database\requirements.txt alembic -c database\alembic.ini current
  ```
  After explicit approval, use the same command prefix with `upgrade <approved_revision>` (or `upgrade head` if all pending revisions are approved), then verify the resulting revision and schema.
- If the sandbox blocks network access, report the blocker or request narrowly scoped authorized access. Do not bypass restrictions.

## Security and access control

- Never print, log, commit or expose passwords, signing secrets, database URLs, API keys, refresh tokens or other credentials. Keep real `.env` files private and use placeholders in `.env.example`. Do not modify actual `.env` files without approval.
- Enforce authorization on the backend, including role and resource ownership checks. A resource ID or frontend role check is not authorization. Default to denying access when scope cannot be established.
- Preserve anonymous visitor access and the SA-25/SA-26 session and conversation behavior. Keep visitor and account authentication distinct; one token type must not authorize the other.
- Reuse the existing account tables and the active roles `candidate`, `interviewer`, `admin`. The four business actors are Visiteur (anonymous), Candidat, Responsable entretiens et rendez-vous, and Administrateur. The two professional actors are independent. Administrators may read candidate profiles; interviewers require an `interview_scheduled` application. Neither role may read private candidate conversations. The professor decision of 2026-11-27 supersedes the former academic/Direction roles and institution-based staff authorization. Obsolete accounts are migrated to inactive interviewers for explicit admin review, never automatically promoted.
- Use maintained cryptographic libraries and secure password hashing; never store plaintext passwords. Public registration must not allow self-assignment of privileged roles. Treat exact account provisioning and recovery workflows as product decisions when not yet approved.
- Follow SA-5 account authentication requirements: short-lived Bearer JWTs (15 minutes) and rotating refresh tokens in Secure, HttpOnly, SameSite cookies; do not store account refresh tokens in localStorage. Store only refresh-token hashes server-side. Account-token configuration should be separate from visitor-token configuration. Document any approved contract deviation.
- Guest-to-account linking (SA-29) requires authenticated candidate identity, explicit consent and verified visitor-session ownership. Do not silently link conversations on login.

## Testing and verification

- Prefer isolated unit/API tests using the existing fake database pattern. Ensure tests do not accidentally load real database credentials from `.env` or inherited environment variables.
- Do not run write-capable integration tests against the shared Neon database. Use offline migration SQL generation or an isolated disposable local PostgreSQL database when appropriate. Ask before accessing any other database target.
- Test success and failure paths, input validation, missing/invalid/expired credentials, role and ownership boundaries, and regressions in affected existing features.
- Use the existing pytest setup and uv environment. Run targeted tests during implementation and the relevant broader suite before completion. Report skipped database-backed tests accurately.
- Run `git diff --check` and summarize meaningful changes. For API work, keep generated OpenAPI behavior and the documented contract consistent. Provide concise manual Swagger checks when useful.

## Task completion

Summarize what was implemented, files changed, tests run and results, migration status, contract changes, and any genuine outstanding decisions. Keep the response practical and provide the next actionable commands when requested. Do not commit, push or apply migrations automatically.
