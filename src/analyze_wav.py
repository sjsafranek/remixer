import io
import sys
import copy
import operator
import json
import time
from math import pow

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from audiolazy.lazy_midi import freq2str
from loguru import logger
from pydub import AudioSegment
from pygame import mixer

logger.remove()

try:
    from aubio import source, tempo
except:
    pass

from .music import getNoteFromFrequency
from .music import getChordFromNotes



class AudioAnalyzer(object):

    def __init__(self, filename):
        self._filename = filename
        fs_rate, signal = wavfile.read(filename)
        self._audio_segment = AudioSegment.from_wav(filename)
        self._fs_rate = fs_rate
        self._signal = signal

    @property
    def filename(self):
        return self._filename

    @property
    def fs_rate(self):
        return self._fs_rate

    @property
    def signal(self):
        return self._signal

    def getSnippet(self, ms_start, ms_end):
        return self._audio_segment[ms_start:ms_end]

    def getSnippetBytes(self, ms_start, ms_end, format="mp3"):
        clip = self.getSnippet(ms_start, ms_end)
        clipBytes = io.BytesIO()
        clip.export(out_f=clipBytes, format=format)
        return clipBytes

    def playSnippet(self, ms_start, ms_end):
        clipBytes = self.getSnippetBytes(ms_start, ms_end)
        mixer.init()
        mixer.music.load(clipBytes)
        mixer.music.play()

    def getBeatsWithNotes(self):
        beats = self.getBeats()
        for i, beat in enumerate(beats):
            if i == 0:
                continue
            yield self.getNotesForBeat(beats[i - 1], beat)

    def getBeats(self, params=None):
        """Calculate the beats per minute (bpm) of a given file.
        param: dictionary of parameters
        """
        if params is None:
            params = {}

        samplerate, win_s, hop_s = self.fs_rate, 1024, 512
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

        s = source(self.filename, samplerate, hop_s)
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
            total_frames += read
            if read < hop_s:
                break

        return beats

    def getNotesForBeat(self, seconds_start, seconds_end, plotit=False):

        samples_start = round(self.fs_rate * seconds_start)
        samples_end = round(self.fs_rate * seconds_end)

        # convert stereo to mono
        tic = time.process_time()
        try:
            # signal = signal.mean(axis=1) # THIS IS SLOW!
            signal = (
                self.signal[samples_start:samples_end, 0] + self.signal[samples_start:samples_end, 1]
            ) / 2
        except:
            pass
        logger.debug("converted tomono in {:2.1f} ms", 1000 * (time.process_time() - tic))

        # generate time in seconds
        t = np.arange(signal.shape[0]) / self.fs_rate
        ss = signal

        # generate FFT and frequencies
        tic = time.process_time()
        sp = np.fft.fft(ss)
        freq = np.fft.fftfreq(len(ss), 1 / self.fs_rate)
        logger.debug("fft in {:2.1f} ms", 1000 * (time.process_time() - tic))
        # find first index > 2000 hz
        index2000 = next(x[0] for x in enumerate(freq) if x[1] > 2000)
        freqx = freq[:index2000]
        freqy = np.abs(sp.real[:index2000])
        peaks = []
        freqy2 = copy.copy(freqy)
        threshold = np.mean(freqy2) + 3 * np.std(freqy2)
        for i in range(8):
            mi = np.argmax(freqy2)
            if threshold < freqy2[mi] and freqx[mi] > 80 and mi not in peaks:
                peaks.append(mi)
            freqy2[mi - 15 : mi + 15] = 0

        if plotit:
            # plot everything
            plt.subplot(211)
            plt.subplots_adjust(hspace=0.7)
            plt.plot(t, ss)
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
        final_powers = []
        final_confidence = 0
        max_power = 0
        for _, peak in enumerate(peaks):
            note = freq2str(freqx[peak])
            noteoffset = note.split("%")[0]
            if "+" in noteoffset:
                noteoffset = float(noteoffset.split("+")[1])
            elif "-" in noteoffset:
                noteoffset = -1 * float(noteoffset.split("-")[1])
            else:
                continue
            if abs(noteoffset) > 15:
                continue
            if plotit:
                plt.text(
                    freqx[peak] + 50,
                    freqy[peak] * 0.95,
                    note,
                    fontsize=8,
                )
            if max_power == 0:
                max_power = freqy[peak]
            note = note.split("+")[0].split("-")[0]
            if note in final_notes:
                continue
            final_notes.append(note)
            final_freqs.append(freqx[peak])
            final_powers.append(int(100 * freqy[peak] / max_power))
            logger.trace("note: {}, freq: {}, amp: {}", note, freqx[peak], freqy[peak])
            note = "".join([i for i in note if not i.isdigit()])
            if note not in notes:
                notes.append(note)
        logger.debug("final notes: {}", final_notes)
        logger.debug("final notes: {}", final_notes)
        logger.debug("final powers: {}", final_powers)
        noteset = {}
        for i, f in enumerate(final_freqs):
            notename = getNoteFromFrequency(f)
            if notename not in noteset:
                noteset[notename] = 0
            noteset[notename] += final_powers[i]
        noteset_sum = 0
        for k in noteset:
            if noteset[k] > noteset_sum:
                noteset_sum = noteset[k]
        for k in noteset:
            noteset[k] = int(100 * noteset[k] / noteset_sum)
        final_noteset = []
        final_noteset_power = []
        notes_for_chord = []
        for a in sorted(noteset.items(), key=operator.itemgetter(1), reverse=True):
            final_noteset.append(a[0])
            final_noteset_power.append(a[1])
            if a[1] > 35:
                notes_for_chord.append(a[0])
        logger.debug("final_noteset: {}", final_noteset)
        logger.debug("final_noteset_power: {}", final_noteset_power)
        final_chord = getChordFromNotes(notes_for_chord)
        if plotit:
            plt.title("chord guess: '{}'".format(final_chord))
            plt.show()

        data = {
            "start": seconds_start,
            "end": seconds_end,
            "notes": [],
            "noteset": [],
        }
        for i, _ in enumerate(final_freqs):
            data["notes"].append(
                {
                    "note": final_notes[i],
                    "frequency": final_freqs[i],
                    "power": final_powers[i],
                }
            )
        for i, _ in enumerate(final_noteset):
            data["noteset"].append(
                {"note": final_noteset[i], "power": final_noteset_power[i]}
            )
        return data




if __name__ == "__main__":
    # this line adds debugging
    debugging = True
    if debugging:
        logger.add(
            sys.stderr,
            format="<blue>{level}</blue> {function}:{line} {message}",
            level="TRACE",
        )
    tic = time.process_time()
    print(
        json.dumps(
            get_notes_and_chord(
                sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), plotit=True
            ),
            indent=2,
        )
    )
    logger.debug("ran in {:2.1f} ms", 1000 * (time.process_time() - tic))
