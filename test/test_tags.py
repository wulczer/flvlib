# -*- coding: utf-8 -*-

import unittest

import logging
import test_common
from StringIO import StringIO

from flvlib import constants, primitives, astypes, tags


class LStringIO(StringIO):
    """
    A StringIO that lies about its tell() position.

    Useful to simulate being in the middle of a file
    """

    def __init__(self, buf='', offset=0):
        self.offset = offset
        StringIO.__init__(self, buf)

    def tell(self):
        return StringIO.tell(self) + self.offset


class TestEnsure(unittest.TestCase):

    def setUp(self):
        self.old_strict = tags.STRICT_PARSING

    def tearDown(self):
        tags.STRICT_PARSING = self.old_strict

    def test_ensure_strict(self):
        tags.STRICT_PARSING = True
        self.assertRaises(tags.MalformedFLV, tags.ensure, 1, 2, "error")

    def test_ensure_nonstrict(self):
        tags.STRICT_PARSING = False
        f = test_common.WarningCounterFilter()
        logging.getLogger('flvlib.tags').addFilter(f)
        tags.ensure(1, 2, "error")
        logging.getLogger('flvlib.tags').removeFilter(f)

        self.assertEquals(f.warnings, 1)

    def test_ensure_noerror(self):
        tags.STRICT_PARSING = True
        tags.ensure(1, 1, "no error")


class TestUnderStrictParsing(unittest.TestCase):

    def setUp(self):
        self.old_strict = tags.STRICT_PARSING
        tags.STRICT_PARSING = True

    def tearDown(self):
        tags.STRICT_PARSING = self.old_strict


class BodyGeneratorMixin(object):

    # this header contains DataSize of 10 and timestamp of 9823
    tag_header = '\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x00'
    tag_footer = '\x00\x00\x00\x15'

    DATASIZE = 10

    def tag_body(self, content):
        return (self.tag_header + content +
                '\x00' * (self.DATASIZE - len(content)) + self.tag_footer)


class TestTag(TestUnderStrictParsing):

    def test_simple_parse(self):
        s = StringIO('\x00\x00\x0a\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x11' * 10 +
                     '\x00\x00\x00\x15')
        t = tags.Tag(None, s)
        t.parse()

        self.assertEquals(s.read(), '')
        # the offset should be StringIO.tell() - 1, which means -1
        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, BodyGeneratorMixin.DATASIZE)
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


class TestAudioTag(TestUnderStrictParsing, BodyGeneratorMixin):

    def test_simple_sound_flags(self):
        s = StringIO(self.tag_body('\x2d'))
        t = tags.AudioTag(None, s)
        t.parse()

        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, BodyGeneratorMixin.DATASIZE)
        self.assertEquals(t.timestamp, 9823)
        self.assertEquals(t.sound_format, constants.SOUND_FORMAT_MP3)
        self.assertEquals(t.sound_rate, constants.SOUND_RATE_44_KHZ)
        self.assertEquals(t.sound_size, constants.SOUND_SIZE_8_BIT)
        self.assertEquals(t.sound_type, constants.SOUND_TYPE_STEREO)

    def test_sound_flags_aac(self):
        s = StringIO(self.tag_body('\xaf\x01'))
        t = tags.AudioTag(None, s)
        t.parse()

        self.assertEquals(t.sound_format, constants.SOUND_FORMAT_AAC)
        self.assertEquals(t.sound_rate, constants.SOUND_RATE_44_KHZ)
        self.assertEquals(t.sound_size, constants.SOUND_SIZE_16_BIT)
        self.assertEquals(t.sound_type, constants.SOUND_TYPE_STEREO)
        self.assertEquals(t.aac_packet_type, constants.AAC_PACKET_TYPE_RAW)

    def test_errors(self):
        # wrong sound format
        t = tags.AudioTag(None, StringIO(self.tag_body('\x9f')))
        self.assertRaises(tags.MalformedFLV, t.parse)

        # wrong sound rate for AAC
        t = tags.AudioTag(None, StringIO(self.tag_body('\xa3')))
        self.assertRaises(tags.MalformedFLV, t.parse)

        # wrong sound type for AAC
        t = tags.AudioTag(None, StringIO(self.tag_body('\xa2')))
        self.assertRaises(tags.MalformedFLV, t.parse)

        # wrong packet type for AAC
        t = tags.AudioTag(None, StringIO(self.tag_body('\xaf\x03')))
        self.assertRaises(tags.MalformedFLV, t.parse)

    def test_repr(self):
        t = tags.AudioTag(None, LStringIO(self.tag_body('\xbb'), 10))
        self.assertEquals(repr(t), "<AudioTag unparsed>")

        t.parse()
        self.assertEquals(repr(t),
                          "<AudioTag at offset 0x00000009, "
                          "time 9823, size 10, Speex>")

        t = tags.AudioTag(None, LStringIO(self.tag_body('\xaf\x01'), 10))
        t.parse()
        self.assertEquals(repr(t),
                          "<AudioTag at offset 0x00000009, "
                          "time 9823, size 10, AAC, raw>")



