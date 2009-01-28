#!/usr/bin/python

import os
import sys

from distutils.core import setup

# Make sure we import flvlib from the current build directory
sys.path.insert(0, os.path.join(sys.path[0], 'lib'))

from flvlib import __versionstr__

# Revert sys.path to the previous state
sys.path = sys.path[1:]


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
      packages=["flvlib"],
      scripts=["scripts/debug-flv", "scripts/index-flv"])
