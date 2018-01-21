#!/usr/bin/env python

import os
import sys
import re
from argparse import ArgumentParser
from subprocess import Popen, PIPE, check_call
from mutagen import File


def match_file(path, pattern):
    matched_files = []
    re_ = re.compile(r"^.*_\d+.wav$")

    for filename in os.listdir(os.path.abspath(path)):
        if re_.match(filename):
            matched_files.append(os.path.join(path, filename))

    return sorted(matched_files)


def extract_flac(filename, wav):
    check_call(["flac", "-d", filename])


def extract_ape(filename, wav):
    check_call(["mac", filename, wav, "-d"])


def extract_wv(filename, wav):
    check_call(["wvunpack", filename, "-o", wav])


def extract_wav(filename, wav):
    """dummy extract method"""
    return


def extract_m4a(filename, wav):
    if "," in wav:
        wav = wav.replace(",", "\\,")

    check_call(["mplayer", "-vo", "none", filename, "-ao",
                "pcm:file=%s" % wav])


def run(split, files=None):
    for filename in files:
        base, ext = os.path.splitext(filename)
        wav = base + ".wav"

        extract_map = {'.flac': extract_flac,
                       '.ape': extract_ape,
                       '.wv': extract_wv,
                       '.wav': extract_wav,
                       '.m4a': extract_m4a}

        if ext.lower() not in extract_map:
            continue

        extract_map[ext.lower()](filename, wav)

        if split:
            cuefile = None
            for tmp in (base + ".cue", base + ".wav.cue",
                            base + ".flac.cue", base + ".wv.cue",
                            base + ".ape.cue"):
                if os.path.exists(tmp):
                    cuefile = tmp
                    print "*** cuefile: %s" % cuefile
                    break

            if cuefile is None:
                print "*** no cuefile found"
                continue

            pipe = Popen(["cuebreakpoints", cuefile], stdout=PIPE)
            check_call(["shnsplit", "-a", base + "_", "-o", "wav", wav],
                       stdin=pipe.stdout, stdout=PIPE)

            for fn in match_file(os.path.dirname(filename), "_*wav"):
                check_call(["oggenc", "-q8", fn])
                os.unlink(fn)
        else:
            tag = File(filename)
            check_call(["oggenc", "-q8", wav])
            ogg_tag = File(base + ".ogg")
            try:
                ogg_tag.update(tag)
                ogg_tag.save()
            except:
                pass

        os.unlink(wav)


def do_walk(split, files=None):
    if files and len(files) == 1 and files[0].startswith("*"):
        pat = "." + files[0]
    else:
        print "Recursive option only works with simple pattern for files match"
        sys.exit(1)

    for root, dirs, files in os.walk("."):
        files_ = []
        for f in files:
            if re.match(pat, f):
                files_.append(os.path.join(root, f))

        if files_:
            run(split, files_)

if __name__ == "__main__":
    arg = ArgumentParser(description='Merge MH mail directories')
    arg.add_argument("-s", action='store_true',
                     help='split output file with provided *.cue file')
    arg.add_argument("-r", action='store_true',
                     help='do the files searchng recursive')
    arg.add_argument("files", nargs="+", help="files to encode")
    args = arg.parse_args()

    if args.r:
        do_walk(args.s, args.files)
    else:
        run(args.s, args.files)
