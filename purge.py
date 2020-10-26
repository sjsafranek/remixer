import json
from src import cmd
from src import database


if __name__ == "__main__":
    parser = cmd.getArgumentParser()
    args = parser.parse_args()

    db = database.Database(
        host=args.dbhost,
        port=args.dbport,
        dbname=args.dbname,
        user=args.dbuser,
        password=args.dbpass
    )

    # songs = db.getSongs()
    # iterator = iter(songs)
    # while True:
    #     try:
    #         song = next(iterator)
    #         song.delete()
    #     except StopIteration:
    #         break

    songs = db.getSongs()
    for song in songs:
        song.delete()
