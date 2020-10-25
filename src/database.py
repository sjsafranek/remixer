import json
import psycopg2

from .analyze_wav import ks_key


class Collection(object):
    def __init__(self, models):
        self.models = models

    def filter(self, rules):
        print("TODO")


class Model(object):
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

    def get(self, columnId):
        with self.getCursor() as cursor:
            cursor.execute(
                """SELECT {0} FROM {1} WHERE id = %s;""".format(columnId, self.table),
                (self.id,),
            )
            results = cursor.fetchone()
        return results[0]

    def delete(self):
        with self.getCursor() as cursor:
            cursor.execute(
                """DELETE FROM {0} WHERE id = %s;""".format(self.table), (self.id,)
            )
            self.save()


class Beat(Model):

    table = "beats"

    def __init__(self, id, db, song):
        super(Beat, self).__init__(id, db)
        self.song = song

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

    @property
    def filename(self):
        return self.get("filename")

    @property
    def title(self):
        return self.get("title")

    @property
    def album(self):
        return self.get("album")

    @property
    def artist(self):
        return self.get("artist")

    @property
    def genre(self):
        return self.get("genre")

    @property
    def year(self):
        return self.get("year")

    @property
    def key(self):
        return self.get("key")

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
            key = ks_key(all_notes)
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

    def fetchSongsWithNoteSet(self, noteset, minPower=1, maxPower=100):
        cursor = self.conn.cursor()
        cursor.execute(
            """
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
                    %s::JSONB <@ (
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
        """,
            (json.dumps(noteset),),
        )
        results = cursor.fetchone()
        if not results or 0 == len(results):
            return None
        cursor.close()
        return results[0]
