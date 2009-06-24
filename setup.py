#!/usr/bin/python

"""flvlib
======

A library for manipulating, parsing and verifying FLV files.

It includes two example scripts, debug-flv and index-flv,
which demonstrate the possible applications of the library.

Provides an easy and extensible way of writing applications that parse
and transforming FLV files. Checks file correctness based on the
official specification released by Adobe.

Can be used as a drop-in replacement for FLVTool2, from which it is
typically much faster. Unlike FLVTool2 it works on audio-only files and
does not overwrite any previous metadata the file might have.

Example usage
-------------

**Printing FLV file information**

::

    $ debug-flv file.flv | head -5
    === `file.flv' ===
    #00001 <AudioTag at offset 0x0000000D, time 0, size 162, MP3>
    #00002 <AudioTag at offset 0x000000BE, time 0, size 105, MP3>
    #00003 <VideoTag at offset 0x00000136, time 0, size 33903, VP6 (keyframe)>
    #00004 <AudioTag at offset 0x000085B4, time 26, size 105, MP3>


**Indexing and FLV file**

::

    $ index-flv -U file.flv
    $ debug-flv --metadata file.flv
    === `file.flv' ===
    #00001 <ScriptTag onMetaData at offset 0x0000000D, time 0, size 259>
    {'duration': 9.979000000000001,
     'keyframes': {'filepositions': [407.0], 'times': [0.0]},
     'metadatacreator': 'flvlib 0.x.x'}
"""

import os
import sys

from distutils.core import setup, Command

# Make sure we import flvlib from the current directory, not some
# version that could have been installed earlier on the system
curdir = sys.path[0]
sys.path.insert(0, os.path.join(curdir, 'lib'))

from flvlib import __versionstr__

# Revert sys.path to the previous state
sys.path = sys.path[1:]

# Don't install man pages and the README on a non-Linux system
if sys.platform == 'linux2':
    data_files = [('share/man/man1', ['man/debug-flv.1', 'man/index-flv.1'])]
else:
    data_files = []

# Define a `test' command to automatically run tests
class test(Command):
    description = "run the automated test suite"
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        from test.test_flvlib import main
        main()

setup(name="flvlib",
      version=__versionstr__,
      description="Parsing, manipulating and indexing FLV files",
      long_description=__doc__,
      classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Multimedia",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      platforms=["any"],
      license="MIT",
      author="Jan Urbanski",
      maintainer="Jan Urbanski",
      author_email="wulczer@wulczer.org",
      maintainer_email="wulczer@wulczer.org",
      url="http://wulczer.org/flvlib/",
      download_url="http://wulczer.org/flvlib/flvlib-latest.tar.bz2",
      package_dir={'': 'lib'},
      packages=["flvlib", "flvlib.scripts"],
      scripts=["scripts/debug-flv", "scripts/index-flv"],
      data_files=data_files,
      cmdclass={'test': test})
