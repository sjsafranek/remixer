# import io
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

    def createSong(self, songname, artist, genre):
        cursor = self.conn.cursor()
        cursor.execute("""INSERT INTO songs (name, artist, genre) VALUES (%s, %s, %s) RETURNING id;""", (songname, artist, genre,))
        results = cursor.fetchone()
        if not results or 0 == len(results):
            conn.rollback()
            return None
        self.conn.commit()
        cursor.close()
        return results[0]

    def importSongChunks(self, songId, generator):
        cursor = self.conn.cursor()
        for chunk in generator:
            print(chunk)
            cursor.execute("""INSERT INTO notes (song_id, start, "end", confidence, chord, notes, noteset, freqs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (
                    songId,
                    int(chunk["start"] * 1000),
                    int(chunk["end"] * 1000),
                    chunk["confidence"],
                    chunk["chord"],
                    json.dumps(chunk["notes"]),
                    json.dumps(chunk["noteset"]),
                    json.dumps(chunk["freqs"])
                )
            )
        self.conn.commit()
        cursor.close()