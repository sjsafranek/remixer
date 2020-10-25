-- https://www.postgresql.org/docs/12/functions-array.html



EXPLAIN ANALYZE
SELECT json_agg(c) FROM (
    SELECT
        count(*) AS matches,
        (
            SELECT
                count(*)
            FROM beats AS b1
            WHERE b1.song_id = songs.id
        ) AS total,
        (
            SELECT
                sv1.song_json
            FROM songs_view AS sv1
            WHERE sv1.id = songs.id
        ) AS song
    FROM beats AS beats
    LEFT JOIN songs AS songs
        ON beats.song_id = songs.id
    WHERE
        '["G#","B"]'::JSONB <@ (
            SELECT to_jsonb(n.noteset) FROM (
                SELECT
                    array_agg(notesets.note) AS noteset
                FROM notesets
                WHERE
                    notesets.beat_id = beats.id
                GROUP BY notesets.beat_id
            ) AS n
        )
    GROUP BY songs.id
) AS c;






EXPLAIN ANALYZE
SELECT json_agg(c) FROM (
    SELECT
        count(DISTINCT beat_id) AS matches,
        (
            SELECT
                count(*)
            FROM beats AS b1
            WHERE b1.song_id = songs.id
        ) AS total,
        (
            SELECT
                sv1.song_json
            FROM songs_view AS sv1
            WHERE sv1.id = songs.id
        ) AS song,
        -- json_agg(beats.*) AS beats
        json_agg(
            json_build_object(
                'id', beats.id,
                'song_id', beats.song_id,
                'start', beats.start,
                'end', beats.end
            )
        ) AS beats
    FROM beats AS beats
    LEFT JOIN songs AS songs
        ON beats.song_id = songs.id
    LEFT JOIN notesets AS notesets
        ON notesets.beat_id = beats.id
    WHERE
        '["G#","B"]'::JSONB <@ (
            SELECT to_jsonb(n.noteset) FROM (
                SELECT
                    array_agg(notesets.note) AS noteset
                FROM notesets
                WHERE
                    notesets.beat_id = beats.id
                GROUP BY notesets.beat_id
            ) AS n
        )
    GROUP BY songs.id
) AS c;






















EXPLAIN ANALYZE

WITH song_beat_ids AS (
        SELECT
            songs.id AS song_id,
            beats.id AS beat_id
        FROM beats AS beats
        LEFT JOIN songs AS songs
            ON beats.song_id = songs.id
        LEFT JOIN notesets AS notesets
            ON notesets.beat_id = beats.id
        WHERE
            '["G#","B"]'::JSONB <@ (
                SELECT to_jsonb(n.noteset) FROM (
                    SELECT
                        array_agg(notesets.note) AS noteset
                    FROM notesets
                    WHERE
                        notesets.beat_id = beats.id
                    GROUP BY notesets.beat_id
                ) AS n
            )
        GROUP BY songs.id, beats.id
    ),
    song_beats_with_notes AS (
        SELECT
            song_beat_ids.song_id,
            song_beat_ids.beat_id,
            (
                SELECT json_agg(n) FROM (
                    SELECT notesets.note, notesets.power FROM notesets WHERE notesets.beat_id = song_beat_ids.beat_id
                ) AS n
            ) AS noteset,
            (
                SELECT json_agg(n) FROM (
                    SELECT notes.note, notes.power, notes.frequency FROM notes WHERE notes.beat_id = song_beat_ids.beat_id
                ) AS n
            ) AS notes
        FROM song_beat_ids
        GROUP BY song_beat_ids.song_id, song_beat_ids.beat_id
    ),
    -- song_beats_with_note_objects AS (
    --     SELECT
    --         song_beats_with_notes.song_id,
    --         song_beats_with_notes.beat_id,
    --         json_build_object(
    --             'beat_id', song_beats_with_notes.beat_id,
    --             'start', beats.start,
    --             'end', beats.end,
    --             'notes', song_beats_with_notes.notes,
    --             'noteset', song_beats_with_notes.noteset
    --         ) AS beat
    --     FROM song_beats_with_notes
    --     INNER JOIN beats
    --         ON beats.id = song_beats_with_notes.beat_id
    -- ),
    -- song_beat_objects AS (
    --     SELECT
    --         song_beats_with_note_objects.song_id,
    --         json_agg(song_beats_with_note_objects.beat) AS beats
    --     FROM song_beats_with_note_objects
    --     GROUP BY song_beats_with_note_objects.song_id
    -- )
    song_beat_objects AS (
        SELECT
            song_beats_with_notes.song_id,
            json_agg(
                json_build_object(
                    'beat_id', song_beats_with_notes.beat_id,
                    'start', beats.start,
                    'end', beats.end,
                    'notes', song_beats_with_notes.notes,
                    'noteset', song_beats_with_notes.noteset
                )
            ) AS beats
        FROM song_beats_with_notes
        INNER JOIN beats
            ON beats.id = song_beats_with_notes.beat_id
        GROUP BY song_beats_with_notes.song_id
    )
SELECT
    json_agg(
        json_build_object(
            'song', songs_view.song_json,
            'beats', song_beat_objects.beats
        )
    )
FROM song_beat_objects
INNER JOIN songs_view
    ON songs_view.id = song_beat_objects.song_id;
