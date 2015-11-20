#!/usr/bin/env python
import datetime
from decimal import Decimal
import re
import time


__author__ = 'litleleprikon'


ESCAPE_REGEX = re.compile(r"[\0\n\r\032\'\"\\]")
ESCAPE_MAP = {'\0': '\\0', '\n': '\\n', '\r': '\\r', '\032': '\\Z',
              '\'': '\\\'', '"': '\\"', '\\': '\\\\', "'": "''"}


# +
def escape_item(val):
    encoder = encoders.get(type(val))

    if not encoder:
        raise TypeError("no default type converter defined")

    if encoder in (escape_dict, escape_sequence):
        val = encoder(val)
    else:
        val = encoder(val)
    return val


# +
def escape_dict(val):
    n = {}
    for k, v in val.items():
        quoted = escape_item(v)
        n[k] = quoted
    return n


# +
def escape_sequence(val):
    n = []
    for item in val:
        quoted = escape_item(item)
        n.append(quoted)
    return "(" + ",".join(n) + ")"


# +
def escape_set(val):
    val = map(lambda x: escape_item(x), val)
    return ','.join(val)


# +
def escape_bool(value):
    return str(value)


# +
def escape_object(value):
    return str(value)


# +
def escape_int(value):
    return str(value)


# +
def escape_float(value):
    return "{0:.15f}".format(value)


# +
def escape_string(value):
    return ("{:s}".format(ESCAPE_REGEX.sub(
        lambda match: ESCAPE_MAP.get(match.group(0)), value), ))


# +
def escape_str(value):
    return "'{:s}'".format(escape_string(value))


# +
def escape_unicode(value):
    return escape_str(value)


# +
def escape_bytes(value, mapping=None):
    return escape_str(value.decode('ascii', 'surrogateescape'))


# +
def escape_None(value):
    return 'NULL'


