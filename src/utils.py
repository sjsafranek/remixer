import fleep
import tempfile
from pydub import AudioSegment


def getAudioMineType(filename):
    """ @method: getAudioMineType
        @description Detects and returns audio file mime-type
        @argument filename {string}
        @returns string
    """
    with open(filename, "rb") as file:
        info = fleep.get(file.read(128))
    return info.mime


def convertAudioToWav(filename, callback=None):
    """ @method: convertAudioToWav
        @description Converts audio file to wav if needed. Returns
            filename of the converted file.
        @argument filename {string}
        @argument callback {function} If callback function is supplied,
            a tempfile will be created and used for file conversion.
        @returns string
    """
    mtype = getAudioMineType(filename)
    fformat = ""

    if "audio/wav" == mtype:
        # No need to convert file
        return filename
    elif "audio/mpeg" == mtype:
        fformat = "mp3"

    audio = AudioSegment.from_file(filename, format=fformat)

    if callback:
        with tempfile.NamedTemporaryFile(mode="wb") as fileHandler:
            audio.export(out_f=fileHandler, format="wav")
            callback(fileHandler.name)
            return

    audio.export("tmp.wav", format="wav")
    return "tmp.wav"
