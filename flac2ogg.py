#!/usr/bin/env python
"""
Audio file converter.

This script automate conversion between different type of audio formats.
Conversion can be performed from the following formats:

    - FLAC
    - MP3
    - MP4
    - WAVE
    - WavePack
    - Musepack
    - Ogg Vorbis

Currently supported encoders:

    - Ogg Vorbis
    - MP3 (lame)

There is an option to set the quality for the encoders - for Ogg files there
would be used an `-q' option for `oggenc` command, and for the mp3 format,
`-V` option would be used for `lame` command. Consult corresponding man pages
for details.

Aim for this script is to produce high quality ogg files out of (preferably)
lossless formats like FLAC/WAVE/WavePack or small-sized mp3 files out of
anything. Of course there is no constraints on what source files would be and
what output format will be, so there is a possibility to create ogg form low
quality mp3 files, nevertheless it doesn't make any sense :)

license: 3-clause BSD license
version: 1.0
"""
import argparse
import multiprocessing as mp
import os
import re
import subprocess as sp
import sys

import mutagen
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3, EasyID3KeyError


def match_file(path):
    """Get all wav files from provided location"""
    matched_files = []
    re_ = re.compile(r"^.*_\d+.wav$")

    for filename in os.listdir(os.path.abspath(path)):
        if re_.match(filename):
            matched_files.append(os.path.join(path, filename))

    return sorted(matched_files)


def get_filepaths_recursively(pattern=None):
    """Gather and return files"""
    if pattern and len(pattern) == 1 and pattern[0].startswith("*"):
        pat = "." + pattern[0]
    else:
        print("Recursive option only works with simple pattern for files"
              " match")
        sys.exit(1)

    files_ = []
    for root, _, files in os.walk("."):
        for filename in files:
            if re.match(pat, filename):
                files_.append(os.path.join(root, filename))

    return files_


def encode(obj):
    """Encode files with specified command"""
    obj.encode()


class CueTrack(object):
    def __init__(self):
        """Init"""
        self.performer = None
        self.title = None


class CueObjectParser(object):
    def __init__(self, cuefile):
        """Init"""
        self.cuefile = cuefile
        self.album_artist = None
        self.album = None
        self.tracks = []
        self._parse_cue()

    def get_track_data(self, index):
        return self.tracks[index].title, self.tracks[index].performer

    def _parse_cue(self):
        """Read and parse cuefile"""
        with open(self.cuefile) as fobj:
            content = fobj.read()

        in_track = False
        track = None

        for line in content.split('\n'):
            if not in_track:
                if line.strip().upper().startswith('REM'):
                    continue

                if line.strip().upper().startswith('PERFORMER'):
                    self.album_artist = line.split('"')[1]
                    continue

                if line.strip().upper().startswith('TITLE'):
                    self.album = line.split('"')[1]
                    continue

            if 'TRACK' in line.strip().upper():
                in_track = True
                track = CueTrack()
                self.tracks.append(track)
                continue

            if in_track:
                if line.strip().upper().startswith('PERFORMER'):
                    track.performer = line.split('"')[1]
                    continue

                if line.strip().upper().startswith('TITLE'):
                    track.title = line.split('"')[1]
                    continue


class Encoder(object):
    """Encoder base class"""
    EXT = ".undefined"

    def __init__(self, quality=None):
        self.quality = quality
        self.ext = self.EXT

    def encode(self, input_fname, output_fname):
        """Encode file"""
        raise NotImplementedError()


class OggEncoder(Encoder):
    """Vorbis encoder"""
    EXT = ".ogg"

    def __init__(self, quality=None):
        """Init"""
        super(OggEncoder, self).__init__(quality)
        if self.quality is None:
            self.quality = 8

    def encode(self, input_fname, output_fname):
        sp.check_call(["oggenc", "-q%s" % self.quality, input_fname,
                       '-o', output_fname])


class Mp3Encoder(Encoder):
    """Mp3 encoder"""
    EXT = ".mp3"

    def __init__(self, quality=None):
        """Init"""
        super(Mp3Encoder, self).__init__(quality)
        if self.quality is None:
            self.quality = 6

    def encode(self, input_fname, output_fname):
        sp.check_call(["lame", "-V%s" % self.quality, input_fname,
                       output_fname])


