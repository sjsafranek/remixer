
import time 
import sys

import fleep
from tinytag import TinyTag
from pydub import AudioSegment


class AudioFile(object):

    def __init__(self, filename):
        self.filename = filename

        # get file info
        with open(self.filename, "rb") as file:
            self._info = fleep.get(file.read(128))

        # file tags
        # https://pypi.org/project/tinytag/
        self._tags = TinyTag.get(self.filename)

    @property
    def tags(self):
        return self._tags

    @property
    def mimetype(self):
        return self._info.mime

    @property
    def extension(self):
        return self._info.extension

    def splice(self, ms_start, ms_end, out_filename=None, out_filehandler=None, out_format="wav"):
        """ @method: splice
            @returns splices out a wav at a current positoin
        """
        if not out_filename and not out_filehandler:
            out_filename = self.filename.replace(self.extension, out_format)

        mtype = self.mimetype
        in_format = ""

        if "audio/wav" == mtype:
            in_format = "wav"
        elif "audio/mpeg" == mtype:
            in_format = "mp3"

        audio = AudioSegment.from_file(self.filename, format = in_format)

        if out_filehandler:
            audio[ms_start:ms_end].export(out_f = out_filehandler, format = out_format)
            return True

        audio[ms_start:ms_end].export(out_filename, format = out_format)
        return True

    def convert(self, out_filename=None, out_filehandler=None, out_format="wav"):
        """ @method: convert
            @returns string or callback results
        """
        if not out_filename and not out_filehandler:
            out_filename = self.filename.replace(self.extension, out_format)

        mtype = self.mimetype
        in_format = ""

        if "audio/wav" == mtype:
            return False
        elif "audio/mpeg" == mtype:
            in_format = "mp3"

        audio = AudioSegment.from_file(self.filename, format = in_format)

        if out_filehandler:
            audio.export(out_f = out_filehandler, format = out_format)
            return True

        audio.export(out_filename, format = out_format)
        return True



if __name__ == "__main__":
    # this line adds debugging
    a = AudioFile(sys.argv[1])
    a.splice(sys.argv[2],sys.argv[3],out_filename="test.mp3",out_format="mp3")
