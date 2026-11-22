# SA-18: Demo data

Status: draft for team review, 2026-11-21. Owner: Member A.
Script: `database/seed/seed_demo.py`, reads `database/seed/catalog_inventory.csv`.

## How to run

From the repo root, with `.env` filled in and the migrations at head (`0003_documents_sync`):

```
python database/seed/seed_demo.py --db test   # smartcampus_test
python database/seed/seed_demo.py --db main   # neondb (demo database)
```

The script **empties all 18 tables first** (TRUNCATE ... RESTART IDENTITY), so it can be re-run any time and always gives the same ids.

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
| app_user | 10 | 5 staff (admin, IIT and ISB academic staff, interviewer, direction) + 5 candidates |
| candidate_profile | 5 | Bac Math, Sciences, Eco-Gestion, Technique, and one Licence 3 |
| application | 5 | One at each stage: draft, submitted, qcm_pending, interview_scheduled, enrolled |
| application_history | 16 | Written by the trigger; the candidate creates and submits, staff do every later step |
| recommendation | 5 | 2 proposed, 3 confirmed by IIT academic staff |
| source_document / document_chunk | 5 / 5 | Real IIT/ISB pages, one chunk each, no embedding yet |
| sync_job | 1 | A finished crawler run |

## Things to know

- All people and emails are fake (`@example.com`). Accounts have no password yet; Member B's auth (SA-28) sets them.
- Fees marked "/9 mois" on the site are stored as `period = month, installments = 9` until the admissions office confirms what they mean. Programs with no published fee have no tariff row.
- Chunks have no embedding: Member C's pipeline fills `embedding` once the model is chosen.

## Tested

On PostgreSQL 16 + pgvector after the three migrations: runs twice in a row with the same counts, each history row is attributed to the right person, and accepted backgrounds and tariffs match the CSV.
