#!/usr/bin/python

from distutils.core import setup

setup(name="flvlib",
      version="0.1.0",
      description="Parsing and manipulating FLV files",
      long_description= \
"""A library for manipulating, parsing and verifying FLV files.
It also includes two example scripts, debug-flv and index-flv,
which demonstrate the possible applications of the library.
""",
      license="New BSD License",
      author="Jan Urbanski",
      author_email="wulczer@wulczer.org",
      provides="flvlib",
      package_dir={'': 'lib'},
      packages=["flvlib"],
      scripts=["scripts/debug-flv", "scripts/index-flv"])
