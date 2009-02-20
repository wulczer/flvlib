import os
import sys
import shutil
import logging
import tempfile

from optparse import OptionParser

from flvlib import __versionstr__
from flvlib.constants import TAG_TYPE_AUDIO, TAG_TYPE_VIDEO, TAG_TYPE_SCRIPT
from flvlib.constants import FRAME_TYPE_KEYFRAME
from flvlib.astypes import MalformedFLV, FLVObject
from flvlib.tags import FLV, EndOfFile, AudioTag, VideoTag, ScriptTag
from flvlib.tags import create_script_tag, create_flv_header

log = logging.getLogger('flvlib.index-flv')


class IndexingAudioTag(AudioTag):

    def parse(self):
        AudioTag.parse(self)

        if not self.parent_flv.first_media_tag_offset:
            self.parent_flv.first_media_tag_offset = self.offset


class IndexingVideoTag(VideoTag):

    def parse(self):
        self.parent_flv.no_video = False
        VideoTag.parse(self)

        if not self.parent_flv.first_media_tag_offset:
            self.parent_flv.first_media_tag_offset = self.offset
        if self.frame_type == FRAME_TYPE_KEYFRAME:
            self.parent_flv.keyframes.filepositions.append(self.offset)
            self.parent_flv.keyframes.times.append(self.timestamp / 1000.0)


class IndexingScriptTag(ScriptTag):

    def parse(self):
        ScriptTag.parse(self)
        if self.name == 'onMetaData':
            self.parent_flv.metadata = self.variable
            self.parent_flv.metadata_tag_start = self.offset
            self.parent_flv.metadata_tag_end = self.f.tell()


tag_to_class = {
    TAG_TYPE_AUDIO: IndexingAudioTag,
    TAG_TYPE_VIDEO: IndexingVideoTag,
    TAG_TYPE_SCRIPT: IndexingScriptTag
}


class IndexingFLV(FLV):

    def __init__(self, f):
        FLV.__init__(self, f)
        self.metadata = None
        # We could provide keyframes as en ECMAscript array, but
        # gstreamer's flvdemux can't handle ECMA arrays in
        # metadata. And since we like gstreamer, we'll use the Object
        # type until gst-plugins-bad gets fixed.
        self.keyframes = FLVObject()
        self.keyframes.filepositions = []
        self.keyframes.times = []
        self.no_video = True
        self.metadata_content = None
        self.metadata_tag_start = None
        self.metadata_tag_end = None
        self.first_media_tag_offset = None

    def tag_type_to_class(self, tag_type):
        try:
            return tag_to_class[tag_type]
        except KeyError:
            raise MalformedFLV("Invalid tag type: %d", tag_type)


KEYFRAME_DENSITY = 10


def keyframes_from_audiotags(flv):
    keyframes = FLVObject()
    keyframes.filepositions = []
    keyframes.times = []
    # that's not really speeding things up, is it?
    audiotags = zip(*[(tag.offset, tag.timestamp / 1000.0)
                      for i, tag in enumerate(flv.tags)
                      if (i % KEYFRAME_DENSITY == 0 and
                          isinstance(tag, AudioTag))])
    if audiotags:
        keyframes.filepositions = list(audiotags[0])
        keyframes.times = list(audiotags[1])

    return keyframes


def duration_from_last_tag(flv):
    # if the file has no tags at all, we would have errored out
    # eariler, while checking for media content presence
    last_tag = flv.tags[-1]
    return last_tag.timestamp / 1000.0


def filepositions_difference(metadata, original_metadata_size):
    test_payload = create_script_tag('onMetaData', metadata)
    payload_size = len(test_payload)
    difference = payload_size - original_metadata_size
    return test_payload, difference


