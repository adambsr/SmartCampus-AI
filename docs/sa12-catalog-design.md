# SA-12: Academic catalog tables

Status: draft for team review, 2026-11-19. Owner: Member A.
SQL: `db/catalog_schema.sql`. Real programs found on iit.tn and isb.tn: `db/catalog_inventory.csv` (31 programs).

## Tables (9)

| Table | Purpose | Key columns |
| --- | --- | --- |
| institution | IIT, ISB | code (unique), name, city, website |
| program | One row per formation | institution_id, code (unique), name, level, program_type, field, duration_years, credits, teaching_language, career_outcomes[], key_modules[], labels[], source_url, is_active |
| specialization | Options inside a program | program_id, name |
| admission_requirement | How to enter a program (one per program) | program_id, entry_level (bac, bac+2, licence, master), selection_steps[], min_average, language_requirement, required_documents[] |
| accepted_background | What a requirement accepts, one row per item | requirement_id, kind (bac_section, prepa_track, licence_specialty, diploma), value |
| tariff | Fees per program, year and student category | program_id, academic_year, student_category (national, international), amount, currency, period (month, year, total), installments, is_confirmed |
| fee_rule | Institution-wide fee rules | institution_id, rule, percent |
| pathway | Passerelles between programs | from_program_id, to_program_id, condition |
| admission_campaign | Pre-registration windows | institution_id, academic_year, opens_at, closes_at, status |

## Decisions taken from the official sites

1. **Engineering admission is by prior diploma, not bac average.** IIT's admission criteria (PDF DC-SC-17) accept a prépa diploma (MP/PC/PT) or a licence from a fixed list of specialties per génie, then file review, interview and test. That list lives in `accepted_background` so the agent can answer "can I enter Génie Informatique with a licence in X?".
2. **Licences list accepted bac sections**, e.g. Génie Logiciel accepts Math, Sciences, Informatique, Économie et Gestion, Technique. Same table, `kind = bac_section`.
3. **Fees have two categories and a period.** IIT pages show "667DT/9 mois" (national) and "189€/9 mois" (international), so a tariff row stores amount, currency, period and installments. `is_confirmed = false` until the admissions office confirms.
4. **Fee rules are separate** because they apply to the whole institution: 5% discount for full payment at registration, +5% per year for new students, no refund after registration, exchange rate of 1 October for international students.
5. **The four IIT informatique licences are separate programs**, not specializations, because each has its own page, prerequisites and fees.
6. Every fact row keeps a `source_url`, so the agent can cite where an answer comes from.

## Open questions

- "/9 mois": is the amount paid per month over 9 months? Prépa shows 5800 DT/year on one page and 556 DT/9 mois on another.
- Fees are not published for the 5 engineering programs (except Génie Civil), Architecture, and all ISB programs.
- ISB has both "Économie de Transport et de la Logistique" and "Transport et Logistique": two programs or one?
- The IIT Mastère page has no exact title and contains demo text.
