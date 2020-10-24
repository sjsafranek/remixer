import math
import copy
import itertools
import operator
from math import log2, pow

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import find_peaks
from audiolazy.lazy_midi import freq2str
import mingus.core.chords as minguschords
from aubio import source, tempo

def freq_to_note(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    n = h % 12
    return name[n]

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
        c = sorted_d[0][0]
        if c == "perfect fourth" or c == "perfect fifth":
            c = notes[0] + c
        return c
    except:
        return "".join(notes)


def get_notes_and_chord(filename, seconds_start, seconds_end, plotit=False):
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
    final_freqs = []
    final_confidence = 0
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
        final_freqs.append(freqx[peak])
        note = "".join([i for i in note if not i.isdigit()])
        if note not in notes:
            notes.append(note)
    freqs = copy.copy(final_freqs)
    freqs.sort()
    final_noteset = []
    for f in freqs:
        notename = freq_to_note(f)
        if notename not in final_noteset:
            final_noteset.append(notename)
    final_chord = notes_to_chord(final_noteset)
    
    if plotit:
        plt.title("chord guess: '{}'".format(final_chord))
        plt.show()
    return final_freqs, final_notes, final_noteset, final_chord, final_confidence


# seconds_start = 14.14
# seconds_end = 14.557
# filename = "metallica.wav"
# print(get_notes_and_chord(filename, seconds_start, seconds_end, plotit=True))


def get_file_beats(path, params=None):
    """ Calculate the beats per minute (bpm) of a given file.
        path: path to the file
        param: dictionary of parameters
    """
    if params is None:
        params = {}
    # default:
    fs_rate, _ = wavfile.read(path)
    samplerate, win_s, hop_s = fs_rate, 1024, 512
    if "mode" in params:
        if params.mode in ["super-fast"]:
            # super fast
            samplerate, win_s, hop_s = 4000, 128, 64
        elif params.mode in ["fast"]:
            # fast
            samplerate, win_s, hop_s = 8000, 512, 128
        elif params.mode in ["default"]:
            pass
        else:
            raise ValueError("unknown mode {:s}".format(params.mode))
    # manual settings
    if "samplerate" in params:
        samplerate = params.samplerate
    if "win_s" in params:
        win_s = params.win_s
    if "hop_s" in params:
        hop_s = params.hop_s

    s = source(path, samplerate, hop_s)
    samplerate = s.samplerate
    o = tempo("specdiff", win_s, hop_s, samplerate)
    # List of beats, in samples
    beats = []
    # Total number of frames read
    total_frames = 0

    while True:
        samples, read = s()
        is_beat = o(samples)
        if is_beat:
            this_beat = o.get_last_s()
            beats.append(this_beat)
            # if o.get_confidence() > .2 and len(beats) > 2.:
            #    break
        total_frames += read
        if read < hop_s:
            break

    return beats
