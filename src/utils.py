import fleep
import tempfile
from tinytag import TinyTag
from pydub import AudioSegment


def getAudioMineType(filename):
    """ @method: getAudioMineType
        @description Detects and returns audio file mime-type
        @argument filename {string,required}
        @returns string
    """
    with open(filename, "rb") as file:
        info = fleep.get(file.read(128))
    return info.mime


def convertAudioToWav(filename, callback=None):
    """ @method: convertAudioToWav
        @description Converts audio file to wav if needed. Returns
            filename of the converted file.
        @argument filename {string,required}
        @argument callback {function,optional} If callback function is supplied,
            a tempfile will be created and used for file conversion.
        @returns string or callback results
    """
    mtype = getAudioMineType(filename)
    fformat = ""

    if "audio/wav" == mtype:
        # No need to convert file
        if callback:
            return callback(filename)
        return filename
    elif "audio/mpeg" == mtype:
        fformat = "mp3"

    audio = AudioSegment.from_file(filename, format=fformat)

    if callback:
        with tempfile.NamedTemporaryFile(mode="wb") as fileHandler:
            audio.export(out_f=fileHandler, format="wav")
            return callback(fileHandler.name)

    audio.export("tmp.wav", format="wav")
    return "tmp.wav"


def getAudioTags(filename):
    """ https://pypi.org/project/tinytag/ """
    return TinyTag.get(filename)