class FileType(object):
    """Base class for file objects"""
    extensions = {'ogg': '.ogg',
                  'mp3': '.mp3'}

    def __init__(self, filename, encoder):
        self.filename = filename
        self.encoder = encoder

        self.out_fname = None

        self.base, self.ext = os.path.splitext(filename)
        self.ext = self.ext.lower()
        self.wav = self.base + ".wav"

        self.tmp_wav_remove = True

        self.album = None
        self.album_artist = None
        self.album = None
        self.title = None
        self.performer = None

    def extract_wav(self):
        """Dummy function for wav files"""
        raise NotImplementedError()

    def encode(self):
        """Encode and tag file"""
        self.out_fname = self._get_output_fn()
        self.extract_wav()
        self.encoder.encode(self.wav, self.out_fname)
        self._tag_file()
        self.cleanup()

    def cleanup(self):
        """Remove intermediate wav file"""
        if not self.tmp_wav_remove:
            return

        os.unlink(self.wav)

    def _get_output_fn(self):
        """Get unique name for the output file"""
        out = self.base

        while os.path.exists(out + self.encoder.ext):
            out = out + "_encoded_"

        return out + self.encoder.ext

    def _tag_file(self):
        """Transfer tags from source files, or from cue"""

        if self.ext == '.mp3':
            tag = MP3(self.filename, ID3=EasyID3)
        else:
            tag = mutagen.File(self.filename)


        if self.encoder == 'mp3':
            self._mp3_tag(tag)
            return

        out_tag = mutagen.File(self.out_fname)
        if self.album:
            out_tag['album'] = self.album
        if self.album_artist:
            out_tag['albumartist'] = self.album_artist
        if self.performer:
            out_tag['artist'] = self.performer
        if self.title:
            out_tag['title'] = self.title
        out_tag.save()

        try:
            out_tag.update(tag)
            out_tag.save()
        except:
            pass

    def _mp3_tag(self, tag):
        """Special case of tagging mp3 output file"""
        mp3_tag = MP3(self.out_fname, ID3=EasyID3)
        mp3_tag.add_tags(ID3=EasyID3)

        if self.album:
            mp3_tag['album'] = self.album
        if self.performer:
            mp3_tag['artist'] = self.performer
        if self.title:
            mp3_tag['title'] = self.title
        mp3_tag.save()

        for key, val in tag.items():
            try:
                if isinstance(val, list):
                    mp3_tag[key] = ", ".join(val)
                else:
                    mp3_tag[key] = val
            except EasyID3KeyError:
                pass  # ignore unknown keys

        mp3_tag.save()


class FlacType(FileType):
    """Flac filetype"""

    def extract_wav(self):
        """Call flac to extract flac file to wav"""
        sp.check_call(["flac", "-d", self.filename])


class ApeType(FileType):
    """Ape filetype"""

    def extract_wav(self):
        """Extract ape file to wav"""
        sp.check_call(["mac", self.filename, self.wav, "-d"])


class WvType(FileType):
    """Wv filetype"""

    def extract_wav(self):
        """Extract wavepack file to wav"""
        sp.check_call(["wvunpack", self.filename, "-o", self.wav])


class M4aType(FileType):
    """M4a filetype"""

    def __init__(self, filename, encoder):
        super(M4aType, self).__init__(filename, encoder)

    def extract_wav(self):
        """Extract m4a file to wav"""
        wav = self.wav
        if "," in wav:
            wav = wav.replace(",", "\\,")
        sp.check_call(["mplayer", "-vo", "none", self.filename, "-ao",
                       "pcm:file=%s" % wav])


class WavType(FileType):
    """Uncompressed wav filetype"""

    def __init__(self, filename, encoder):
        super(WavType, self).__init__(filename, encoder)
        self.wav = filename
        self.tmp_wav_remove = False

    def extract_wav(self):
        """Do nothing, we already unpacked here"""
        return


