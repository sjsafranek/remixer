import io
import json
from src import cmd
from src import database

from pydub import AudioSegment
from pydub import playback


if __name__ == "__main__":
    parser = cmd.getArgumentParser()
    parser.add_argument('-song_id', type=int, required=True, help='Song ID containing beat')
    parser.add_argument('-beat_id', type=int, required=True, help='Beat ID to play')
    args = parser.parse_args()

    db = database.Database(
        host=args.dbhost,
        port=args.dbport,
        dbname=args.dbname,
        user=args.dbuser,
        password=args.dbpass
    )

    songs = db.getSongs(id = args.song_id)
    if 0 == songs:
        print("Not Found")
        exit(1)

    beats = songs[0].getBeats(id = args.beat_id)
    if 0 == beats:
        print("Not Found")
        exit(1)

    clip = io.BytesIO(beats[0].clip.tobytes())
    segment = AudioSegment.from_file(clip, format=beats[0].format)
    playback.play(segment)
