import time
import datetime

from StringIO import StringIO
from UserDict import DictMixin

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

class OrderedAttrDict(DictMixin):
    """
    A dictionary that preserves insert order and also has an attribute
    interface.

    Values can be transparently accessed and set as keys or as attributes.
    """

    def __init__(self, dict=None, **kwargs):
        self.__dict__["_order_priv_"] = []
        self.__dict__["_data_priv_"] = {}
        if dict is not None:
            self.update(dict)
        if len(kwargs):
            self.update(kwargs)

    # Mapping interface

    def __setitem__(self, key, value):
        if key not in self:
            self._order_priv_.append(key)
        self._data_priv_[key] = value

    def __getitem__(self, key):
        return self._data_priv_[key]

    def __delitem__(self, key):
        del self._data_priv_[key]
        self._order_priv_.remove(key)

    def keys(self):
        return list(self._order_priv_)

    # Attribute interface

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

    # String representation

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self._data_priv_)

    def __str__(self):
        return '%s' % self._data_priv_
