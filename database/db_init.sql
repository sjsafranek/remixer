
CREATE DATABASE remixerdb;

\c remixerdb


-- Create URL data type
-- https://www.cybertec-postgresql.com/en/postgresql-useful-new-data-types/

DROP DOMAIN IF EXISTS url CASCADE;

CREATE DOMAIN url AS text
CHECK (VALUE ~ 'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#()?&//=]*)');

COMMENT ON DOMAIN url IS 'match URLs (http or https)';



-- Create table for songs

DROP TABLE IF EXISTS songs CASCADE;

CREATE TABLE IF NOT EXISTS songs (
    id      SERIAL PRIMARY KEY,
    name    VARCHAR NOT NULL,
    artist  VARCHAR,
    genre   VARCHAR,
    url     URL
);


-- Create table for notes
DROP TABLE IF EXISTS notes CASCADE;

CREATE TABLE IF NOT EXISTS notes (
    song_id     INTEGER NOT NULL,
    start       BIGINT NOT NULL,
    "end"         BIGINT NOT NULL,
    confidence  REAL,
    chord       VARCHAR,
    notes       JSONB,
    freqs       JSONB,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE(song_id, start, "end")
);

SELECT create_hypertable('notes', 'start', chunk_time_interval=>100000);
