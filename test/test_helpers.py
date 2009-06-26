# -*- coding: utf-8 -*-

import unittest

import sys
import datetime
from StringIO import StringIO

from flvlib import helpers


class TestFixedOffsetTimezone(unittest.TestCase):

    def setUp(self):
        self.now = datetime.datetime.now()

    def test_utcoffset(self):
        fo = helpers.FixedOffset(30, "Fixed")
        self.assertEquals(fo.utcoffset(self.now), datetime.timedelta(minutes=30))

        fo = helpers.FixedOffset(-15, "Fixed")
        self.assertEquals(fo.utcoffset(self.now), datetime.timedelta(minutes=-15))

        fo = helpers.FixedOffset(0, "Fixed")
        self.assertEquals(fo.utcoffset(self.now), datetime.timedelta(minutes=0))

    def test_tzname(self):
        fo = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(fo.tzname(self.now), "Fixed")

    def test_dst(self):
        fo = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(fo.dst(self.now), datetime.timedelta(0))

    def test_equality(self):
        fo1 = helpers.FixedOffset(15, "Fixed")
        fo2 = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(fo1, fo2)

        fo2 = helpers.FixedOffset(16, "Fixed")
        self.assertNotEquals(fo1, fo2)

        fo2 = helpers.FixedOffset(15, "Fixed2")
        self.assertNotEquals(fo1, fo2)

        self.assertNotEquals(fo1, None)

    def test_repr(self):
        fo = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(repr(fo),
                          "<FixedOffset %s>" % datetime.timedelta(minutes=15))


class TestOrderedAttrDict(unittest.TestCase):

    def test_creating(self):
        o1 = helpers.OrderedAttrDict()
        o2 = helpers.OrderedAttrDict(dict(a=1, b='c'))
        o3 = helpers.OrderedAttrDict(a=1, b='c')

        self.assertNotEquals(o1, o2)
        self.assertNotEquals(o1, o3)
        self.assertEquals(o2, o3)

    def test_mapping(self):
        o = helpers.OrderedAttrDict({'a': 1, 'b': 'c'})
        self.assertEquals(o['a'], 1)
        self.assertEquals(o['b'], 'c')
        self.assertRaises(KeyError, o.__getitem__, 'c')

        self.assertTrue('a' in o)
        self.assertFalse('c' in o)

        o['c'] = 1.5
        self.assertTrue('c' in o)
        self.assertTrue(o.has_key('c'))
        self.assertEquals(o['c'], 1.5)

        o['a'] = 2
        self.assertEquals(o['a'], 2)

        del o['c']
        self.assertTrue('c' not in o)
        self.assertFalse(o.has_key('c'))

        self.assertEquals(o.get('a', None), 2)
        self.assertEquals(o.get('c', None), None)

        self.assertEquals(o.items(), [('a', 2), ('b', 'c')])

        i = o.iteritems()
        self.assertTrue(iter(i), i)
        self.assertEquals(list(i), [('a', 2), ('b', 'c')])

        self.assertEquals(o.keys(), ['a', 'b'])

        i = o.iterkeys()
        self.assertTrue(iter(i), i)
        self.assertEquals(list(i), ['a', 'b'])

        self.assertEquals(o.pop('b'), 'c')
        self.assertFalse('b' in o)
        self.assertEquals(o.pop('c', None), None)
        self.assertRaises(KeyError, o.pop, 'c')

        self.assertEquals(o.values(), [2])

        self.assertEquals(o.setdefault('a', 1), 2)
        self.assertEquals(o.setdefault('b', 'c'), 'c')
        self.assertEquals(o['b'], 'c')

        self.assertTrue(bool(o))
        del o['b']
        self.assertEquals(o.popitem(), ('a', 2))
        self.assertRaises(KeyError, o.popitem)
        self.assertFalse(bool(o))

    def test_attribute(self):
        o = helpers.OrderedAttrDict(a=1, b='c')
        self.assertEquals(o.a, 1)
        self.assertEquals(o.b, 'c')
        self.assertRaises(AttributeError, getattr, o, 'c')

        self.assertTrue(hasattr(o, 'a'))
        self.assertFalse(hasattr(o, 'c'))

        o.c = 1.5
        self.assertTrue(hasattr(o, 'c'))
        self.assertEquals(o.c, 1.5)

        o.a = 2
        self.assertEquals(o.a, 2)

        del o.c
        self.assertFalse(hasattr(o, 'c'))

        self.assertEquals(getattr(o, 'a', None), 2)
        self.assertEquals(getattr(o, 'c', None), None)

        delattr(o, 'b')
        self.assertFalse(hasattr(o, 'b'))

        self.assertRaises(AttributeError, delattr, o, 'b')

        setattr(o, 'b', 'c')
        self.assertEquals(o.b, 'c')

    def test_ordering(self):
        o = helpers.OrderedAttrDict({'a': 1})
        o['b'] = 2
        self.assertEquals(o.items(), [('a', 1), ('b', 2)])

        o['c'] = 3
        self.assertEquals(o.items(), [('a', 1), ('b', 2), ('c', 3)])

        o = helpers.OrderedAttrDict()
        for number in xrange(ord('A'), ord('z')):
            o[chr(number)] = number
        self.assertEquals([(c, o[c]) for c in o.keys()],
                          [(chr(n), n) for n in xrange(ord('A'), ord('z'))])

        o = helpers.OrderedAttrDict()
        o['a'] = 1
        o['b'] = 2
        o['c'] = 3
        self.assertEquals(o.items(), [('a', 1), ('b', 2), ('c', 3)])

        del o['b']
        o['b'] = 2
        self.assertEquals(o.items(), [('a', 1), ('c', 3), ('b', 2)])

        o['a'] = 2
        self.assertEquals(o.items(), [('a', 2), ('c', 3), ('b', 2)])

    def test_equality(self):
        o1 = helpers.OrderedAttrDict()
        o2 = helpers.OrderedAttrDict()
        self.assertEquals(o1, o2)

        o1.a = 1
        o2['a'] = 1
        self.assertEquals(o1, o2)

        o2.a = 2
        self.assertNotEquals(o1, o2)

        o1['a'] = 2
        self.assertEquals(o1, o2)

        o1.b = 'c'
        self.assertNotEquals(o1, o2)

        o2.b = 'd'
        self.assertNotEquals(o1, o2)

        o2.b = 'c'
        self.assertEquals(o1, o2)

        o1.c = 1
        o1.d = 1
        o2.d = 1
        o2.c = 1
        # ordering matters
        self.assertNotEquals(o1, o2)

        del o1.d
        del o2.d
        self.assertEquals(o1, o2)

        o1.d = 1
        o2.d = 1
        self.assertEquals(o1, o2)

        self.assertNotEquals(o1, None)

    def test_weird_attribute_names(self):
        o = helpers.OrderedAttrDict()
        setattr(o, r'spaces! \slashes* ^carets`', 1)
        self.assertEquals(o[r'spaces! \slashes* ^carets`'], 1)

        o['NUL \x00 byte'] = 2
        self.assertEquals(getattr(o, 'NUL \x00 byte'), 2)

        o['\x45\x12\x86'] = 3
        self.assertEquals(o['\x45\x12\x86'], 3)

        o[4] = 4
        self.assertEquals(o[4], 4)

        o[(1, 2, u'3')] = 5
        self.assertEquals(o[(1, 2, u'3')], 5)

    def test_repr(self):
        o = helpers.OrderedAttrDict()
        o.a = 1
        o['b'] = 2
        o.c = 'd'
        self.assertEquals(repr(o), '<OrderedAttrDict %s>' % o)

    def test_str(self):
        o = helpers.OrderedAttrDict()
        o.a = 1
        o['b'] = 2
        o.c = 'd'
        o[3] = 3
        self.assertEquals(str(o), "{'a': 1, 'b': 2, 'c': 'd', 3: 3}")


