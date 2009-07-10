# -*- coding: utf-8 -*-

from StringIO import StringIO
from datetime import datetime, timedelta, tzinfo
from test_common import SerializerTester

from flvlib import constants, primitives, astypes


class FakeTZInfo(tzinfo):
    def __init__(self, m):
        self.m = m
    def utcoffset(self, dt):
        return timedelta(minutes=self.m)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "Fake Timezone"


class ScriptDataValueSerializerTester(SerializerTester):

    def run_tests(self):
        SerializerTester.run_tests(self)

        getter, maker = (getattr(self.module, 'get_' + self.name),
                         getattr(self.module, 'make_' + self.name))
        value_type = getattr(constants, 'VALUE_TYPE_' + self.name.upper())

        for value in self.equivalence_tests:
            self.script_data_value_equivalent(value, getter, maker, value_type)

    def script_data_value_equivalent(self, val, getter, maker, value_type):
        s = StringIO(primitives.make_ui8(value_type) + maker(val))
        self.assertEquals(astypes.make_script_data_value(val), s.getvalue())
        self.assertEquals(val, astypes.get_script_data_value(s))
        self.assertEquals(s.read(), '')


class TestASTypes(ScriptDataValueSerializerTester):

    def setUp(self):
        ScriptDataValueSerializerTester.setUp(self)
        self.module = astypes

    def test_number(self):
        self.set_name('number')
        self.add_get_test('\x40\x97\xfa\x9d\xb2\x2d\x0e\x56', 1534.654)
        self.add_make_test(-4.32, '\xc0\x11\x47\xae\x14\x7a\xe1\x48')
        self.add_equivalence_test(-45.34)
        self.add_equivalence_test(0)
        self.run_tests()

    def test_boolean(self):
        self.set_name('boolean')
        self.add_get_test('\x05', True)
        self.add_get_test('\x00', False)
        self.add_make_test(False, '\x00')
        self.add_equivalence_test(True)
        self.add_equivalence_test(False)
        self.run_tests()

    def test_string(self):
        self.set_name('string')
        self.add_get_test('\x00\x0btest string', 'test string')
        self.add_get_test('\x00\x1azażółć gęślą jaźń', 'zażółć gęślą jaźń')
        self.add_make_test('zażółć gęślą jaźń', '\x00\x1azażółć gęślą jaźń')
        # the resulting string should be UTF-8 encoded, just like this file
        self.add_make_test(u'λ', '\x00\x02λ')
        self.add_equivalence_test('astring')
        # A random blob should also work
        self.add_equivalence_test('\x45\x2d\x6e\x55\x00\x23\x50')
        self.add_equivalence_test('')
        self.run_tests()

    def test_longstring(self):
        self.set_name('longstring')
        self.add_get_test('\x00\x00\x00\x0btest string', 'test string')
        self.add_get_test('\x00\x00\x00\x1azażółć gęślą jaźń', 'zażółć gęślą jaźń')
        self.add_make_test('zażółć gęślą jaźń', '\x00\x00\x00\x1azażółć gęślą jaźń')
        # the resulting string should be UTF-8 encoded, just like this file
        self.add_make_test(u'λ', '\x00\x00\x00\x02λ')
        # A random blob should also work
        self.add_make_test('\x45\x2d\x6e\x55\x00\x23\x50', '\x00\x00\x00\x07\x45\x2d\x6e\x55\x00\x23\x50')
        self.add_make_test('', '\x00\x00\x00\x00')
        self.run_tests()

        # Longstrings are not getter/maker equivalent, because *all*
        # strings are serialized as normal strings, not longstrings.
        # So to test proper deserialization from script_data_values we
        # need to do it manually.
        val = 'a test longstring'
        # serialize, should get a string
        self.assertEquals(astypes.make_script_data_value(val),
                          primitives.make_ui8(constants.VALUE_TYPE_STRING)
                          + '\x00\x11a test longstring')
        # deserialize a longstring
        s = StringIO(primitives.make_ui8(constants.VALUE_TYPE_LONGSTRING)
                     + astypes.make_longstring(val))
        self.assertEquals(val, astypes.get_script_data_value(s))
        self.assertEquals(s.read(), '')


    def test_ecma_array(self):
        self.set_name('ecma_array')
        self.add_get_test('\x00\x00\x00\x01\x00\x08test key\x00\x3f\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x09', {'test key': 1})
        # try a wrong approximate array size, should be parsed anyway
        self.add_get_test('\x00\x00\x00\x04\x00\x00\x01\x00\x00\x01 \x00\x40\x08\x00\x00\x00\x00\x00\x00\x00\x03goo\x02\x00\x02λ\x00\x00\x09', {'': False, ' ': 3, 'goo': u'λ'.encode('utf-8')})
        self.add_make_test({'key': 'val'}, '\x00\x00\x00\x01\x00\x03key\x02\x00\x03val\x00\x00\x09')

        d = astypes.ECMAArray()
        for key, val in (('key', 7.4), ('w00t', 'w00t'), ('blargh!', u'λ')):
            d[key] = val
        self.add_make_test(d, '\x00\x00\x00\x03\x00\x03key\x00\x40\x1d\x99\x99\x99\x99\x99\x9a\x00\x04w00t\x02\x00\x04w00t\x00\x07blargh!\x02\x00\x02\xce\xbb\x00\x00\x09')

        self.add_equivalence_test({'a': 4, 'b': 6})
        self.add_equivalence_test({})
        self.add_equivalence_test({'a': 4, 'b': {'g': 6.3, 'j': [1, 2, 'a', 3]}})
        self.run_tests()

        # Various corner cases:

        # try using the max_offset kwarg and removing the marker
        self.assertEquals(astypes.get_ecma_array(StringIO('\x00\x00\x00\x04\x00\x00\x01\x00\x00\x01 \x00\x40\x08\x00\x00\x00\x00\x00\x00\x00\x03goo\x02\x00\x02λ\x00\x00'), max_offset=30), {'': False, ' ': 3, 'goo': u'λ'.encode('utf-8')})
        # try not using the max_offset kwarg and removing the marker, should fail
        self.assertRaises(primitives.EndOfFile, astypes.get_ecma_array, StringIO('\x00\x00\x00\x04\x00\x00\x01\x00\x00\x01 \x00\x40\x08\x00\x00\x00\x00\x00\x00\x00\x03goo\x02\x00\x02λ\x00\x00'))

    def test_strict_array(self):
        self.set_name('strict_array')
        self.add_get_test('\x00\x00\x00\x01\x00\x3f\xf0\x00\x00\x00\x00\x00\x00', [1])
        self.add_get_test('\x00\x00\x00\x06\x00\x40\x08\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00\x00\x00\xc0\x15\x99\x99\x99\x99\x99\x9a\x02\x00\x02\xce\xbb\x01\x01', [3, False, '', -5.4, 'λ', True])
        self.add_make_test([-1, 'foo'], '\x00\x00\x00\x02\x00\xbf\xf0\x00\x00\x00\x00\x00\x00\x02\x00\x03\x66\x6f\x6f')
        self.add_equivalence_test(['a', 4, 'b', 6, True])
        self.add_equivalence_test([])
        self.add_equivalence_test(['a', 4, 'b', ['g', 6.3, 'j', {'a': 1, 'b': 2}]])
        self.run_tests()

        # Various corner cases:

        # try wrong array size, should fail
        self.assertRaises(primitives.EndOfFile, astypes.get_strict_array, StringIO('\x00\x00\x00\x07\x00\x40\x08\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00\x00\x00\xc0\x15\x99\x99\x99\x99\x99\x9a\x02\x00\x02\xc2\xbb\x01\x01'))

    def test_date(self):
        self.set_name('date')
        self.add_get_test('\x42\x5d\x2b\x75\x29\xaa\x00\x00\x00\x1e',
                          datetime(1985, 11, 18, 4, 0, 1, tzinfo=FakeTZInfo(30)))
        self.add_get_test('\x42\x5d\x2b\x7c\x07\x7a\x00\x00\x00\x00',
                          datetime(1985, 11, 18, 4, 0, 1, tzinfo=FakeTZInfo(0)))
        self.add_make_test(datetime(2009, 01, 01, 20, 0, 0, tzinfo=FakeTZInfo(10)),
                           '\x42\x71\xe9\x3b\xec\x64\x00\x00\x00\x0a')
        # FIXME add tests for serializing naive datetimes
        self.add_equivalence_test(datetime.now(FakeTZInfo(0)).replace(microsecond=0))
        self.add_equivalence_test(datetime.now(FakeTZInfo(-10)).replace(microsecond=0))
        self.run_tests()

    def test_null(self):
        self.set_name('null')
        self.add_get_test('', None)
        self.add_make_test(None, '')
        self.add_equivalence_test(None)
        self.run_tests()

    def test_object(self):
        self.set_name('object')
        # these tests are almost identical to ECMA array's
        o = astypes.FLVObject({'test key': 1})
        self.add_get_test('\x00\x08test key\x00\x3f\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x09', o)
        self.add_make_test({'key': 'val'}, '\x00\x03key\x02\x00\x03val\x00\x00\x09')

        o = astypes.FLVObject()
        for key, val in (('key', 7.4), ('w00t', 'w00t'), ('blargh!', u'λ')):
            setattr(o, key, val)
        self.add_make_test(o, '\x00\x03key\x00\x40\x1d\x99\x99\x99\x99\x99\x9a\x00\x04w00t\x02\x00\x04w00t\x00\x07blargh!\x02\x00\x02\xce\xbb\x00\x00\x09')

        # try an object, that's not iterable, should serialize its __dict__
        class dummy(object): pass
        d = dummy()
        d.x = 1
        self.add_make_test(d, '\x00\x01\x78\x00\x3f\xf0\x00\x00\x00\x00\x00\x00\x00\x00\x09')

        o = astypes.FLVObject()
        o.a, o.b = 4, 6
        self.add_equivalence_test(o)

        o = astypes.FLVObject()
        self.add_equivalence_test(o)

        o, o1 = astypes.FLVObject(), astypes.FLVObject()
        o1.g, o1.j = 6.3, [1, 2, 'a', 3]
        o.a, o.b = 4, o1
        self.add_equivalence_test(o)

        self.run_tests()

        # Various corner cases:

        # try using the max_offset kwarg and removing the marker
        o = astypes.FLVObject()
        for key, val in (('', False), (' ', 3), ('goo', u'λ'.encode('utf-8'))):
            setattr(o, key, val)
        self.assertEquals(astypes.get_object(StringIO('\x00\x00\x01\x00\x00\x01 \x00\x40\x08\x00\x00\x00\x00\x00\x00\x00\x03goo\x02\x00\x02λ\x00\x00'), max_offset=26), o)
        # try not using the max_offset kwarg and removing the marker, should fail
        self.assertRaises(primitives.EndOfFile, astypes.get_object, StringIO('\x00\x00\x01\x00\x00\x01 \x00\x40\x08\x00\x00\x00\x00\x00\x00\x00\x03goo\x02\x00\x02λ\x00\x00'))

    def test_movieclip(self):
        self.set_name('movieclip')
        self.add_get_test('\x00\x0d/path/to/clip', astypes.MovieClip('/path/to/clip'))
        self.add_make_test(astypes.MovieClip('/other/path'), '\x00\x0b/other/path')
        self.add_equivalence_test(astypes.MovieClip(''))
        self.add_equivalence_test(astypes.MovieClip('λ'))
        self.run_tests()

        # test human-readable representation
        self.assertEquals(repr(astypes.MovieClip('path')), '<MovieClip at path>')

    def test_undefined(self):
        self.set_name('undefined')
        self.add_get_test('', astypes.Undefined())
        self.add_make_test(astypes.Undefined(), '')
        self.add_equivalence_test(astypes.Undefined())
        self.run_tests()

        # test human-readable representation
        self.assertEquals(repr(astypes.Undefined()), '<Undefined>')

    def test_reference(self):
        self.set_name('reference')
        self.add_get_test('\x01\x56', astypes.Reference(342))
        self.add_make_test(astypes.Reference(0), '\x00\x00')
        self.add_equivalence_test(astypes.Reference(14))
        self.run_tests()

        # test human-readable representation
        self.assertEquals(repr(astypes.Reference(1)), '<Reference to 1>')


