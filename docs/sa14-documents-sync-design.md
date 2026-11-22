# SA-14: Documents and synchronisation tables

Status: draft for team review, 2026-11-21. Owner: Member A.
SQL: `database/schema/documents_sync_schema.sql` (apply after SA-12 and SA-13). Needs pgvector.

## Tables (4)

| Table | Purpose | Key columns |
| --- | --- | --- |
| source_document | One official IIT/ISB page or PDF used by the RAG | external_id (crawler document_id), institution_id, program_id, title, document_type, format (html, pdf), source_url, language, academic_year, content (Markdown), checksum, version, status (active, needs_ocr, archived), crawled_at, last_synced_at |
| document_chunk | A piece of a document plus its embedding | document_id, chunk_index, heading_path, content, token_count, embedding (pgvector), embedding_model, metadata |
| sync_job | One row per crawler run or re-import | institution_id, triggered_by, started_at, finished_at, status, documents_seen, added, updated, unchanged, archived, errors, error_log |
| application_document | A file a candidate uploads | application_id, kind (bac_transcript, diploma, transcript, id_card, cv, other), file_path, original_name, mime_type, size_bytes, verified_by, verified_at |

## Decisions

1. **Built around the crawler's manifest.** Each `manifest.jsonl` record maps to one `source_document`: document_id → external_id, document_type, source_url, language, academic_year, content_path, crawl_date → crawled_at. `document_type` uses the crawler's exact 14 values. Tested by loading the 27 records of the crawler's sample run.
2. **Scanned PDFs are kept, not invented.** The crawler flags PDFs without text as needing OCR; they get `status = needs_ocr` and no content.
3. **Change detection:** `checksum` (SHA-256) lets a sync skip unchanged documents, and `version` goes up when content changes, so the agent can say how fresh an answer is (`last_synced_at`).
4. **Embedding size left open.** `embedding` is a plain `vector` until Member C picks the embedding model. Then SA-17 fixes the size and adds the HNSW index (`vector_cosine_ops`).
5. **Candidate uploads are separate** from the RAG corpus and store a private storage key, never a public URL. A file counts as verified only when both verified_by and verified_at are set.

## For Member C (RAG)

- Read chunks with `ORDER BY embedding <=> :query_vector LIMIT k` and join `source_document` to cite `title` and `source_url`.
- Tell Member A the embedding model and its dimension so the column and index can be finalised.

## Tested

On PostgreSQL 16 + pgvector: tables create after SA-12 and SA-13 (18 tables total), the 27 sample manifest records load, and a cosine-distance search on document_chunk returns the closest chunk.
