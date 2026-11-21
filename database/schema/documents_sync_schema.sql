-- SmartCampus AI - SA-14 Documents and synchronisation tables (draft for review)
-- Track A. Requires catalog_schema.sql (SA-12) and users_applications_schema.sql (SA-13).
-- Needs the pgvector extension (already enabled on both Neon databases).
-- Designed to load the smartcampus-crawler output: one manifest.jsonl record = one source_document.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

-- Closed lists ---------------------------------------------------------------
-- Same values as the crawler's document_type (config.yaml -> classification)
CREATE TYPE document_type AS ENUM (
    'academic_program', 'study_plan', 'registration', 'tuition_fees', 'scholarship',
    'regulation', 'career', 'student_services', 'international', 'research',
    'brochure', 'university_info', 'general_page', 'pdf_document'
);
CREATE TYPE document_format AS ENUM ('html', 'pdf');
CREATE TYPE document_status AS ENUM ('active', 'needs_ocr', 'archived');
CREATE TYPE sync_status AS ENUM ('running', 'success', 'partial', 'failed');
CREATE TYPE upload_kind AS ENUM ('bac_transcript', 'diploma', 'transcript', 'id_card', 'cv', 'other');

-- Source document: one official IIT/ISB page or PDF used by the RAG
CREATE TABLE source_document (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id      TEXT NOT NULL UNIQUE,        -- crawler document_id, e.g. 'iit-cec3e0a5a7d2'
    institution_id   BIGINT NOT NULL REFERENCES institution(id),
    program_id       BIGINT REFERENCES program(id), -- set when the document is about one program
    title            TEXT NOT NULL,
    document_type    document_type NOT NULL,
    format           document_format NOT NULL,
    source_url       TEXT NOT NULL UNIQUE,
    language         TEXT,                        -- 'fr', 'en', 'ar', 'fr+en' ...
    academic_year    TEXT CHECK (academic_year ~ '^\d{4}-\d{4}$'),
    content          TEXT,                        -- extracted Markdown (NULL when needs_ocr)
    content_path     TEXT,                        -- crawler path, e.g. markdown/iit/....md
    checksum         CHAR(64),                    -- SHA-256 of the content, to skip unchanged files
    version          INTEGER NOT NULL DEFAULT 1,  -- +1 each time the content changes
    status           document_status NOT NULL DEFAULT 'active',
    crawled_at       TIMESTAMPTZ,                 -- crawler crawl_date
    last_synced_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX source_document_type_idx ON source_document (institution_id, document_type);
CREATE INDEX source_document_program_idx ON source_document (program_id);

-- Document chunk: a piece of a document with its embedding, searched by the RAG.
-- The vector size depends on Member C's embedding model, so it is left open here.
-- Once C picks the model (e.g. 1024 dims), SA-17 fixes it and adds the HNSW index:
--   ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(1024);
--   CREATE INDEX ON document_chunk USING hnsw (embedding vector_cosine_ops);
CREATE TABLE document_chunk (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id    BIGINT NOT NULL REFERENCES source_document(id) ON DELETE CASCADE,
    chunk_index    INTEGER NOT NULL CHECK (chunk_index >= 0),
    heading_path   TEXT,                          -- 'Procédure et frais > Frais d''inscription'
    content        TEXT NOT NULL,
    token_count    INTEGER,
    embedding      vector,                        -- NULL until C's pipeline embeds it
    embedding_model TEXT,                         -- which model produced the vector
    metadata       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

-- Sync job: one row per crawler run / re-import, so the admin sees what changed
CREATE TABLE sync_job (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    institution_id BIGINT REFERENCES institution(id),  -- NULL = both sites
    triggered_by   BIGINT REFERENCES app_user(id),      -- NULL = scheduled run
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    status         sync_status NOT NULL DEFAULT 'running',
    documents_seen INTEGER NOT NULL DEFAULT 0,
    added          INTEGER NOT NULL DEFAULT 0,
    updated        INTEGER NOT NULL DEFAULT 0,
    unchanged      INTEGER NOT NULL DEFAULT 0,
    archived       INTEGER NOT NULL DEFAULT 0,
    errors         INTEGER NOT NULL DEFAULT 0,
    error_log      JSONB NOT NULL DEFAULT '[]'::jsonb, -- copy of the crawler's errors.jsonl lines
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CHECK (status = 'running' OR finished_at IS NOT NULL)
);

-- Application document: a file a candidate uploads for their pre-registration
CREATE TABLE application_document (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    application_id  BIGINT NOT NULL REFERENCES application(id) ON DELETE CASCADE,
    kind            upload_kind NOT NULL,
    file_path       TEXT NOT NULL,               -- storage key, never a public URL
    original_name   TEXT,
    mime_type       TEXT,
    size_bytes      BIGINT CHECK (size_bytes >= 0),
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_by     BIGINT REFERENCES app_user(id),
    verified_at     TIMESTAMPTZ,
    CHECK ((verified_by IS NULL) = (verified_at IS NULL))
);
CREATE INDEX application_document_app_idx ON application_document (application_id);

COMMIT;