class TestScriptSerialization(SerializerTester):

    def setUp(self):
        SerializerTester.setUp(self)
        self.module = astypes

    def test_script_data_value(self):
        self.set_name('script_data_value')
        self.add_get_test('\x08\x00\x00\x00\x01\x00\x03\x66\x6f\x6f\x0a\x00\x00\x00\x03\x01\x00\x05\x0a\x00\x00\x00\x01\x00\x40\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x09', {'foo': [False, None, [3.5]]})
        self.add_make_test(['string', 0], '\x0a\x00\x00\x00\x02\x02\x00\x06\x73\x74\x72\x69\x6e\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.add_equivalence_test({'a': 0.5,
                                   'b': [4, False, astypes.Undefined()],
                                   'c': {'d': datetime(2009, 01, 01, 20, 0, 0, tzinfo=FakeTZInfo(10))},
                                   'e': [astypes.Reference(3), None, 'foo']})
        self.run_tests()

        # Various corner cases:

        # Invalid value type
        self.assertRaises(astypes.MalformedFLV, astypes.get_script_data_value, StringIO('\x09\x00\x00\x00\x01\x00\x03\x66\x6f\x6f\x0a\x00\x00\x00\x03\x01\x00\x05\x0a\x00\x00\x00\x01\x00\x40\x0c\x00\x00\x00\x00\x00\x00\x00\x00\x09'))

    def test_script_data_variable(self):
        self.set_name('script_data_variable')
        self.add_get_test('\x00\x03\x66\x6f\x6f\x05', ('foo', None))
        self.run_tests()

        # can't just add a maker test, because it expects the maker to accept only one argument
        self.assertEquals(astypes.make_script_data_variable('variable name', [1, 2, '3']), '\x00\x0d\x76\x61\x72\x69\x61\x62\x6c\x65\x20\x6e\x61\x6d\x65\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x02\x00\x01\x33')
