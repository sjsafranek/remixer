from .analyze_wav import *


def pipeline_wav(filename):
    beats = get_file_beats(filename)
    for i, beat in enumerate(beats):
        if i == 0:
            continue
        yield get_notes_and_chord(filename, beats[i - 1], beat)


# for data in pipeline_wav("metallica.wav"):
#    print(data)
