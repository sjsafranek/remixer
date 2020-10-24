
from src import cmd
from src import utils
from src import database
from src import pipeline_wav


if __name__ == "__main__":
    parser = cmd.getArgumentParser()
    parser.add_argument('-file', type=str, help='song file')
    parser.add_argument('-name', type=str, help='song name')
    parser.add_argument('-artist', type=str, help='artist')
    parser.add_argument('-genre', type=str, help='genre')
    parser.add_argument('--dryrun', action='store_true', help='does not do database writes')
    parser.set_defaults(dryrun=False)
    args = parser.parse_args()

    # Create database
    db = database.Database(
        host=args.dbhost,
        port=args.dbport,
        dbname=args.dbname,
        user=args.dbuser,
        password=args.dbpass
    )

    filename = args.file

    def ingestSong(tmpfile):
        # Collect metadata tags
        tags = utils.getAudioTags(filename)

        generator = pipeline_wav.pipeline_wav(tmpfile)

        if args.dryrun:
            for chunk in generator:
                print(chunk)
            return

        # Create song record
        songId = db.createSong(
            filename,
            title=tags.title,
            album = tags.album,
            artist = tags.artist,
            genre = tags.genre,
            year = tags.year
        )

        # Read file and insert chunks to database
        db.importSongChunks(songId, generator)

    # Convert to WAV file if needed
    utils.convertAudioToWav(filename, callback=ingestSong)
