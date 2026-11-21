-- SmartCampus AI - SA-12 Academic catalog tables (draft for review)
-- Track A. Target: PostgreSQL on Neon. In SA-17 these become Alembic migrations.
-- Safe to run on the test database (smartcampus_test) to check the design.

BEGIN;

-- Closed lists ---------------------------------------------------------------
CREATE TYPE program_level AS ENUM ('prepa', 'licence', 'ingenieur', 'mastere', 'mba', 'architecture');
CREATE TYPE entry_level   AS ENUM ('bac', 'bac+2', 'licence', 'master');
CREATE TYPE background_kind AS ENUM ('bac_section', 'prepa_track', 'licence_specialty', 'diploma');
CREATE TYPE student_category AS ENUM ('national', 'international');
CREATE TYPE fee_period AS ENUM ('month', 'year', 'total');
CREATE TYPE campaign_status AS ENUM ('planned', 'open', 'closed');

-- Institution ----------------------------------------------------------------
CREATE TABLE institution (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,              -- 'IIT', 'ISB'
    name        TEXT NOT NULL,
    city        TEXT,
    website     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Program: one row per formation (Prépa, each licence, each génie, each mastère, MBA)
CREATE TABLE program (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id     BIGINT NOT NULL REFERENCES institution(id),
    code               TEXT NOT NULL UNIQUE,       -- e.g. 'IIT-LIC-GLSI'
    name               TEXT NOT NULL,
    level              program_level NOT NULL,
    program_type       TEXT,                       -- 'Licence nationale', 'Mastère professionnel', ...
    field              TEXT,                       -- 'Informatique', 'Finance', ...
    duration_years     SMALLINT CHECK (duration_years BETWEEN 1 AND 7),
    credits            SMALLINT,
    teaching_language  TEXT NOT NULL DEFAULT 'fr', -- 'fr', 'en'
    start_month        SMALLINT CHECK (start_month BETWEEN 1 AND 12),
    description        TEXT,
    career_outcomes    TEXT[],                     -- débouchés
    key_modules        TEXT[],
    labels             TEXT[],                     -- 'EUR-ACE', 'EURO-INF'
    source_url         TEXT,                       -- official page the facts come from
    is_active          BOOLEAN NOT NULL DEFAULT true,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX program_institution_level_idx ON program (institution_id, level);

-- Specialization: options inside one program (kept for programs that have tracks)
CREATE TABLE specialization (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_id  BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    UNIQUE (program_id, name)
);

-- Admission requirement: how one enters a program
CREATE TABLE admission_requirement (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_id          BIGINT NOT NULL UNIQUE REFERENCES program(id) ON DELETE CASCADE,
    entry_level         entry_level NOT NULL,
    selection_steps     TEXT[],                    -- {'dossier','entretien','test'}
    min_average         NUMERIC(4,2),              -- only where an official minimum exists
    language_requirement TEXT,                     -- 'Anglais et mathématiques solides au bac'
    required_documents  TEXT[],
    notes               TEXT,
    source_url          TEXT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Accepted background: the diplomas / bac sections / prépa tracks / licence specialties
-- that a requirement accepts. One row per accepted item.
CREATE TABLE accepted_background (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    requirement_id  BIGINT NOT NULL REFERENCES admission_requirement(id) ON DELETE CASCADE,
    kind            background_kind NOT NULL,
    value           TEXT NOT NULL,                 -- 'Math', 'MP', 'Informatique de gestion'
    UNIQUE (requirement_id, kind, value)
);

-- Tariff: one row per program, academic year and student category
CREATE TABLE tariff (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    program_id       BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
    academic_year    TEXT NOT NULL CHECK (academic_year ~ '^\d{4}-\d{4}$'),
    student_category student_category NOT NULL,
    amount           NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    currency         CHAR(3) NOT NULL,             -- 'TND', 'EUR'
    period           fee_period NOT NULL,
    installments     SMALLINT,                     -- e.g. 9 for '/9 mois'
    is_confirmed     BOOLEAN NOT NULL DEFAULT false,
    notes            TEXT,
    source_url       TEXT,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (program_id, academic_year, student_category)
);

-- Fee rule: institution-wide rules the agent must quote (discounts, yearly increase, refunds)
CREATE TABLE fee_rule (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id  BIGINT NOT NULL REFERENCES institution(id),
    rule            TEXT NOT NULL,
    percent         NUMERIC(5,2),
    source_url      TEXT
);

-- Pathway: passerelles between programs (Prépa -> Ingénieur, Licence -> Mastère ...)
CREATE TABLE pathway (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    from_program_id  BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
    to_program_id    BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
    condition        TEXT,
    CHECK (from_program_id <> to_program_id),
    UNIQUE (from_program_id, to_program_id)
);

-- Admission campaign: the windows the admin opens per institution and year
CREATE TABLE admission_campaign (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id  BIGINT NOT NULL REFERENCES institution(id),
    academic_year   TEXT NOT NULL CHECK (academic_year ~ '^\d{4}-\d{4}$'),
    opens_at        DATE,
    closes_at       DATE,
    status          campaign_status NOT NULL DEFAULT 'planned',
    CHECK (closes_at IS NULL OR opens_at IS NULL OR closes_at >= opens_at),
    UNIQUE (institution_id, academic_year)
);

COMMIT;
