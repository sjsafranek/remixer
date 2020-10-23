import tempfile
import os
import sys
import wave
import ntpath

from numpy import *
from scipy.io import wavfile


def load_wav(filename):
    try:
        wavedata = wavfile.read(filename)
        samplerate = int(wavedata[0])
        smp = wavedata[1] * (1.0 / 32768.0)
        if len(smp.shape) > 1:  # convert to mono
            smp = (smp[:, 0] + smp[:, 1]) * 0.5
        return (samplerate, smp)
    except:
        print("Error loading wav: " + filename)
        return None


def wav_asr(filename, attack, sustain, decay):
    samplerate, smp = load_wav(filename)
    outfile = wave.open(filename, "wb")
    outfile.setsampwidth(2)
    outfile.setframerate(samplerate)
    outfile.setnchannels(1)
    x1 = attack
    x2 = attack + sustain
    x3 = attack + sustain + decay
    if x3 > float(len(smp)) / float(samplerate):
        raise ("too long!")
    for i in range(len(smp)):
        cur_time = float(i) / float(samplerate)
        if cur_time < x1:
            smp[i] = smp[i] * cur_time / attack
        elif cur_time > x2 and cur_time < x3:
            smp[i] = smp[i] * (1 - (cur_time - x2) / (decay))
        elif cur_time > x3:
            smp[i] = 0

    outfile.writeframes(int16(smp * 32767.0).tobytes())
    outfile.close()


########################################


def paulstretch(samplerate, smp, stretch, windowsize_seconds, outfilename):
    outfile = wave.open(outfilename, "wb")
    outfile.setsampwidth(2)
    outfile.setframerate(samplerate)
    outfile.setnchannels(1)

    # make sure that windowsize is even and larger than 16
    windowsize = int(windowsize_seconds * samplerate)
    if windowsize < 16:
        windowsize = 16
    windowsize = int(windowsize / 2) * 2
    half_windowsize = int(windowsize / 2)

    # correct the end of the smp
    end_size = int(samplerate * 0.05)
    if end_size < 16:
        end_size = 16
    smp[len(smp) - end_size : len(smp)] *= linspace(1, 0, end_size)

    # compute the displacement inside the input file
    start_pos = 0.0
    displace_pos = (windowsize * 0.5) / stretch

    # create Hann window
    window = (
        0.5 - cos(arange(windowsize, dtype="float") * 2.0 * pi / (windowsize - 1)) * 0.5
    )

    old_windowed_buf = zeros(windowsize)
    hinv_sqrt2 = (1 + sqrt(0.5)) * 0.5
    hinv_buf = hinv_sqrt2 - (1.0 - hinv_sqrt2) * cos(
        arange(half_windowsize, dtype="float") * 2.0 * pi / half_windowsize
    )

    while True:

        # get the windowed buffer
        istart_pos = int(floor(start_pos))
        buf = smp[istart_pos : istart_pos + windowsize]
        if len(buf) < windowsize:
            buf = append(buf, zeros(windowsize - len(buf)))
        buf = buf * window

        # get the amplitudes of the frequency components and discard the phases
        freqs = abs(fft.rfft(buf))

        # randomize the phases by multiplication with a random complex number with modulus=1
        ph = random.uniform(0, 2 * pi, len(freqs)) * 1j
        freqs = freqs * exp(ph)

        # do the inverse FFT
        buf = fft.irfft(freqs)

        # window again the output buffer
        buf *= window

        # overlap-add the output
        output = buf[0:half_windowsize] + old_windowed_buf[half_windowsize:windowsize]
        old_windowed_buf = buf

        # remove the resulted amplitude modulation
        output *= hinv_buf

        # clamp the values to -1..1
        output[output > 1.0] = 1.0
        output[output < -1.0] = -1.0

        # write the output to wav file
        outfile.writeframes(int16(output * 32767.0).tobytes())

        start_pos += displace_pos
        if start_pos >= len(smp):
            break

    outfile.close()


########################################


def stretch_wav(wavname, target_seconds):
    filename = ntpath.basename(wavname)
    (samplerate, smp) = load_wav(wavname)
    current_seconds = float(len(smp))/float(samplerate)
    tmpfile = os.path.join(
        tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()) + ".wav"
    )
    print(tmpfile)
    paulstretch(samplerate, smp, target_seconds / current_seconds * 4, 0.15, tmpfile)
    wi = wave.open(tmpfile, "rb")
    wave_channels = wi.getnchannels()
    wave_samplewidth = wi.getsampwidth()
    wave_framerate = wi.getframerate()
    wave_nframes = wi.getnframes()
    wavname_extended = wavname + "-{:1.3f}.wav".format(target_seconds)
    wo = wave.open(wavname_extended, "wb")
    wo.setnchannels(wave_channels)
    wo.setsampwidth(wave_samplewidth)
    wo.setframerate(wave_framerate)
    wo.setnframes(int(wave_framerate * target_seconds))
    wi.setpos(2429)
    wo.writeframes(wi.readframes(int(wave_framerate * target_seconds)))
    wo.close()
    wi.close()
    os.remove(tmpfile)
    return wavname_extended


# f1 = wav_extend("chords/1727/Dm/0.1509_4_0.wav", 0.875/4*1.454*2)
# # # wav_asr(f1,0.1,1.8,0.1)
# f2 = wav_extend("chords/1727/Am/0.1625_4_0.wav", 1.125/4*1.454*2)
# # # wav_asr(f2,0.1,1.8,0.1)
# f3 = wav_extend("chords/1727/FM/0.2206_5_0.wav", 1.25/4*1.454*2)
# # # wav_asr(f3,0.1,1.8,0.1)
# f4 = wav_extend("chords/1727/DFA#/0.0813_4_0.wav", 0.75/4*1.454*2)
# # # wav_asr(f3,0.1,1.8,0.1)


# infiles = [f3,f4]
# outfile = "sounds.wav"

# data = []
# for infile in infiles:
#     w = wave.open(infile, "rb")
#     data.append([w.getparams(), w.readframes(w.getnframes())])
#     w.close()

# output = wave.open(outfile, "wb")
# output.setparams(data[0][0])
# for i in range(len(data)):
#     output.writeframes(data[i][1])
# output.close()
