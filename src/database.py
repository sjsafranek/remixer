import json
import psycopg2

from .music import getKeyFromNotes


class Collection(object):
    def __init__(self, models):
        self.models = models

    def filter(self, rules):
        print("TODO")


class Model(object):

    table = None

    columns = []

    def __init__(self, id, db):
        self.id = id
        self.db = db

    def getDatabase(self):
        return self.db

    def getCursor(self):
        return self.getDatabase().getCursor()

    def set(self, columnId, value):
        with self.getCursor() as cursor:
            cursor.execute(
                """UPDATE {0} SET {1} = %s WHERE id = %s;""".format(
                    self.table, columnId
                ),
                (value, self.id,),
            )
            self.save()

    def save(self):
        self.getDatabase().commit()

    def undo(self):
        self.getDatabase().rollback()

    def get(self, columns=[]):
        if list == type(columns):
            column = ",".join(columns)
        with self.getCursor() as cursor:
            cursor.execute(
                """SELECT {0} FROM {1} WHERE id = %s;""".format(column, self.table),
                (self.id,),
            )
            results = cursor.fetchone()
        return results

    def delete(self):
        with self.getCursor() as cursor:
            cursor.execute(
                """DELETE FROM {0} WHERE id = %s;""".format(self.table), (self.id,)
            )
            self.save()

    def toDict(self):
        values = self.get(columns = self.columns)
        return {self.columns[i]: values[i] for i in range(len(self.columns))}



class Beat(Model):

    table = "beats"

    columns = [
        'id',
        'end',
        'start'
    ]

    def __init__(self, id, db, song):
        super(Beat, self).__init__(id, db)
        self.song = song

    @property
    def end(self):
        return self.get('end')[0]

    @property
    def start(self):
        return self.get('start')[0]

    def importNotes(self, notes):
        with self.getCursor() as cursor:
            for note in notes:
                cursor.execute(
                    """INSERT INTO notes (beat_id, note, "power", frequency)
                                    VALUES (%s, %s, %s, %s);""",
                    (self.id, note["note"], note["power"], note["frequency"]),
                )
            self.save()

    @property
    def notes(self):
        with self.getCursor() as cursor:
            cursor.execute(
                """SELECT json_agg(c) FROM (SELECT * FROM notes WHERE beat_id = %s) AS c;""",
                (self.id,),
            )
            results = cursor.fetchall()
        return results[0][0]

    def importNoteSet(self, noteset):
        with self.getCursor() as cursor:
            for note in noteset:
                cursor.execute(
                    """INSERT INTO notesets (beat_id, note, "power")
                                    VALUES (%s, %s, %s)""",
                    (self.id, note["note"], note["power"]),
                )
            self.save()

    @property
    def noteset(self):
        with self.getCursor() as cursor:
            cursor.execute(
                """SELECT json_agg(c) FROM (SELECT * FROM notesets WHERE beat_id = %s) AS c;""",
                (self.id,),
            )
            results = cursor.fetchall()
        return results[0][0]


class Song(Model):

    table = "songs"

    columns = [
        'id',
        'filename',
        'title',
        'album',
        'artist',
        'genre',
        'year',
        'key'
    ]

    @property
    def filename(self):
        return self.get(columns=['filename'])[0]

    @property
    def title(self):
        return self.get(columns=['title'])[0]

    @property
    def album(self):
        return self.get(columns=['album'])[0]

    @property
    def artist(self):
        return self.get(columns=['artist'])[0]

    @property
    def genre(self):
        return self.get(columns=['genre'])[0]

    @property
    def year(self):
        return self.get(columns=['year'])[0]

    @property
    def key(self):
        return self.get(columns=['key'])[0]

    def reset(self):
        with self.getCursor() as cursor:
            cursor.execute(
                """
                DELETE FROM beats WHERE song_id = %s;
            """,
                (self.id,),
            )
            self.save()

    def createBeat(self, start, end):
        with self.getCursor() as cursor:
            cursor.execute(
                """INSERT INTO beats (song_id, start, "end")
                                VALUES (%s, %s, %s)
                                RETURNING id;""",
                (self.id, start, end,),
            )
            results = cursor.fetchone()
            if not results or 0 == len(results):
                self.undo()
                return None
            self.save()
        return Beat(results[0], self.getDatabase(), self)

    @property
    def beats(self):
        with self.getCursor() as cursor:
            cursor.execute("""SELECT id FROM beats WHERE song_id = %s;""", (self.id,))
            results = cursor.fetchall()
        return Collection([Beat(id, self.db, self) for id in results])

    def importBeats(self, generator):
        try:
            all_notes = []
            for chunk in generator:
                print(json.dumps(chunk, separators=(",", ":")))
                beat = self.createBeat(
                    int(chunk["start"] * 1000), int(chunk["end"] * 1000)
                )
                beat.importNotes(chunk["notes"])
                beat.importNoteSet(chunk["noteset"])
                if len(chunk["noteset"]) > 0:
                    all_notes.append(chunk["noteset"][0]["note"])
            key = getKeyFromNotes(all_notes)
            self.set("key", key)
        except Exception as err:
            print(err)
            print("Rolling back")
            self.reset()


