# Catalog and admission API (SA-20, SA-21, SA-22)

Status: 2026-11-21. Owner: Member A. Code: `backend/` on branch `backend`, built on Member B's SA-7 app.
Interactive docs: run the server and open `/docs`. All routes are read-only `GET` under `/api/v1`.

## Run it

From `backend/`, with `backend/.env` holding `DATABASE_URL` (Neon connection string, never committed):

```
python -m uvicorn app.main:app --reload     # server on http://127.0.0.1:8000
python -m pytest -q                          # 22 tests (skipped without DATABASE_URL)
python scripts/smoke_test.py                 # 16 live checks against the running server
```

## Endpoints

| Route | Use | Main parameters |
| --- | --- | --- |
| `/institutions` | IIT and ISB with their program counts | none |
| `/programs` | Search the catalog | `institution` (IIT, ISB), `level` (prepa, licence, ingenieur, mastere, mba, architecture), `field`, `language` (fr, en), `q` (free text, 2+ chars), `limit` (1-100, default 50), `offset` |
| `/programs/{code}` | One program: details, specializations, `leads_to` and `reachable_from` pathways | `code` such as `IIT-ING-GI` (case does not matter) |
| `/programs/{code}/admission` | Entry level, selection steps, accepted backgrounds grouped by kind, current campaign | |
| `/programs/{code}/eligibility` | Is a background accepted? Returns `eligible`: true, false, or null when no list is published | `kind` (bac_section, prepa_track, licence_specialty, diploma), `value`; accents and case are ignored |
| `/programs/{code}/tariffs` | Fees per student category, institution fee rules, and a `message` to quote | `academic_year` like `2026-2027` |
| `/campaigns` | Admission campaigns | `institution`, `status` (planned, open, closed) |

## Rules for callers (agent and frontend)

- **Money comes as strings** (`"667.00"`) so amounts stay exact. Convert for display only.
- **`is_confirmed: false`** means the fee was copied from the website and the admissions office has not confirmed it. The agent should say so. For "/9 mois" fees, `year_total_estimate` = amount × installments and is an estimate.
- **`published: false`** or **`eligible: null`** means the information is not published: answer "ask the admissions office", never invent a value.
- **Errors** use Member B's shape: `{"error": {"code", "message", "details", "request_id"}}`. Codes added here: `PROGRAM_NOT_FOUND` (404), `ADMISSION_NOT_FOUND` (404), `DATABASE_NOT_CONFIGURED` (503).

## For Member C (agent tools)

The agent's catalog tools map one-to-one onto these routes: search programs, program detail, admission rules, eligibility check, fees. Use `source_url` from the responses to cite the official page.

## Verification (SA-22)

| Check | Result |
| --- | --- |
| Unit and API tests (`pytest`), test database | 22 passed (Member A's PC, Neon `smartcampus_test`) |
| Live smoke checks (`smoke_test.py`), running server | 16/16 passed on PostgreSQL 16 copy; Neon result to record |
| Reconnect after the database drops an idle connection | Fixed in SA-21 (`check_connection`, `max_idle=120`) and verified |
