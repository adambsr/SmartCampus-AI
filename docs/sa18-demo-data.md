# SA-18: Demo data

Status: draft for team review, 2026-11-21. Owner: Member A.
Script: `database/seed/seed_demo.py`, reads `database/seed/catalog_inventory.csv`.

## How to run

From the repo root, with `DATABASE_URL` set and migrations through `0008_simplify_roles` applied:

```
python database/seed/seed_demo.py --confirm-reset
```

The script uses `DATABASE_URL` only and requires `--confirm-reset`. It **empties all 26 application tables first** (TRUNCATE ... RESTART IDENTITY CASCADE), including visitor sessions/conversations and account sessions/invitations/role audits/auth throttling. It is only for a disposable fresh demo database. It must never be run against the team's default Neon database or any database with records to preserve. It does not read `TEST_DATABASE_URL` or target `smartcampus-test`.

## What it loads

| Table | Rows | Content |
| --- | --- | --- |
| institution | 2 | IIT and ISB (Sfax) |
| program | 31 | The real programs from iit.tn and isb.tn (15 IIT, 16 ISB) |
| admission_requirement | 31 | Entry level, selection steps, notes, source page |
| accepted_background | 116 | Bac sections, prépa tracks (MP/PC/PT), licence specialties from IIT's criteria PDF (DC-SC-17), MBA diplomas |
| tariff | 20 | Fees shown on the websites, all `is_confirmed = false` |
| fee_rule | 4 | IIT rules: 5 % discount, 5 % yearly increase, no refund, exchange rate on 01/10 |
| pathway | 15 | Prépa → 5 engineering programs, IT licences → Génie Informatique, plus a few demo routes |
| admission_campaign | 2 | 2026-2027, open 2026-03-01 to 2026-10-01 |
| app_user | 7 | 2 passwordless professional accounts (admin, interviewer) + 5 candidates |
| candidate_profile | 5 | Bac Math, Sciences, Eco-Gestion, Technique, and one Licence 3 |
| application | 5 | One at each stage: draft, submitted, qcm_pending, interview_scheduled, enrolled |
| application_history | 16 | Written by the trigger; the candidate creates and submits, staff do every later step |
| recommendation | 5 | 2 proposed, 3 confirmed by the synthetic admin |
| source_document / document_chunk | 5 / 5 | Real IIT/ISB pages, one chunk each, no embedding yet |
| sync_job | 1 | A finished crawler run |

## Things to know

- All people and emails are fake (`@example.com`). Accounts are passwordless. On a fresh disposable database, start the backend from `backend/` and run `uv run python -m scripts.bootstrap_admin` to set the first admin password; that admin can then issue invitations to the other accounts. Never bootstrap against the team's default Neon database as part of seeding.
- Fees marked "/9 mois" on the site are stored as `period = month, installments = 9` until the admissions office confirms what they mean. Programs with no published fee have no tariff row.
- Chunks have no embedding: Member C's pipeline fills `embedding` once the model is chosen.

## Historical verification

On PostgreSQL 16 + pgvector, the catalog and admissions rows were previously checked for stable counts, correct history attribution, and agreement with the CSV. The seeder now also clears the SA-25/SA-26/SA-28 tables when explicitly reset; this destructive behavior has not been run against the current Neon database.

The 2026-11-27 role change updates only future disposable demo fixtures and staff attribution to the synthetic admin. It does not reseed or remap existing records. The updated seeder has not been executed against Neon.
