import time
import datetime
from UserDict import DictMixin, UserDict

class LocalTimezone(datetime.tzinfo):
    """A tzinfo class representing the system's idea of the local timezone"""
    STDOFFSET = datetime.timedelta(seconds=-time.timezone)
    if time.daylight:
        DSTOFFSET = datetime.timedelta(seconds=-time.altzone)
    else:
        DSTOFFSET = STDOFFSET
    DSTDIFF = DSTOFFSET - STDOFFSET
    ZERO = datetime.timedelta(0)

    def utcoffset(self, dt):
        if self._isdst(dt):
            return self.DSTOFFSET
        else:
            return self.STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return self.DSTDIFF
        else:
            return self.ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        return time.localtime(time.mktime(tt)).tm_isdst > 0

Local = LocalTimezone()

class FixedOffset(datetime.tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)

    def __repr__(self):
        return '<FixedOffset %s>' % self.__offset


class OrderedDict(DictMixin):
    """
    A dictionary that preserves insert order.
    Largely copied from twisted.python.util (thanks!).
    """

    def __init__(self, dict=None, **kwargs):
        self._order = []
        self.data = {}
        if dict is not None:
            self.update(dict)
        if len(kwargs):
            self.update(kwargs)

    def __repr__(self):
        return '{'+', '.join([('%r: %r' % item) for item in self.items()])+'}'

    def __setitem__(self, key, value):
        if key not in self:
            self._order.append(key)
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]
        self._order.remove(key)

    def keys(self):
        return list(self._order)
