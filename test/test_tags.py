# -*- coding: utf-8 -*-

import unittest

import logging
import test_common
from StringIO import StringIO

from flvlib import primitives, astypes, tags


tags.STRICT_PARSING = True


class TestTag(unittest.TestCase):

    def test_simple_parse(self):
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x15')
        t = tags.Tag(None, s)
        t.parse()

        self.assertEquals(s.read(), '')
        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, 10)
        self.assertEquals(t.timestamp, 9823)

    def test_negative_timestamp(self):
        s = StringIO('\x00\x00\x0f\xcc\xff\x1b\xff\x00\x00\x00' +
                     '\x11' * 15 +
                     '\x00\x00\x00\x1a')
        t = tags.Tag(None, s)

        # This should give a warning
        f = test_common.WarningCounterFilter()
        logging.getLogger('flvlib.tags').addFilter(f)
        t.parse()
        logging.getLogger('flvlib.tags').removeFilter(f)

        self.assertEquals(f.warnings, 1)

        self.assertEquals(s.read(), '')
        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, 15)
        self.assertEquals(t.timestamp, -3342565)

    def test_zero_size_data(self):
        s = StringIO('\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0b')
        t = tags.Tag(None, s)
        t.parse()

        self.assertEquals(s.read(), '')
        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, 0)
        self.assertEquals(t.timestamp, 0)

    def test_errors(self):
        # nonzero StreamID
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x01' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x15')
        t = tags.Tag(None, s)
        self.assertRaises(astypes.MalformedFLV, t.parse)

        # PreviousTagSize too small
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x14')
        t = tags.Tag(None, s)
        self.assertRaises(astypes.MalformedFLV, t.parse)

        # PreviousTagSize too big
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x16')
        t = tags.Tag(None, s)
        self.assertRaises(astypes.MalformedFLV, t.parse)

        # DataSize too big
        s = StringIO('\x00\x00\x10\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x15')
        t = tags.Tag(None, s)
        self.assertRaises(astypes.EndOfFile, t.parse)

        # file too short
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00')
        t = tags.Tag(None, s)
        self.assertRaises(primitives.EndOfFile, t.parse)
