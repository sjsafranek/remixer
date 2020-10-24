
import json
import psycopg2


class Database(object):

    def __init__(self, host="localhost", port=5432, dbname="remixerdb", user="remixeruser", password="dev"):
        self.options = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.conn = psycopg2.connect(self.connectionString)

    @property
    def connectionString(self):
        return "host='{0}' port='{1}' dbname='{2}' user='{3}' password='{4}'".format(
            self.options["host"],
            self.options["port"],
            self.options["dbname"],
            self.options["user"],
            self.options["password"]
        )

    def createSong(self, filename, title=None, album=None, artist=None, genre=None, year=None):
        cursor = self.conn.cursor()
        cursor.execute("""
INSERT INTO songs (filename, title, artist, genre, album, year)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
""", (filename, title, artist, genre, album, year,))
        results = cursor.fetchone()
        if not results or 0 == len(results):
            conn.rollback()
            return None
        self.conn.commit()
        cursor.close()
        return results[0]

    def createBeat(self, songId, start, end):
        cursor = self.conn.cursor()
        cursor.execute("""
INSERT INTO beats (song_id, start, "end")
    VALUES (%s, %s, %s)
    RETURNING id;
""", (songId, start, end,))
        results = cursor.fetchone()
        if not results or 0 == len(results):
            conn.rollback()
            return None
        self.conn.commit()
        cursor.close()
        return results[0]

    def importNotes(self, songId, beatId, notes):
        cursor = self.conn.cursor()
        for note in notes:
            cursor.execute("""
INSERT INTO notes (song_id, beat_id, note, "power", frequency)
    VALUES (%s, %s, %s, %s, %s)
""", (songId, beatId, note["note"], note["power"], note["frequency"]) )
        self.conn.commit()
        cursor.close()

    def importNoteSet(self, songId, beatId, noteset):
        cursor = self.conn.cursor()
        for note in noteset:
            cursor.execute("""
INSERT INTO notesets (song_id, beat_id, note, "power")
    VALUES (%s, %s, %s, %s)
""", (songId, beatId, note["note"], note["power"]) )
        self.conn.commit()
        cursor.close()

    def importSongChunks(self, songId, generator):
        for chunk in generator:
            print(json.dumps(chunk, separators=(',', ':')))
            beatId = self.createBeat(songId, int(chunk["start"] * 1000), int(chunk["end"] * 1000))
            self.importNotes(songId, beatId, chunk["notes"])
            self.importNoteSet(songId, beatId, chunk["noteset"])

    def fetchSongsWithNoteSet(self, noteset):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT json_agg(c) FROM (
                SELECT
                    (SELECT sv.song_json FROM songs_view AS sv WHERE sv.id = songs.id) AS song,
                    count(*) AS matches,
                    (SELECT count(*) FROM beats AS b2 WHERE b2.song_id = songs.id) AS total
                FROM beats
                LEFT JOIN songs AS songs ON notes.song_id = songs.id
                WHERE
                    %s::JSONB <@ noteset
                GROUP BY songs.id
            ) AS c;
        """, (json.dumps(noteset),))
        results = cursor.fetchone()
        if not results or 0 == len(results):
            return None
        cursor.close()
        return results[0]
