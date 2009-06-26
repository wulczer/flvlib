import logging
import unittest
from StringIO import StringIO

class SerializerTester(unittest.TestCase):

    def setUp(self):
        self.name = None
        self.module = None
        self.get_tests = []
        self.make_tests = []
        self.equivalence_tests = []

    def set_name(self, name):
        self.name = name

    def set_module(self, module):
        self.module = module

    def add_get_test(self, input, expected):
        self.get_tests.append((input, expected))

    def add_make_test(self, value, blob):
        self.make_tests.append((value, blob))

    def add_equivalence_test(self, value):
        self.equivalence_tests.append(value)

    def run_tests(self):
        getter, maker = (getattr(self.module, 'get_' + self.name),
                         getattr(self.module, 'make_' + self.name))

        for input, expected in self.get_tests:
            self.assertEquals(getter(StringIO(input)), expected)

        for value, blob in self.make_tests:
            self.assertEquals(maker(value), blob)

        for value in self.equivalence_tests:
            self.equivalent(value, getter, maker)

    def equivalent(self, val, getter, maker):
        s = StringIO(maker(val))
        self.assertEquals(val, getter(s))
        self.assertEquals(s.read(), '')


class WarningCounterFilter(object):

    warnings = 0

    def filter(self, record):
        if record.levelno == logging.WARNING:
            self.warnings += 1
            return 0
        return 1
