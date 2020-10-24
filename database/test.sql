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
    songs.*,
    count(*) AS matches,
    (SELECT count(*) FROM notes AS n2 WHERE n2.song_id = songs.id) AS total
FROM notes
LEFT JOIN songs ON notes.song_id = songs.id
WHERE
    '["G#","B"]'::JSONB <@ noteset
GROUP BY songs.id
;
