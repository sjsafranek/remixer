import json
from src import cmd
from src import database


if __name__ == "__main__":

    parser = cmd.getArgumentParser()
    parser.add_argument('noteset', metavar='N', type=str, nargs='+', help='noteset to search for')
    args = parser.parse_args()

    db = database.Database(
        host=args.dbhost,
        port=args.dbport,
        dbname=args.dbname,
        user=args.dbuser,
        password=args.dbpass
    )

    # Normalize music notes for search
    noteset = [item[0].upper() + item[1:] for item in args.noteset]

    results = db.fetchSongsWithNoteSet(noteset)
    print(json.dumps(results, separators=(',', ':')))