class TestVideoTag(TestUnderStrictParsing, BodyGeneratorMixin):

    def test_simple_video_flags(self):
        s = StringIO(self.tag_body('\x22'))
        t = tags.VideoTag(None, s)
        t.parse()

        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, BodyGeneratorMixin.DATASIZE)
        self.assertEquals(t.timestamp, 9823)
        self.assertEquals(t.frame_type, constants.FRAME_TYPE_INTERFRAME)
        self.assertEquals(t.codec_id, constants.CODEC_ID_H263)

    def test_video_flags_h264(self):
        s = StringIO(self.tag_body('\x17\x01'))
        t = tags.VideoTag(None, s)
        t.parse()

        self.assertEquals(t.frame_type, constants.FRAME_TYPE_KEYFRAME)
        self.assertEquals(t.codec_id, constants.CODEC_ID_H264)
        self.assertEquals(t.h264_packet_type, constants.H264_PACKET_TYPE_NALU)

    def test_errors(self):
        # wrong frame type
        t = tags.VideoTag(None, StringIO(self.tag_body('\x01')))
        self.assertRaises(tags.MalformedFLV, t.parse)

        # wrong codec ID
        t = tags.VideoTag(None, StringIO(self.tag_body('\x18')))
        self.assertRaises(tags.MalformedFLV, t.parse)

        # wrong packet type for H.264
        t = tags.VideoTag(None, StringIO(self.tag_body('\x27\x04')))
        self.assertRaises(tags.MalformedFLV, t.parse)

    def test_repr(self):
        t = tags.VideoTag(None, LStringIO(self.tag_body('\x11'), 10))
        self.assertEquals(repr(t), "<VideoTag unparsed>")

        t.parse()
        self.assertEquals(repr(t),
                          "<VideoTag at offset 0x00000009, "
                          "time 9823, size 10, JPEG (keyframe)>")

        t = tags.VideoTag(None, LStringIO(self.tag_body('\x27\x01'), 10))
        t.parse()
        self.assertEquals(repr(t),
                          "<VideoTag at offset 0x00000009, "
                          "time 9823, size 10, H.264 (interframe), NAL unit>")


class TestScriptTag(TestUnderStrictParsing):

    def test_simple_script_tag(self):
        s = StringIO('\x00\x00\x07\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x02\x00\x03\x66\x6f\x6f\x05\x00\x00\x00\x12')
        t = tags.ScriptTag(None, s)
        t.parse()

        self.assertEquals(t.offset, -1)
        self.assertEquals(t.size, 7)
        self.assertEquals(t.timestamp, 9823)
        self.assertEquals(t.name, 'foo')
        self.assertTrue(t.variable is None)

    def test_variable_parsing(self):
        s = StringIO('\x00\x00\x28\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x02\x00\x0aonMetaData\x08\x00\x00\x00\x01' +
                     '\x00\x08duration\x00\x3f\xf0\x00\x00\x00\x00\x00\x00' +
                     '\x00\x00\x09\x00\x00\x00\x33')
        t = tags.ScriptTag(None, s)
        t.parse()

        self.assertEquals(t.name, 'onMetaData')
        self.assertEquals(t.variable, {'duration': 1.0})

        # try an ECMAArray without the marker and without strict parsing

        tags.STRICT_PARSING = False
        s = StringIO('\x00\x00\x25\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x02\x00\x0aonMetaData\x08\x00\x00\x00\x01' +
                     '\x00\x08duration\x00\x3f\xf0\x00\x00\x00\x00\x00\x00' +
                     '\x00\x00\x00\x30')
        t = tags.ScriptTag(None, s)
        t.parse()
        tags.STRICT_PARSING = True

        self.assertEquals(t.name, 'onMetaData')
        self.assertEquals(t.variable, {'duration': 1.0})

    def test_errors(self):
        # name is not a string (no 0x02 byte before the name)
        s = StringIO('\x00\x00\x07\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x03\x00\x03\x66\x6f\x6f\x05\x00\x00\x00\x12')
        t = tags.ScriptTag(None, s)
        self.assertRaises(tags.MalformedFLV, t.parse)

        # an ECMAArray without the marer, should fail under strict parsing
        s = StringIO('\x00\x00\x25\x00\x26\x5f\x00\x00\x00\x00' +
                     '\x02\x00\x0aonMetaData\x08\x00\x00\x00\x01' +
                     '\x00\x08duration\x00\x3f\xf0\x00\x00\x00\x00\x00\x00' +
                     '\x00\x00\x00\x30')
        t = tags.ScriptTag(None, s)
        self.assertRaises(primitives.EndOfFile, t.parse)

    def test_repr(self):
        s = LStringIO('\x00\x00\x07\x00\x26\x5f\x00\x00\x00\x00' +
                      '\x02\x00\x03\x66\x6f\x6f\x05\x00\x00\x00\x12', 10)
        t = tags.ScriptTag(None, s)
        self.assertEquals(repr(t), "<ScriptTag unparsed>")

        t.parse()
        self.assertEquals(repr(t),
                          "<ScriptTag foo at offset 0x00000009, "
                          "time 9823, size 7>")


