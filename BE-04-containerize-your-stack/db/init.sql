-- Initial schema for the Task API.
-- Mounted into the Postgres container via docker-compose and run once
-- on first creation of the volume (docker-entrypoint-initdb.d).

CREATE TABLE IF NOT EXISTS tasks (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT        NOT NULL,
    done        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TEXT        NOT NULL,
    updated_at  TEXT        NOT NULL
);

-- Index used by the stretch "EXPLAIN ANALYZE" demo: speeds up
-- title-based search (ILIKE) and the default ORDER BY title.
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title);

-- Seed a few rows so the API returns data right after `docker compose up`.
INSERT INTO tasks (title, done, created_at, updated_at) VALUES
    ('Buy groceries',        FALSE, now()::text, now()::text),
    ('Read a book',          TRUE,  now()::text, now()::text),
    ('Clean the house',      FALSE, now()::text, now()::text)
ON CONFLICT DO NOTHING;
