-- https://www.postgresql.org/docs/12/functions-array.html


SELECT * FROM notes;



CREATE OR REPLACE FUNCTION jsonb_array_casttext(jsonb) RETURNS text[] AS $f$
    SELECT
        array_agg(x)::text[] || ARRAY[]::text[]
    FROM jsonb_array_elements_text($1) t(x);
$f$ LANGUAGE sql IMMUTABLE;



-- Select every record with at least a G# and B
SELECT
    DISTINCT songs.name
FROM notes
LEFT JOIN songs ON notes.song_id = songs.id
WHERE
    -- ARRAY['"G#"','"B"'] <@ ARRAY(SELECT jsonb_array_elements::TEXT FROM jsonb_array_elements(noteset))
    ARRAY['G#','B'] <@ jsonb_array_casttext(noteset)
;