class TestFLV(TestUnderStrictParsing, BodyGeneratorMixin):

    def test_simple_parse(self):
        s = StringIO('FLV\x00\x04\x00\x00\x00\x09\x00\x00\x00\x00')
        f = tags.FLV(s)
        f.parse_header()

        self.assertEquals(f.version, 0)
        self.assertEquals(f.has_audio, True)
        self.assertEquals(f.has_video, False)

    def test_parse_tags(self):
        s = StringIO('FLV\x00\x05\x00\x00\x00\x09\x00\x00\x00\x00' +
                     '\x08' + self.tag_body('\x4b') +
                     '\x08' + self.tag_body('\xbb') +
                     '\x09' + self.tag_body('\x17\x00') +
                     '\x12' + ('\x00\x00\x07\x00\x26\x5f\x00\x00\x00\x00' +
                               '\x02\x00\x03\x66\x6f\x6f\x05\x00\x00\x00\x12'))
        f = tags.FLV(s)
        f.read_tags()

        self.assertEquals(f.version, 0)
        self.assertEquals(f.has_audio, True)
        self.assertEquals(f.has_video, True)

        self.assertEquals(len(f.tags), 4)
        self.assertTrue(isinstance(f.tags[0], tags.AudioTag))
        self.assertTrue(isinstance(f.tags[1], tags.AudioTag))
        self.assertTrue(isinstance(f.tags[2], tags.VideoTag))
        self.assertTrue(isinstance(f.tags[3], tags.ScriptTag))

    def test_errors(self):
        # file shorter than 3 bytes
        s = StringIO()
        f = tags.FLV(s)
        self.assertRaises(tags.MalformedFLV, f.read_tags)

        # header invalid
        s = StringIO('XLV\x00\x04\x00\x00\x00\x09\x00\x00\x00\x00')
        f = tags.FLV(s)
        self.assertRaises(tags.MalformedFLV, f.read_tags)

        # invalid tag type
        s = StringIO('FLV\x00\x05\x00\x00\x00\x09\x00\x00\x00\x00' +
                     '\x01' + self.tag_body('\x4b'))
        f = tags.FLV(s)
        self.assertRaises(tags.MalformedFLV, f.read_tags)


class TestCreateTags(TestUnderStrictParsing):

    def test_create_flv_tag(self):
        s = tags.create_flv_tag(0x08, 'random-garbage', 1234)

        self.assertEquals(s, ('\x08\x00\x00\x0e\x00\x04\xd2\x00\x00\x00\x00' +
                              'random-garbage\x00\x00\x00\x19'))

    def test_create_script_tag(self):
        s = tags.create_script_tag('onMetaData', {'silly': True})

        self.assertEquals(s, ('\x12\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00' +
                              '\x02\x00\x0aonMetaData\x08\x00\x00\x00\x01' +
                              '\x00\x05silly\x01\x01\x00\x00\x09' +
                              '\x00\x00\x00\x29'))

    def test_create_flv_header(self):
        data = (((True, True), 'FLV\x01\x05\x00\x00\x00\t\x00\x00\x00\x00'),
                ((True, False), 'FLV\x01\x04\x00\x00\x00\t\x00\x00\x00\x00'),
                ((False, True), 'FLV\x01\x01\x00\x00\x00\t\x00\x00\x00\x00'),
                ((False, False), 'FLV\x01\x00\x00\x00\x00\t\x00\x00\x00\x00'))

        for has_audio_video, expected in data:
            s = tags.create_flv_header(*has_audio_video)
            self.assertEquals(s, expected)
