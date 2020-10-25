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

WITH matching_song_beats AS (
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
    song_beats AS (
        SELECT
            matching_song_beats.song_id,
            matching_song_beats.beat_id,
            json_agg(notesets.*) AS noteset,
            json_agg(notes.*) AS notes
        FROM matching_song_beats
        LEFT JOIN notesets
            ON notesets.beat_id = matching_song_beats.beat_id
        LEFT JOIN notes
            ON notes.beat_id = matching_song_beats.beat_id
        GROUP BY matching_song_beats.song_id, matching_song_beats.beat_id
    ),
    song_beats_full AS (
        SELECT
            song_beats.song_id,
            song_beats.beat_id,
            json_build_object(
                'id', song_beats.beat_id,
                'start', beats.start,
                'end', beats.end,
                'notes', song_beats.notes,
                'noteset', song_beats.noteset
            ) AS beat
        FROM song_beats
        INNER JOIN beats
            ON beats.id = song_beats.beat_id
    )

--
SELECT * FROM song_beats_full;

SELECT json_agg(c) FROM (
    SELECT * FROM song_beats_full
) AS c;





SELECT
    count(DISTINCT songbeats.beat_id) AS matches,
    (
        SELECT
            count(*)
        FROM beats AS b1
        WHERE b1.song_id = songbeats.song_id
    ) AS total,
    (
        SELECT
            sv1.song_json
        FROM songs_view AS sv1
        WHERE sv1.id = songbeats.song_id
    ) AS song,
    noteset,
    notes
FROM song_beats AS songbeats GROUP BY song_id, noteset, notes;








SELECT json_agg(c) FROM (


) AS c;
