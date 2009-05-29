import os
import struct
import logging

from primitives import *
from constants import *
from astypes import MalformedFLV
from astypes import get_script_data_variable, make_script_data_variable

log = logging.getLogger('flvlib.tags')

STRICT_PARSING = False
def strict_parser():
    return globals()['STRICT_PARSING']


class EndOfTags(Exception):
    pass


def ensure(value, expected, error_msg):
    if value == expected:
        return

    if strict_parser():
        raise MalformedFLV(error_msg)
    else:
        log.warning('Skipping non-conformant value in FLV file')


class Tag(object):

    def __init__(self, parent_flv, f):
        self.f = f
        self.parent_flv = parent_flv
        self.offset = None
        self.size = None
        self.timestamp = None
        self.data_start = None

    def parse(self):
        f = self.f

        self.offset = f.tell() - 1

        # DataSize
        self.size = get_ui24(f)
        log.debug("Data size is %d", self.size)

        # Timestamp + TimestampExtended
        self.timestamp = get_si32_extended(f)
        log.debug("Tag timestamp is %d", self.timestamp)

        if self.timestamp < 0:
            log.warning("The tag at offset 0x%08X has negative timestamp: %d",
                        self.offset, self.timestamp)

        # StreamID
        stream_id = get_ui24(f)
        ensure(stream_id, 0, "StreamID non zero: 0x%06X" % stream_id)

        # The rest gets parsed in the subclass

    def seek_past_data(self, adjust=0):
        f = self.f

        f.seek(self.size + adjust, os.SEEK_CUR)
        log.debug("%s seeked past the data of the tag", self)

        previous_tag_size = get_ui32(f)
        ensure(previous_tag_size, self.size + 11,
               "PreviousTagSize of %d (0x%08X) "
               "not equal to actual tag size of %d (0x%08X)" %
               (previous_tag_size, previous_tag_size,
                self.size + 11, self.size + 11))
        log.debug("Ready to read another tag")


class AudioTag(Tag):

    def __init__(self, parent_flv, f):
        Tag.__init__(self, parent_flv, f)
        self.sound_format = None
        self.sound_rate = None
        self.sound_size = None
        self.sound_type = None

    def parse(self):
        f = self.f
        Tag.parse(self)

        sound_flags = get_ui8(f)

        self.sound_format = (sound_flags & 0xF0) >> 4
        self.sound_rate = (sound_flags & 0xC) >> 2
        self.sound_size = (sound_flags & 0x2) >> 1
        self.sound_type = sound_flags & 0x1

        if strict_parser():
            try:
                sound_format_to_string[self.sound_format]
            except KeyError:
                raise MalformedFLV("Invalid sound format: %d",
                                   self.sound_format)
            try:
                sound_rate_to_string[self.sound_rate]
            except KeyError:
                raise MalformedFLV("Invalid sound rate: %d",
                                   self.sound_rate)
            try:
                sound_size_to_string[self.sound_size]
            except KeyError:
                raise MalformedFLV("Invalid sound size type: %d",
                                   self.sound_size)
            try:
                sound_type_to_string[self.sound_type]
            except KeyError:
                raise MalformedFLV("Invalid sound type: %d",
                                   self.sound_type)

        if self.sound_format == SOUND_FORMAT_AAC:
            # AAC always has sampling rate of 44 kHz
            ensure(self.sound_rate, SOUND_RATE_44_KHZ,
                   "AAC sound format with incorrect sound rate: %d" %
                   self.sound_rate)
            # AAC is always stereo
            ensure(self.sound_type, SOUND_TYPE_STEREO,
                   "AAC sound format with incorrect sound type: %d" %
                   self.sound_type)

        self.seek_past_data(adjust=-1)

    def __repr__(self):
        if self.offset is None:
            return "<AudioTag unparsed>"
        elif self.sound_format is None:
            return ("<AudioTag at offset 0x%08X, time %d, size %d>" %
                    (self.offset, self.timestamp, self.size))
        else:
            return ("<AudioTag at offset 0x%08X, time %d, size %d, %s>" %
                    (self.offset, self.timestamp, self.size,
                     sound_format_to_string[self.sound_format]))


class VideoTag(Tag):

    def __init__(self, parent_flv, f):
        Tag.__init__(self, parent_flv, f)
        self.frame_type = None
        self.codec_id = None

    def parse(self):
        f = self.f
        Tag.parse(self)

        video_flags = get_ui8(f)

        self.frame_type = (video_flags & 0xF0) >> 4
        self.codec_id = video_flags & 0xF

        if strict_parser():
            try:
                frame_type_to_string[self.frame_type]
            except KeyError:
                raise MalformedFLV("Invalid frame type: %d", self.frame_type)
            try:
                codec_id_to_string[self.codec_id]
            except KeyError:
                raise MalformedFLV("Invalid codec ID: %d", self.codec_id)

        self.seek_past_data(adjust=-1)

    def __repr__(self):
        if self.offset is None:
            return "<VideoTag unparsed>"
        elif self.frame_type is None:
            return ("<VideoTag at offset 0x%08X, time %d, size %d>" %
                    (self.offset, self.timestamp, self.size))
        else:
            return ("<VideoTag at offset 0x%08X, time %d, size %d, %s (%s)>" %
                    (self.offset, self.timestamp, self.size,
                     codec_id_to_string[self.codec_id],
                     frame_type_to_string[self.frame_type]))


