
CREATE DATABASE remixerdb;

\c remixerdb


-- Create URL data type
-- https://www.cybertec-postgresql.com/en/postgresql-useful-new-data-types/

DROP DOMAIN IF EXISTS url CASCADE;

CREATE DOMAIN url AS text
CHECK (VALUE ~ 'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#()?&//=]*)');

COMMENT ON DOMAIN url IS 'match URLs (http or https)';





-- @function update_modified_column
-- @description updates record updated_at column
--              with current timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
$$ language 'plpgsql';



-- -- create function for casting jsonb array to text array
-- CREATE OR REPLACE FUNCTION jsonb_array_cast2text(jsonb) RETURNS text[] AS $f$
--     SELECT
--         array_agg(x)::text[] || ARRAY[]::text[]
--     FROM jsonb_array_elements_text($1) t(x);
-- $f$ LANGUAGE sql IMMUTABLE;



-- Create table for songs

DROP TABLE IF EXISTS songs CASCADE;

CREATE TABLE IF NOT EXISTS songs (
    id                      SERIAL PRIMARY KEY,
    filename                VARCHAR NOT NULL,
    title                   VARCHAR,
    artist                  VARCHAR,
    genre                   VARCHAR,
    album                   VARCHAR,
    year                    INTEGER,
    url                     URL,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- @trigger users_update
DROP TRIGGER IF EXISTS songs_update ON songs;
CREATE TRIGGER songs_update
    BEFORE UPDATE ON songs
        FOR EACH ROW
            EXECUTE PROCEDURE update_modified_column();


DROP VIEW IF EXISTS songs_view CASCADE;

CREATE OR REPLACE VIEW songs_view AS (
    SELECT
        *,
        json_build_object(
            'id', songs.id,
            'filename', songs.filename,
            'title', songs.title,
            'artist', songs.artist,
            'album', songs.album,
            'year', songs.year,
            'genre', songs.genre,
            'url', songs.url,
            'created_at', to_char(songs.created_at, 'YYYY-MM-DD"T"HH:MI:SS"Z"'),
            'updated_at', to_char(songs.updated_at, 'YYYY-MM-DD"T"HH:MI:SS"Z"')
        ) AS song_json
    FROM songs
);







-- Create table for beats
DROP TABLE IF EXISTS beats CASCADE;

CREATE TABLE IF NOT EXISTS beats (
    id                  SERIAL PRIMARY KEY,
    song_id             INTEGER NOT NULL,
    start               BIGINT NOT NULL,
    "end"               BIGINT NOT NULL,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE(song_id, start, "end")
);

-- SELECT create_hypertable('notes', 'start', chunk_time_interval=>100000);


-- Create table for notes
DROP TABLE IF EXISTS notes CASCADE;

CREATE TABLE IF NOT EXISTS notes (
    beat_id             INTEGER NOT NULL,
    song_id             INTEGER NOT NULL,
    note                VARCHAR,
    frequency           REAL,
    "power"             INTEGER,
    FOREIGN KEY (beat_id) REFERENCES beats(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE(beat_id, song_id, note)
);


-- Create table for notesets
DROP TABLE IF EXISTS notesets CASCADE;

CREATE TABLE IF NOT EXISTS notesets (
    beat_id             INTEGER NOT NULL,
    song_id             INTEGER NOT NULL,
    note                VARCHAR,
    "power"             VARCHAR,
    FOREIGN KEY (beat_id) REFERENCES beats(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE(beat_id, song_id, note)
);


--
