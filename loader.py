import tempfile
import traceback

from src import cmd
from src.audiofile import AudioFile
from src import database
# from src import pipeline_wav
from src.analyze_wav import AudioAnalyzer



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
    fname = filename
    afile = AudioFile(filename)

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="wb") as fileHandler:

        afile.convert(out_filehandler = fileHandler, out_format="wav")

        fname = fileHandler.name

        # Make the generator
        aa = AudioAnalyzer(fname)
        generator = aa.getBeatsWithNotes()

        # Don't import data if running a dry run
        if args.dryrun:
            for chunk in generator:
                print(chunk)
            exit()

        # Create song record
        song = db.createSong(
            filename,
            title = afile.tags.title,
            album = afile.tags.album,
            artist = afile.tags.artist,
            genre = afile.tags.genre,
            year = afile.tags.year
        )

        # Read file and insert chunks to database
        try:
            song.importBeats(generator)
        except Exception as e:
            print(e)
            print(traceback.print_tb)
