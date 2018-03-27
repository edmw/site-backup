# coding: utf-8

__version__ = '1.0.0'

import re

from datetime import datetime

LF = '\n'
LFLF = '\n\n'
SPACE = ' '

SUPERSCRIPT = dict(zip([ord(char) for char in '0123456789'], '⁰¹²³⁴⁵⁶⁷⁸⁹'))
FULLWIDTH = dict(zip([ord(char) for char in '0123456789'], '０１２３４５６７８９'))

TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'


def timestamp4now(now=datetime.now()):
    return now.strftime(TIMESTAMP_FORMAT)


def timestamp2date(timestamp):
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT)


def slugify(value):
    if value is not None:
        import unicodedata
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        value = re.sub(r'[-\s]+', '-', value)
    return value


def superscript(string):
    return string.translate(SUPERSCRIPT)


def fullwidth(string):
    return string.translate(FULLWIDTH)


def formatkv(kv, title=None):
    out = list()
    if title:
        out.append(title)
    for (k, v) in kv:
        out.append("    {}: {}".format(k, v))
    return "\n".join(out)


def formatsize(size, binary=False, format='{:.1f}'):
    if binary:
        base = 1024
        suffixes = ('KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')
    else:
        base = 1000
        suffixes = ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

    bytes = float(size)

    if bytes == 1:
        return '1 Byte'
    if bytes < base:
        return '{} Bytes'.format(bytes)

    for i, suffix in enumerate(suffixes):
        unit = base ** (i + 2)
        if bytes < unit:
            return (format + ' {}').format((base * bytes / unit), suffix)
    return (format + ' {}').format((base * bytes / unit), suffix)
