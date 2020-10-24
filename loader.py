import json
import argparse
import psycopg2

from src import pipeline_wav

# from database import Database


# Open database connection
conn = psycopg2.connect("host='127.0.0.1' port='5431' dbname='remixerdb' user='postgres' password='dev'")

# Initialize cursor
cur = conn.cursor()


def createSong(songname, artist, genre):
    cur.execute("""INSERT INTO songs (name, artist, genre) VALUES (%s, %s, %s) RETURNING id;""", (songname, artist, genre,))
    results = cur.fetchone()
    if not results or 0 == len(results):
        conn.rollback()
        return None
    conn.commit()
    return results[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Command line client for PyRemixer')
    parser.add_argument('-f', type=str, help='song file')
    parser.add_argument('-n', type=str, help='song name')
    parser.add_argument('-a', type=str, help='artist')
    parser.add_argument('-g', type=str, help='genre')
    args = parser.parse_args()

    filename = args.f

    # Create record in database
    songname = args.n
    if not songname:
        songname = filename

    songId = createSong(songname, args.a, args.g)

    # Read file and insert chunks to database
    for chunk in pipeline_wav.pipeline_wav(filename):
        print(chunk)

        cur.execute("""INSERT INTO notes (song_id, start, "end", confidence, chord, notes, noteset, freqs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (
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

    conn.commit()
    conn.close()
