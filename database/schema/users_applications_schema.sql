-- SmartCampus AI - SA-13 Users and applications tables (draft for review)
-- Track A. Requires catalog_schema.sql (SA-12) to be applied first:
-- it references program, institution and admission_campaign.

BEGIN;

-- Closed lists ---------------------------------------------------------------
-- Roles follow the actors of the project spec. Academic staff are tied to one
-- institution (IIT or ISB) through app_user.institution_id.
CREATE TYPE user_role AS ENUM ('candidate', 'academic_staff', 'interviewer', 'direction', 'admin');
CREATE TYPE preferred_language AS ENUM ('fr', 'tn', 'arabizi', 'ar', 'en');
CREATE TYPE application_status AS ENUM (
    'draft', 'submitted', 'qcm_pending', 'interview_scheduled',
    'accepted', 'waitlisted', 'rejected', 'enrolled', 'abandoned'
);
CREATE TYPE recommendation_status AS ENUM ('proposed', 'confirmed', 'adjusted', 'rejected');
CREATE TYPE recommendation_source AS ENUM ('agent', 'staff');

-- User account (all actors). Auth itself (SA-28) is built by Member B on this table.
CREATE TABLE app_user (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email           TEXT NOT NULL,
    password_hash   TEXT,                        -- NULL until the account is activated
    full_name       TEXT NOT NULL,
    phone           TEXT,
    role            user_role NOT NULL DEFAULT 'candidate',
    institution_id  BIGINT REFERENCES institution(id),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- academic staff must belong to IIT or ISB
    CHECK (role <> 'academic_staff' OR institution_id IS NOT NULL)
);
CREATE UNIQUE INDEX app_user_email_lower_idx ON app_user (lower(email));

-- Candidate profile, filled step by step by the conversation agent
CREATE TABLE candidate_profile (
    user_id             BIGINT PRIMARY KEY REFERENCES app_user(id) ON DELETE CASCADE,
    birth_year          SMALLINT CHECK (birth_year BETWEEN 1950 AND 2020),
    city                TEXT,
    nationality         TEXT,
    current_level       TEXT,                    -- 'Bac', 'Prépa 2', 'Licence 3' ...
    bac_section         TEXT,                    -- 'Math', 'Sciences', 'Informatique' ...
    bac_year            SMALLINT,
    bac_average         NUMERIC(4,2) CHECK (bac_average BETWEEN 0 AND 20),
    last_diploma        TEXT,                    -- for bac+2 / licence entries
    last_diploma_specialty TEXT,
    favorite_subjects   TEXT[],
    interests           TEXT[],
    career_goal         TEXT,
    constraints         TEXT,                    -- budget, city, schedule ...
    preferred_language  preferred_language NOT NULL DEFAULT 'fr',
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Application = the pre-registration (préinscription) to one program in one campaign
CREATE TABLE application (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    program_id    BIGINT NOT NULL REFERENCES program(id),
    campaign_id   BIGINT REFERENCES admission_campaign(id),
    status        application_status NOT NULL DEFAULT 'draft',
    consent_at    TIMESTAMPTZ,                   -- data-processing consent, required once submitted
    source        TEXT NOT NULL DEFAULT 'chatbot', -- 'chatbot', 'web_form', 'staff'
    submitted_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, program_id, campaign_id),
    CHECK (status = 'draft' OR consent_at IS NOT NULL)
);
CREATE INDEX application_status_idx ON application (status);
CREATE INDEX application_program_idx ON application (program_id);

-- Every status change, for the follow-up and the direction dashboard funnel
CREATE TABLE application_history (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id  BIGINT NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    from_status     application_status,          -- NULL for the creation row
    to_status       application_status NOT NULL,
    changed_by      BIGINT REFERENCES app_user(id),
    note            TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX application_history_app_idx ON application_history (application_id, changed_at);

-- Write the history automatically. The backend can say who made the change with:
--   SET LOCAL app.user_id = '<id>';   inside the same transaction
CREATE FUNCTION log_application_status() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' OR NEW.status IS DISTINCT FROM OLD.status THEN
        INSERT INTO application_history (application_id, from_status, to_status, changed_by)
        VALUES (NEW.id,
                CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.status END,
                NEW.status,
                NULLIF(current_setting('app.user_id', true), '')::BIGINT);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER application_status_history
AFTER INSERT OR UPDATE OF status ON application
FOR EACH ROW EXECUTE FUNCTION log_application_status();

-- Recommendation: a program suggested to a candidate, with a score and a justification
CREATE TABLE recommendation (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    program_id     BIGINT NOT NULL REFERENCES program(id),
    score          NUMERIC(5,2) CHECK (score BETWEEN 0 AND 100),  -- compatibility %
    rank           SMALLINT,                     -- 1 = best match in the shortlist
    justification  TEXT NOT NULL,
    source         recommendation_source NOT NULL DEFAULT 'agent',
    status         recommendation_status NOT NULL DEFAULT 'proposed',
    reviewed_by    BIGINT REFERENCES app_user(id),
    reviewed_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (status = 'proposed' OR reviewed_by IS NOT NULL)
);
CREATE INDEX recommendation_user_idx ON recommendation (user_id, created_at);

COMMIT;
