import unittest
from StringIO import StringIO
from test_common import SerializerTester

from flvlib import primitives


class EOFSerializerTester(SerializerTester):

    def equivalent(self, val, getter, maker):
        SerializerTester.equivalent(self, val, getter, maker)
        s = StringIO(maker(val))
        s.seek(1)
        self.assertRaises(primitives.EndOfFile, getter, s)


class TestPrimitives(EOFSerializerTester):

    def setUp(self):
        EOFSerializerTester.setUp(self)
        self.module = primitives

    def test_ui32(self):
        self.set_name('ui32')
        self.add_get_test('\x02\x93\xd3\xde', 43242462)
        self.add_make_test(3426345, '\x00\x34\x48\x29')
        self.add_equivalence_test(4532)
        self.run_tests()

    def test_si32_extended(self):
        self.set_name('si32_extended')
        self.add_get_test('\xcc\xff\x1b\xff', -3342565)
        self.add_make_test(9823, '\x00\x26\x5f\x00')
        self.add_equivalence_test(-243)
        self.add_equivalence_test(0)
        self.run_tests()

    def test_ui24(self):
        self.set_name('ui24')
        self.add_get_test('\x00\x04\xd2', 1234)
        self.add_make_test(4321, '\x00\x10\xe1')
        self.add_equivalence_test(16)
        self.run_tests()

    def test_ui16(self):
        self.set_name('ui16')
        self.add_get_test('\x00\x42', 66)
        self.add_make_test(333, '\x01\x4d')
        self.add_equivalence_test(7409)
        self.run_tests()

    def test_si16(self):
        self.set_name('si16')
        self.add_get_test('\x0d\xd8', 3544)
        self.add_make_test(-24, '\xff\xe8')
        self.add_equivalence_test(-26)
        self.run_tests()

    def test_ui8(self):
        self.set_name('ui8')
        self.add_get_test('\x22', 34)
        self.add_make_test(58, '\x3a')
        self.add_equivalence_test(5)
        self.run_tests()

    def test_double(self):
        self.set_name('double')
        self.add_get_test('\xbf\xd4\xdd\x2f\x1a\x9f\xbe\x77', -0.326)
        self.add_make_test(324653.45, '\x41\x13\xd0\xb5\xcc\xcc\xcc\xcd')
        # FIXME are these floating-representation safe?
        self.add_equivalence_test(5.436)
        self.add_equivalence_test(-5.136)
        self.add_equivalence_test(0)
        self.add_equivalence_test(-0.4525)
        self.run_tests()