class Mp3Type(FileType):
    """Mp3 filetype"""

    def extract_wav(self):
        """Extract mp3 file to wav"""
        sp.check_call(["lame", "--decode", self.filename, self.wav])

class OggType(FileType):
    """Ogg Vorbis filetype"""

    def extract_wav(self):
        """Extract mp3 file to wav"""
        sp.check_call(["oggdec", self.filename])


class Converter(object):
    """Main class for converting files"""
    extract_map = {'.ape': ApeType,
                   '.flac': FlacType,
                   '.m4a': M4aType,
                   '.mp3': Mp3Type,
                   '.ogg': OggType,
                   '.wav': WavType,
                   '.wv': WvType}

    def __init__(self, split=False, files=tuple()):
        """Init"""
        self.files = files
        self._file_objs = []
        self.split = split

    def run(self, encoder):
        """Do the conversion"""
        self._prepare_files(encoder)
        self._encode()

    def _prepare_files(self, encoder):
        """Determine file types, and create corresponding objects"""

        for filename in self.files:
            base, ext = os.path.splitext(filename)

            if self.split:
                self._split_file(filename, base, ext, encoder)
            else:
                klass = Converter.extract_map.get(ext.lower())
                if not klass:
                    continue
                obj = klass(filename, encoder)
                self._file_objs.append(obj)

    def _split_file(self, filename, base, ext, encoder):
        """Split file using cue file information"""
        wav = base + ".wav"

        cuefile = None

        for tmp in (base + ".cue", base + ".wav.cue", base + ".flac.cue",
                    base + ".wv.cue", base + ".ape.cue"):
            if os.path.exists(tmp):
                cuefile = tmp
                print("*** cuefile: %s" % cuefile)
                break

        if cuefile is None:
            print("*** No cuefile found for `%s'" % filename)
            return

        cue = CueObjectParser(cuefile)

        # Extract file to the wav. Note, that object will not be added to the
        # list of wavs to encode
        klass = Converter.extract_map.get(ext.lower())
        if not klass:
            print("*** Cannot find right converter for `%s'" % ext)
            return

        fobj = klass(filename, encoder)
        fobj.extract_wav()

        pipe = sp.Popen(["cuebreakpoints", cuefile], stdout=sp.PIPE)
        sp.check_call(["shnsplit", "-a", base + "_", "-o", "wav", wav],
                      stdin=pipe.stdout, stdout=sp.PIPE)

        filepath = os.path.dirname(filename)
        for index, filename in enumerate(match_file(filepath)):
            obj = WavType(filename, encoder)
            obj.tmp_wav_remove = True
            obj.album = cue.album
            obj.album_artist = cue.album_artist
            obj.album = cue.album
            obj.title, obj.performer = cue.get_track_data(index)
            self._file_objs.append(obj)

        fobj.cleanup()

    def _encode(self):
        """Encode files"""
        pool = mp.Pool()
        # NOTE: map_async and get with timeout 999 are simply a hack for being
        # able to interrupt the process with ctrl+c
        pool.map_async(encode, tuple(self._file_objs)).get(999)


ENCODERS = {'ogg': OggEncoder,
            'mp3': Mp3Encoder}


def main():
    """Main"""
    arg = argparse.ArgumentParser(description='Convert between different '
                                  'audio file format.')
    arg.add_argument('-s', '--split', action='store_true',
                     help='split output file with provided *.cue file')
    arg.add_argument('-r', '--recursive', action='store_true',
                     help='do the files searching recursive')
    arg.add_argument('-e', '--encoder', default='ogg', type=str,
                     choices=('ogg', 'mp3'), help='encoder to use. Defaults '
                     'to "ogg"')
    arg.add_argument('-q', '--quality', help='Quality of the encoded file. '
                     'Consult "lame" and "oggenc" for details. Defaults are '
                     '6 for lame and 8 for oggenc.')
    arg.add_argument('files', nargs='+', help='files to encode')
    args = arg.parse_args()

    if args.recursive:
        files = get_filepaths_recursively(args.files)
    else:
        files = args.files

    conv = Converter(args.split, files)
    encoder = ENCODERS[args.encoder](args.quality)
    conv.run(encoder)

if __name__ == "__main__":
    main()
