#!/usr/bin/python

import os
import sys

from distutils.core import setup

# Make sure we import flvlib from the current build directory
curdir = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.insert(0, os.path.join(curdir, 'lib'))

from flvlib import __versionstr__

# Revert sys.path to the previous state
sys.path = sys.path[1:]

# Don't install man pages and the README on a non-Linux system
if sys.platform == 'linux2':
    data_files = [('share/man/man1', ['man/debug-flv.1', 'man/index-flv.1']),
                  ('share/doc/flvlib-%s' % __versionstr__,
                   ['README'])]
else:
    data_files = []

setup(name="flvlib",
      version=__versionstr__,
      description="Parsing and manipulating FLV files",
      long_description= \
"""A library for manipulating, parsing and verifying FLV files.
It also includes two example scripts, debug-flv and index-flv,
which demonstrate the possible applications of the library.
""",
      license="MIT",
      author="Jan Urbanski",
      author_email="wulczer@wulczer.org",
      url="http://wulczer.org/flvlib/",
      provides="flvlib",
      package_dir={'': 'lib'},
      packages=["flvlib", "flvlib.scripts"],
      scripts=["scripts/debug-flv", "scripts/index-flv"],
      data_files=data_files)