# +
def escape_timedelta(obj):
    seconds = int(obj.seconds) % 60
    minutes = int(obj.seconds // 60) % 60
    hours = int(obj.seconds // 3600) % 24 + int(obj.days) * 24
    if obj.microseconds:
        fmt = "'{0:02d}:{1:02d}:{2:02d}.{3:06d}'"
    else:
        fmt = "'{0:02d}:{1:02d}:{2:02d}'"
    return fmt.format(hours, minutes, seconds, obj.microseconds)


# +
def escape_time(obj):
    if obj.microsecond:
        fmt = "'{0.hour:02}:{0.minute:02}:{0.second:02}.{0.microsecond:06}'"
    else:
        fmt = "'{0.hour:02}:{0.minute:02}:{0.second:02}'"
    return fmt.format(obj)


# +
def escape_datetime(obj):
    if obj.microsecond:
        fmt = "'{0.year:04}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}.{0.microsecond:06}'"
    else:
        fmt = "'{0.year:04}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}'"
    return fmt.format(obj)


# +
def escape_date(obj):
    fmt = "'{0.year:04}-{0.month:02}-{0.day:02}'"
    return fmt.format(obj)


# +
def escape_struct_time(obj):
    return escape_datetime(datetime.datetime(*obj[:6]))


def convert_data(collection):
    return tuple(collection)


# +
def convert_datetime(obj):
    """Returns a DATETIME or TIMESTAMP column value as a datetime object:

      >>> datetime_or_None('2007-02-25 23:06:20')
      datetime.datetime(2007, 2, 25, 23, 6, 20)
      >>> datetime_or_None('2007-02-25T23:06:20')
      datetime.datetime(2007, 2, 25, 23, 6, 20)

    Illegal values are returned as None:

      >>> datetime_or_None('2007-02-31T23:06:20') is None
      True
      >>> datetime_or_None('0000-00-00 00:00:00') is None
      True

    """
    if ' ' in obj:
        sep = ' '
    elif 'T' in obj:
        sep = 'T'
    else:
        return convert_date(obj)

    try:
        ymd, hms = obj.split(sep, 1)
        usecs = '0'
        if '.' in hms:
            hms, usecs = hms.split('.')
        usecs = float('0.' + usecs) * 1e6
        return datetime.datetime(*[int(x) for x in ymd.split('-') + hms.split(':') + [usecs]])
    except ValueError:
        return convert_date(obj)


# +
def convert_timedelta(obj):
    """Returns a TIME column as a timedelta object:

      >>> timedelta_or_None('25:06:17')
      datetime.timedelta(1, 3977)
      >>> timedelta_or_None('-25:06:17')
      datetime.timedelta(-2, 83177)

    Illegal values are returned as None:

      >>> timedelta_or_None('random crap') is None
      True

    Note that MySQL always returns TIME columns as (+|-)HH:MM:SS, but
    can accept values as (+|-)DD HH:MM:SS. The latter format will not
    be parsed correctly by this function.
    """
    try:
        microseconds = 0
        if "." in obj:
            (obj, tail) = obj.split('.')
            microseconds = float('0.' + tail) * 1e6
        hours, minutes, seconds = obj.split(':')
        negate = 1
        if hours.startswith("-"):
            hours = hours[1:]
            negate = -1
        tdelta = datetime.timedelta(
            hours=int(hours),
            minutes=int(minutes),
            seconds=int(seconds),
            microseconds=int(microseconds)
        ) * negate
        return tdelta
    except ValueError:
        return None


# +
def convert_time(obj):
    """Returns a TIME column as a time object:

      >>> time_or_None('15:06:17')
      datetime.time(15, 6, 17)

    Illegal values are returned as None:

      >>> time_or_None('-25:06:17') is None
      True
      >>> time_or_None('random crap') is None
      True

    Note that MySQL always returns TIME columns as (+|-)HH:MM:SS, but
    can accept values as (+|-)DD HH:MM:SS. The latter format will not
    be parsed correctly by this function.

    Also note that MySQL's TIME column corresponds more closely to
    Python's timedelta and not time. However if you want TIME columns
    to be treated as time-of-day and not a time offset, then you can
    use set this function as the converter for FIELD_TYPE.TIME.
    """
    try:
        microseconds = 0
        if "." in obj:
            (obj, tail) = obj.split('.')
            microseconds = float('0.' + tail) * 1e6
        hours, minutes, seconds = obj.split(':')
        return datetime.time(hour=int(hours), minute=int(minutes),
                             second=int(seconds), microsecond=int(microseconds))
    except ValueError:
        return None


# +
def convert_date(obj):
    """Returns a DATE column as a date object:

      >>> date_or_None('2007-02-26')
      datetime.date(2007, 2, 26)

    Illegal values are returned as None:

      >>> date_or_None('2007-02-31') is None
      True
      >>> date_or_None('0000-00-00') is None
      True

    """
    try:
        return datetime.date(*[int(x) for x in obj.split('-', 2)])
    except ValueError:
        return None


# +
def convert_mysql_timestamp(timestamp):
    """Convert a MySQL TIMESTAMP to a Timestamp object.

    MySQL >= 4.1 returns TIMESTAMP in the same format as DATETIME:

      >>> mysql_timestamp_converter('2007-02-25 22:32:17')
      datetime.datetime(2007, 2, 25, 22, 32, 17)

    MySQL < 4.1 uses a big string of numbers:

      >>> mysql_timestamp_converter('20070225223217')
      datetime.datetime(2007, 2, 25, 22, 32, 17)

    Illegal values are returned as None:

      >>> mysql_timestamp_converter('2007-02-31 22:32:17') is None
      True
      >>> mysql_timestamp_converter('00000000000000') is None
      True

    """
    if timestamp[4] == '-':
        return convert_datetime(timestamp)
    timestamp += "0" * (14 - len(timestamp))  # padding
    year, month, day, hour, minute, second = \
        int(timestamp[:4]), int(timestamp[4:6]), int(timestamp[6:8]), \
        int(timestamp[8:10]), int(timestamp[10:12]), int(timestamp[12:14])
    try:
        return datetime.datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


# +
def convert_set(s):
    return set(s.split(","))


encoders = {
    bool: escape_bool,
    int: escape_int,
    float: escape_float,
    str: escape_str,
    tuple: escape_sequence,
    list: escape_sequence,
    set: escape_sequence,
    dict: escape_dict,
    type(None): escape_None,
    datetime.date: escape_date,
    datetime.datetime: escape_datetime,
    datetime.timedelta: escape_timedelta,
    datetime.time: escape_time,
    time.struct_time: escape_struct_time,
    Decimal: escape_object,
}
