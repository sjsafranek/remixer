-- https://www.postgresql.org/docs/12/functions-array.html


SELECT * FROM notes;



-- Select every record with at least a G# and B
SELECT
    songs.*, count(*)
FROM notes
LEFT JOIN songs ON notes.song_id = songs.id
WHERE
    ARRAY['G#','B'] <@ jsonb_array_cast2text(noteset)
GROUP BY songs.id
;




SELECT
    json_build_object(
        'song', json_build_object(
            'id', songs.id,
            'name', songs.name,
            'artist', songs.artist,
            'genre', songs.genre,
            'url', songs.url,
            'created_at', to_char(songs.created_at, 'YYYY-MM-DD"T"HH:MI:SS"Z"'),
            'updated_at', to_char(songs.updated_at, 'YYYY-MM-DD"T"HH:MI:SS"Z"')
        ),
        'matches', count(*),
        'total', (SELECT count(*) FROM notes AS n2 WHERE n2.song_id = songs.id)
    ) AS song
FROM notes
LEFT JOIN songs ON notes.song_id = songs.id
WHERE
    '["G#","B"]'::JSONB <@ noteset
GROUP BY songs.id
;




SELECT
    json_build_object(
        'song',  (SELECT sv.song_json FROM songs_view AS sv WHERE sv.id = songs.id),
        'matches', count(*),
        'total', (SELECT count(*) FROM notes AS n2 WHERE n2.song_id = songs.id)
    ) AS song
FROM notes
LEFT JOIN songs AS songs ON notes.song_id = songs.id
WHERE
    '["G#","B"]'::JSONB <@ noteset
GROUP BY songs.id
;



SELECT json_agg(c) FROM (
    SELECT
        json_build_object(
            'song',  (SELECT sv.song_json FROM songs_view AS sv WHERE sv.id = songs.id),
            'matches', count(*),
            'total', (SELECT count(*) FROM notes AS n2 WHERE n2.song_id = songs.id)
        ) AS song
    FROM notes
    LEFT JOIN songs AS songs ON notes.song_id = songs.id
    WHERE
        '["G#","B"]'::JSONB <@ noteset
    GROUP BY songs.id
) AS c;