class ScriptTag(Tag):

    def __init__(self, parent_flv, f):
        Tag.__init__(self, parent_flv, f)
        self.name = None
        self.variable = None

    def parse(self):
        f = self.f
        Tag.parse(self)

        # Here there's always a byte with the value of 0x02,
        # which means "string", although the spec says NOTHING
        # about it..
        value_type = get_ui8(f)
        ensure(value_type, 2, "The name of a script tag is not a string")

        # Need to pass the tag end offset, because apparently YouTube
        # doesn't give a *shit* about the FLV spec and just happily
        # ends the onMetaData tag after self.size bytes, instead of
        # ending it with the *required* 0x09 marker. Bastards!

        if strict_parser():
            # If we're strict, just don't pass this info
            tag_end = None
        else:
            # 11 = tag type (1) + data size (3) + timestamp (4) + stream id (3)
            tag_end = self.offset + 11 + self.size

        log.debug("max offset is 0x%08X", tag_end)

        self.name, self.variable = \
                   get_script_data_variable(f, max_offset=tag_end)
        log.debug("A script tag with a name of %s and value of %r",
                  self.name, self.variable)

        previous_tag_size = get_ui32(f)
        ensure(previous_tag_size, self.size + 11,
               "PreviousTagSize of %d (0x%08X) "
               "not equal to actual tag size of %d (0x%08X)" %
               (previous_tag_size, previous_tag_size,
                self.size + 11, self.size + 11))
        log.debug("Ready to read another tag")

    def __repr__(self):
        if self.offset is None:
            return "<ScriptTag unparsed>"
        elif not self.name:
            return ("<ScriptTag at offset 0x%08X, time %d, size %d>" %
                    (self.offset, self.timestamp, self.size))
        else:
            return ("<ScriptTag %s at offset 0x%08X, time %d, size %d>" %
                    (self.name, self.offset, self.timestamp, self.size))


tag_to_class = {
    TAG_TYPE_AUDIO: AudioTag,
    TAG_TYPE_VIDEO: VideoTag,
    TAG_TYPE_SCRIPT: ScriptTag
}


class FLV(object):

    def __init__(self, f):
        self.f = f
        self.version = None
        self.has_audio = None
        self.has_video = None
        self.tags = []

    def parse_header(self):
        f = self.f
        f.seek(0)

        # FLV header
        header = f.read(3)
        if len(header) < 3:
            raise MalformedFLV("The file is shorter than 3 bytes")

        # Do this irrelevant of STRICT_PARSING, to catch bogus files
        if header != "FLV":
            raise MalformedFLV("File signature is incorrect: 0x%X 0x%X 0x%X" %
                               struct.unpack("3B", header))

        # File version
        self.version = get_ui8(f)
        log.debug("File version is %d", self.version)

        # TypeFlags
        flags = get_ui8(f)

        ensure(flags & 0xF8, 0,
               "First TypeFlagsReserved field non zero: 0x%X" % (flags & 0xF8))
        ensure(flags & 0x2, 0,
               "Second TypeFlagsReserved field non zero: 0x%X" % (flags & 0x2))

        self.has_audio = False
        self.has_video = False
        if flags & 0x4:
            self.has_audio = True
        if flags & 0x1:
            self.has_video = True
        log.debug("File %s audio",
                  (self.has_audio and "has") or "does not have")
        log.debug("File %s video",
                  (self.has_video and "has") or "does not have")

        header_size = get_ui32(f)
        log.debug("Header size is %d bytes", header_size)

        f.seek(header_size)

        tag_0_size = get_ui32(f)
        ensure(tag_0_size, 0, "PreviousTagSize0 non zero: 0x%08X" % tag_0_size)

    def iter_tags(self):
        self.parse_header()
        try:
            while True:
                tag = self.get_next_tag()
                yield tag
        except EndOfTags:
            pass

    def read_tags(self):
        self.tags = list(self.iter_tags())

    def get_next_tag(self):
        f = self.f

        try:
            tag_type = get_ui8(f)
        except EndOfFile:
            raise EndOfTags

        tag_klass = self.tag_type_to_class(tag_type)
        tag = tag_klass(self, f)
        log.debug("Found a tag: %s", tag)

        tag.parse()

        return tag

    def tag_type_to_class(self, tag_type):
        try:
            return tag_to_class[tag_type]
        except KeyError:
            raise MalformedFLV("Invalid tag type: %d", tag_type)


def create_flv_tag(type, data, timestamp=0):
    tag_type = struct.pack("B", type)
    timestamp = make_si32_extended(timestamp)
    stream_id = make_ui24(0)

    data_size = len(data)
    tag_size = data_size + 11

    return ''.join([tag_type, make_ui24(data_size), timestamp, stream_id,
                    data, make_ui32(tag_size)])


def create_script_tag(name, data, timestamp=0):
    payload = make_ui8(2) + make_script_data_variable(name, data)
    return create_flv_tag(TAG_TYPE_SCRIPT, payload, timestamp)


def create_flv_header(has_audio=True, has_video=True):
    type_flags = 0
    if has_video:
        type_flags = type_flags | 0x1
    if has_audio:
        type_flags = type_flags | 0x4
    return ''.join(['FLV', make_ui8(1), make_ui8(type_flags), make_ui32(9),
                    make_ui32(0)])