class TestASPrettyPrinter(unittest.TestCase):

    def setUp(self):
        self.pp = helpers.ASPrettyPrinter

    def test_string(self):
        self.assertEquals(self.pp.pformat('a'), "'a'")
        self.assertEquals(self.pp.pformat('a b'), "'a b'")
        self.assertEquals(self.pp.pformat('\x91'), "'\x91'")

    def test_unicode(self):
        self.assertEquals(self.pp.pformat(u'λ'), "u'λ'")

    def test_number(self):
        self.assertEquals(self.pp.pformat(3), "3")
        self.assertEquals(self.pp.pformat(0.4), "0.4")
        self.assertEquals(self.pp.pformat(10L), "10")

    def test_dict(self):
        self.assertEquals(self.pp.pformat({}), "{}")
        self.assertEquals(self.pp.pformat({'a': 1}), "{'a': 1}")

        s = self.pp.pformat({'a': 1, 'b': 2})
        # ordering is undefined
        o1 = "{'a': 1,\n 'b': 2}"
        o2 = "{'b': 2,\n 'a': 1}"
        self.assertTrue((s == o1) or (s == o2))

        o = helpers.OrderedAttrDict()
        o['a'], o['b'], o['c'] = 1, 2, 3
        self.assertEquals(self.pp.pformat(o), "{'a': 1,\n 'b': 2,\n 'c': 3}")

    def test_list(self):
        self.assertEquals(self.pp.pformat([1, 2, 3]), "[1,\n 2,\n 3]")
        self.assertEquals(self.pp.pformat([]), "[]")

    def test_other_types(self):
        self.assertEquals(self.pp.pformat(None), "None")
        self.assertEquals(self.pp.pformat((1, 2, 3)), "(1, 2, 3)")

        class Test(object):
            def __repr__(self):
                return "<Test>"
        t = Test()
        self.assertEquals(self.pp.pformat(t), "<Test>")

    def test_printing(self):
        s = StringIO()
        old_stdout, sys.stdout = sys.stdout, s
        self.pp.pprint([1, 2, 3])
        # the trailing newline here comes from using Python's print
        self.assertEquals(s.getvalue(), "[1,\n 2,\n 3]\n")
        sys.stdout = old_stdout

    def test_complex(self):
        o1, o2 = helpers.OrderedAttrDict(), helpers.OrderedAttrDict()

        o1['a'], o1['b'], o1['c'] = 3, (1, 2, 3), [1, 2, [4, 5]]
        o2['key'] = {'otherkey': 10L}

        l = [o1, {'i': o2}, o1, (10, 11)]
        expected = """
[{'a': 3,
  'b': (1, 2, 3),
  'c': [1,
        2,
        [4,
         5]]},
 {'i': {'key': {'otherkey': 10}}},
 {'a': 3,
  'b': (1, 2, 3),
  'c': [1,
        2,
        [4,
         5]]},
 (10, 11)]"""
        self.assertEquals(self.pp.pformat(l), expected.lstrip('\n'))
