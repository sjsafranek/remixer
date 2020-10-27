import tempfile
import traceback

from src import cmd
from src.audiofile import AudioFile
from src import database
from src.analyze_wav import AudioAnalyzer



if __name__ == "__main__":
    parser = cmd.getArgumentParser()
    parser.add_argument('-file', type=str, help='song file')
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

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="wb") as fileHandler:

        filename = args.file

        afile = AudioFile(filename)
        afile.convert(out_filehandler = fileHandler, out_format="wav")

        fname = fileHandler.name

        # Make the generator
        analyzer = AudioAnalyzer(fname)

        # Don't import data if running a dry run
        if args.dryrun:
            for chunk in analyzer.getBeatsWithNotes():
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
            song.importBeatsFromAudioAnalyzer(analyzer)
        except Exception as e:
            print(e)
            print(traceback.print_tb)
