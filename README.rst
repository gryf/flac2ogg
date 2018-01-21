flac2ogg
========

Flac2ogg is an automated Audio file converter.

At the beginning, aim of ``flac2ogg`` was to produce high quality *ogg* files
out of (preferably) lossless formats like *FLAC*/*WAVE*/*WavePack*. Over time
it evolved of ability to produce small-sized *mp3* files out of anything.

Of course there is no constraints on what source files would be and what output
format will be, so there is a possibility to create *ogg* form low quality
*mp3* files, nevertheless it doesn't make any sense :) This script automate
conversion between different type of audio formats.

Requirements
============

- python in version 2.7 or 3
- `mutagen`_ python library for tag read/write
- `vorbis tools`_ for ``ogg`` files encode/decode
- `lame`_ for ``mp3`` files encode/decode
- `flac`_ for ``flac`` files decode
- `mac`_ for ``Monkey audio codecs``/``ape`` files decode
- `wavpack`_ for ``wavpack`` files decode
- `mplayer`_ for ``m4a`` files decode
- `shntool`_ and `cuetools`_ for splitting monolithic CD dump files

Supported formats
=================

Conversion can be performed from the following formats:

- FLAC
- MP3
- MP4
- WAVE
- WavePack
- Ape
- Ogg Vorbis

Currently supported encoders:

- Ogg Vorbis
- MP3 (lame)

There is an option to set the quality for the encoders - for *Ogg* files there
would be used an ``-q`` option for ``oggenc`` command, and for the *mp3*
format, ``-V`` option would be used for ``lame`` command. Consult corresponding
man pages for details.

Usage
=====

Given that there are couple of music files, simplest usage is as follows:

.. code:: shell-session

   $ flac2ogg.py directory_of_music_files/*

All files from that directory will be encoded to *ogg* by defaults. If there
are already some *ogg* files, new files would have ``_encoded_`` added into the
filename. Note, that output files will be placed next to the original files.

License
=======

This work is licensed on 3-clause BSD license. See LICENSE file for details.


.. _mutagen: https://mutagen.readthedocs.io/en/latest/
.. _vorbis tools: http://www.vorbis.com/
.. _flac: http://www.vorbis.com/
.. _lame: http://lame.sourceforge.net/
.. _mac: http://www.deb-multimedia.org/dists/testing/main/binary-amd64/package/monkeys-audio.php
.. _wavpack: http://www.wavpack.com/
.. _mplayer: http://www.mplayerhq.hu/
.. _cuetools: https://github.com/svend/cuetools
.. _shntool: http://www.etree.org/shnutils/shntool/
