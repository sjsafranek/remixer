import itertools
import operator
from math import log2

import numpy as np
import scipy.stats
import scipy.linalg
import mingus.core.chords as minguschords



def getChordFromNotes(notes):
    chords = {}
    for notelist in itertools.permutations(notes):
        notelist = list(notelist)
        chord = minguschords.determine(notelist, True)
        if len(chord) == 0:
            continue
        if chord[0] not in chords:
            chords[chord[0]] = 0
        chords[chord[0]] += 1
    sorted_d = sorted(chords.items(), key=operator.itemgetter(1))
    try:
        c = sorted_d[0][0]
        if c == "perfect fourth" or c == "perfect fifth":
            c = notes[0] + c
        return c
    except:
        return "".join(notes)


def getNoteFromFrequency(freq):
    A4 = 440
    C0 = A4 * pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12 * log2(freq / C0))
    n = h % 12
    return name[n]


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
