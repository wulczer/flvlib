import unittest
import datetime

from flvlib import helpers


class TestFixedOffsetTimezone(unittest.TestCase):

    def test_utcoffset(self):
        fo = helpers.FixedOffset(30, "Fixed")
        self.assertEquals(fo.utcoffset(True), datetime.timedelta(minutes=30))
        self.assertEquals(fo.utcoffset(False), datetime.timedelta(minutes=30))

        fo = helpers.FixedOffset(-15, "Fixed")
        self.assertEquals(fo.utcoffset(True), datetime.timedelta(minutes=-15))

        fo = helpers.FixedOffset(0, "Fixed")
        self.assertEquals(fo.utcoffset(True), datetime.timedelta(minutes=0))

    def test_tzname(self):
        fo = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(fo.tzname(True), "Fixed")
        self.assertEquals(fo.tzname(False), "Fixed")

    def test_dst(self):
        fo = helpers.FixedOffset(15, "Fixed")
        self.assertEquals(fo.dst(False), datetime.timedelta(0))
        self.assertEquals(fo.dst(True), datetime.timedelta(0))

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
