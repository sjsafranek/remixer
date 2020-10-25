import numpy as np
import scipy.stats
import scipy.linalg


def getKeyFromNotes(notes):
    """ @method getKeyFromNotes
        @description takes a list of music notes and
            determines the key.
        @params notes []string
    """
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    X = np.array([0] * len(name))

    for _, note in enumerate(notes):
        X[name.index(note)] += 1

    # https://gist.github.com/bmcfee/1f66825cef2eb34c839b42dddbad49fd
    X = scipy.stats.zscore(X)

    # Coefficients from Kumhansl and Schmuckler
    # as reported here: http://rnhart.net/articles/key-finding/
    major = np.asarray(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )

    major = scipy.stats.zscore(major)
    major = scipy.linalg.circulant(major)
    major = major.T.dot(X)

    minor = np.asarray(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )
    minor = scipy.stats.zscore(minor)
    minor = scipy.linalg.circulant(minor)
    minor = minor.T.dot(X)

    return name[np.argmax(minor)]
