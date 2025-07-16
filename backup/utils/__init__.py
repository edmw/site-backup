# coding: utf-8

__version__ = "1.0.0"

import re

from datetime import datetime

LF = "\n"
LFLF = "\n\n"
SPACE = " "
SPACER = "    "

SUPERSCRIPT = dict(zip([ord(char) for char in "0123456789"], "⁰¹²³⁴⁵⁶⁷⁸⁹"))
FULLWIDTH = dict(zip([ord(char) for char in "0123456789"], "０１２３４５６７８９"))

TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"


def timestamp4now(now=datetime.now()):
    return now.strftime(TIMESTAMP_FORMAT)


def timestamp2date(timestamp):
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT)


def slugify(value):
    if value is not None:
        import unicodedata

        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        value = re.sub(r"[^\w\s-]", "", value).strip().lower()
        value = re.sub(r"[-\s]+", "-", value)
    return value


def superscript(string):
    return string.translate(SUPERSCRIPT)


def fullwidth(string):
    return string.translate(FULLWIDTH)


def formatkv(kv, title=None):
    o = list()
    a = o.append

    if title:
        a(title)

    for key, value in kv:
        if value:
            if hasattr(value, "__format_value__"):
                text = value.__format_value__()
            else:
                text = str(value)
            lines = text.splitlines() or None if text else None
            if lines:
                for index, line in enumerate(lines):
                    if index == 0:
                        a(SPACER + "{}: {}".format(key, line))
                    else:
                        a(2 * SPACER + "{}".format(line))
            else:
                a(SPACER + "{}: None".format(key))
        else:
            a(SPACER + "{}: None".format(key))

    return "\n".join(o)


def formatsize(size, binary=False, format="{:.1f}"):
    if binary:
        base = 1024
        suffixes = ("KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    else:
        base = 1000
        suffixes = ("kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

    bytes = float(size)

    if bytes == 1:
        return "1 Byte"
    if bytes < base:
        return "{} Bytes".format(bytes)

    for i, suffix in enumerate(suffixes):
        unit = base ** (i + 2)
        if bytes < unit:
            s = format.format(base * bytes / unit)
            return s + " {}".format(suffix)
    s = format.format(base * bytes / unit)
    return s + " {}".format(suffix)
