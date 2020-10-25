import argparse


def getArgumentParser():
    """ @method: getArgumentParser
        @description returns command line parser containing base args
        @returns argparse.ArgumentParser {Object}
    """
    parser = argparse.ArgumentParser(description="Command line client for PyRemixer")
    parser.add_argument("-dbhost", default="127.0.0.1", type=str, help="database host")
    parser.add_argument("-dbport", default=5432, type=int, help="database post")
    parser.add_argument("-dbname", default="remixerdb", type=str, help="database name")
    parser.add_argument("-dbuser", default="postgres", type=str, help="database user")
    parser.add_argument("-dbpass", default="dev", type=str, help="database password")
    return parser
