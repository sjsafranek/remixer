from analyze_wav import *


def pipeline_wav(filename):
    beats = get_file_beats(filename)
    for i, beat in enumerate(beats):
        if i == 0:
            continue
        data = {"start": beats[i - 1], "end": beat}
        (
            data["freqs"],
            data["notes"],
            data["chord"],
            data["confidence"],
        ) = get_notes_and_chord(filename, data["start"], data["end"])
        yield data


#for data in pipeline_wav("metallica.wav"):
#    print(data)