def index_file(inpath, outpath=None):
    out_text = (outpath and ("into file `%s'" % outpath)) or "in place"
    log.debug("Indexing file `%s' %s", inpath, out_text)

    try:
        f = open(inpath, 'rb')
    except IOError, (errno, strerror):
        log.error("Failed to open `%s': %s", inpath, strerror)
        return False

    flv = IndexingFLV(f)

    try:
        flv.read_tags()
    except MalformedFLV, e:
        message = e[0] % e[1:]
        log.error("The file `%s' is not a valid FLV file: %s", inpath, message)
        return False
    except EndOfFile:
        log.error("Unexpected end of file on file `%s'", inpath)
        return False

    if not flv.first_media_tag_offset:
        log.error("The file `%s' does not have any media content", inpath)
        return False

    metadata = flv.metadata or {}

    if flv.metadata_tag_start:
        original_metadata_size = flv.metadata_tag_end - flv.metadata_tag_start
    else:
        log.debug("The file `%s' has no metadata", inpath)
        original_metadata_size = 0

    keyframes = flv.keyframes

    if flv.no_video:
        log.info("The file `%s' has no video, adding fake keyframe info",
                 inpath)
        keyframes = keyframes_from_audiotags(flv)

    duration = metadata.get('duration', None)
    if not duration:
        duration = duration_from_last_tag(flv)

    metadata['duration'] = duration
    metadata['keyframes'] = keyframes
    metadata['metadatacreator'] = 'flvlib %s' % __versionstr__

    # we're going to write new metadata, so we need to shift the
    # filepositions by the amount of bytes that we're going to add to
    # the metadata tag
    test_payload, difference = filepositions_difference(metadata,
                                                        original_metadata_size)

    if difference:
        new_filepositions = [pos + difference
                             for pos in keyframes.filepositions]
        metadata['keyframes'].filepositions = new_filepositions
        payload = create_script_tag('onMetaData', metadata)
    else:
        log.debug("The file `%s' metadata size did not change.", inpath)
        payload = test_payload

    if outpath:
        try:
            fo = open(outpath, 'wb')
        except IOError, (errno, strerror):
            log.error("Failed to open `%s': %s", outpath, strerror)
            return False
    else:
        try:
            fd, temppath = tempfile.mkstemp()
            # preserve the permission bits
            shutil.copymode(inpath, temppath)
            fo = os.fdopen(fd, 'wb')
        except EnvironmentError, (errno, strerror):
            log.error("Failed to create temporary file: %s", strerror)
            return False

    log.debug("Creating the output file")

    try:
        fo.write(create_flv_header(has_audio=flv.has_audio,
                                   has_video=flv.has_video))
        fo.write(payload)
        f.seek(flv.first_media_tag_offset)
        shutil.copyfileobj(f, fo)
    except IOError, (errno, strerror):
        log.error("Failed to create the indexed file: %s", strerror)
        return False

    f.close()
    fo.close()

    if not outpath:
        # If we were not writing directly to the output file
        # we need to overwrite the original
        try:
            shutil.move(temppath, inpath)
        except EnvironmentError, (errno, strerror):
            log.error("Failed to overwrite the original file "
                      "with the indexed version: %s", strerror)
            return False

    return True


def process_options():
    usage = "%prog [-U] file [outfile|file2 file3 ...]"
    description = ("Finds keyframe timestamps and file offsets "
                   "in FLV files and updates the onMetaData "
                   "script tag with that information. "
                   "With the -U (update) option operates on all parameters, "
                   "updating the files in place. Without the -U option "
                   "accepts one input and one output file path.")
    version = "%%prog flvlib %s" % __versionstr__
    parser = OptionParser(usage=usage, description=description,
                          version=version)
    parser.add_option("-U", "--update", action="store_true",
                      help=("update mode, overwrites the given files "
                            "instead of writing to outfile"))
    parser.add_option("-v", "--verbose", action="count",
                      default=0, dest="verbosity",
                      help="be more verbose, each -v increases verbosity")
    options, args = parser.parse_args(sys.argv)

    if len(args) < 2:
        parser.error("You have to provide at least one file path")

    if not options.update and len(args) != 3:
        parser.error("You need to provide one infile and one outfile "
                     "when not using the update mode")

    if options.verbosity > 3:
        options.verbosity = 3

    log.setLevel({0: logging.ERROR, 1: logging.WARNING,
                  2: logging.INFO, 3: logging.DEBUG}[options.verbosity])

    return options, args


def index_files():
    options, args = process_options()

    clean_run = True

    if not options.update:
        clean_run = index_file(args[1], args[2])
    else:
        for filename in args[1:]:
            if not index_file(filename):
                clean_run = False

    return clean_run


def main():
    try:
        outcome = index_files()
    except KeyboardInterrupt:
        # give the right exit status, 128 + signal number
        # signal.SIGINT = 2
        sys.exit(128 + 2)
    except EnvironmentError, (errno, strerror):
        try:
            print >>sys.stderr, strerror
        except StandardError:
            pass
        sys.exit(2)

    if outcome:
        sys.exit(0)
    else:
        sys.exit(1)
