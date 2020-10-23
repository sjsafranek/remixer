import math
import copy
import itertools
import operator

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import find_peaks
from audiolazy.lazy_midi import freq2str
import mingus.core.chords as minguschords


def notes_to_chord(notes):
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
        return sorted_d[0][0]
    except:
        return "".join(notes)


def get_notes_and_chord(filename, start, end, plotit=False):
    fs_rate, signal = wavfile.read(filename)

    samples_start = round(fs_rate * seconds_start)
    samples_end = round(fs_rate * seconds_end)

    # convert stereo to mono
    signal = signal.mean(axis=1)

    # generate time in seconds
    t = np.arange(signal.shape[0]) / fs_rate
    ss = signal[samples_start:samples_end]

    # generate FFT and frequencies
    sp = np.fft.fft(ss)
    freq = np.fft.fftfreq(len(ss), 1 / fs_rate)
    # find first index > 2000 hz
    index2000 = next(x[0] for x in enumerate(freq) if x[1] > 2000)
    freqx = freq[:index2000]
    freqy = np.abs(sp.real[:index2000])
    peaks = []
    freqy2 = copy.copy(freqy)
    threshold = np.mean(freqy2) + 3 * np.std(freqy2)
    for i in range(8):
        mi = np.argmax(freqy2)
        if threshold < freqy2[mi] and freqx[mi] > 100:
            peaks.append(mi)
        freqy2[mi - 10 : mi + 10] = 0

    if plotit:
        # plot everything
        plt.subplot(211)
        plt.subplots_adjust(hspace=0.7)
        plt.plot(t[samples_start:samples_end], ss)
        plt.xlabel("position (s)")
        plt.ylabel("amplitude")
        plt.title("file '{}'".format(filename))
        plt.subplot(212)
        plt.plot(freqx, freqy)
        plt.plot(freqx[peaks], freqy[peaks], "o")
        plt.xlabel("frequency (hz)")
        plt.ylabel("power")
    notes = []
    final_notes = []
    for _, peak in enumerate(peaks):
        note = freq2str(freqx[peak])
        if plotit:
            plt.text(
                freqx[peak] + 50,
                freqy[peak] * 0.95,
                "{:2.1f} ({})".format(freqx[peak], note),
                fontsize=10,
            )
        note = note.split("+")[0].split("-")[0]
        final_notes.append(note)
        note = "".join([i for i in note if not i.isdigit()])
        if note not in notes:
            notes.append(note)
    final_chord = notes_to_chord(notes)
    if plotit:
        plt.title("chord guess: '{}'".format(final_chord))
        plt.show()
    return final_notes, final_chord


seconds_start = 14.14
seconds_end = 14.557
filename = "metallica.wav"
print(get_notes_and_chord(filename, seconds_start, seconds_end, plotit=True))