class Database(object):
    def __init__(
        self,
        host="localhost",
        port=5432,
        dbname="remixerdb",
        user="remixeruser",
        password="dev",
    ):
        self.options = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self.conn = psycopg2.connect(self.connectionString)

    @property
    def connectionString(self):
        return "host='{0}' port='{1}' dbname='{2}' user='{3}' password='{4}'".format(
            self.options["host"],
            self.options["port"],
            self.options["dbname"],
            self.options["user"],
            self.options["password"],
        )

    def getCursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def createSong(
        self, filename, title=None, album=None, artist=None, genre=None, year=None
    ):
        with self.getCursor() as cursor:
            cursor.execute(
                """INSERT INTO songs (filename, title, artist, genre, album, year)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING id;""",
                (filename, title, artist, genre, album, year,),
            )
            results = cursor.fetchone()
            if not results or 0 == len(results):
                conn.rollback()
                return None
            self.conn.commit()
        return Song(results[0], self)

    def _getSongs(self, query, params):
        with self.getCursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
        return Collection([Song(id, self) for id in results])

    def getSongsByFilename(self, filename):
        return self._getSongs(
            """SELECT id FROM songs WHERE filename = %s;""", (filename,)
        )

    def getSongsByTitle(self, title):
        return self._getSongs("""SELECT id FROM songs WHERE title = %s;""", (title,))

    def getSongsById(self, id):
        return self._getSongs("""SELECT id FROM songs WHERE id = %s;""", (id,))

    # def fetchSongsWithNoteSet__depricated(self, noteset, minPower=1, maxPower=100):
    #     cursor = self.conn.cursor()
    #     cursor.execute(
    #         """
    #         SELECT json_agg(c) FROM (
    #             SELECT
    #                 count(*) AS matches,
    #                 (
    #                     SELECT
    #                         count(*)
    #                     FROM beats AS b1
    #                     WHERE b1.song_id = songs.id
    #                 ) AS total,
    #                 (
    #                     SELECT
    #                         sv1.song_json
    #                     FROM songs_view AS sv1
    #                     WHERE sv1.id = songs.id
    #                 ) AS song
    #             FROM beats AS beats
    #             LEFT JOIN songs AS songs
    #                 ON beats.song_id = songs.id
    #             WHERE
    #                 %s::JSONB <@ (
    #                     SELECT to_jsonb(n.noteset) FROM (
    #                         SELECT
    #                             array_agg(notesets.note) AS noteset
    #                         FROM notesets
    #                         WHERE
    #                             notesets.beat_id = beats.id
    #                         GROUP BY notesets.beat_id
    #                     ) AS n
    #                 )
    #             GROUP BY songs.id
    #         ) AS c;
    #     """,
    #         (json.dumps(noteset),),
    #     )
    #     results = cursor.fetchone()
    #     if not results or 0 == len(results):
    #         return None
    #     cursor.close()
    #     return results[0]

    def fetchSongsWithNoteSet(self, noteset, minPower=1, maxPower=100):
        cursor = self.conn.cursor()
        cursor.execute(
"""
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

""",
            (json.dumps(noteset),),
        )
        results = cursor.fetchone()
        if not results or 0 == len(results):
            return None
        cursor.close()
        return results[0]
