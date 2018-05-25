# coding: utf-8

import pytest  # noqa: 401

from backup.utils import timestamp4now, timestamp2date, slugify, formatsize


def testTimestamp():
    from datetime import datetime
    now = datetime.now().replace(microsecond=0)
    timestamp = timestamp4now(now=now)
    assert(timestamp2date(timestamp) == now)


def testSlugify():
    assert slugify(None) is None
    assert slugify(u"") == ""
    assert slugify(u"This") == "this"
    assert slugify(u"is") == "is"
    assert slugify(u"the end") == "the-end"
    assert slugify(u"Hold your breath ") == "hold-your-breath"
    assert slugify(u" and count to ten") == "and-count-to-ten"
    assert slugify(u"Feel the 34r7|-| move and then") == "feel-the-34r7-move-and-then"
    assert slugify(u"-- Hear my heart burst again") == "-hear-my-heart-burst-again"


def testFormatSize():
    assert formatsize(123) == "123.0 Bytes"
    assert formatsize(123123) == "123.1 kB"
    assert formatsize(123123123) == "123.1 MB"
    assert formatsize(123123123123) == "123.1 GB"
    assert formatsize(123123123123123) == "123.1 TB"
    assert formatsize(123123123123123123) == "123.1 PB"
    assert formatsize(123123123123123123123) == "123.1 EB"
    assert formatsize(123123123123123123123123) == "123.1 ZB"
    assert formatsize(123123123123123123123123123) == "123.1 YB"
    assert formatsize(123123123123123123123123123123) == "123123.1 YB"

def testFormatSizeBinary():
    assert formatsize(123, binary=True) == "123.0 Bytes"
    assert formatsize(123123, binary=True) == "120.2 KiB"
    assert formatsize(123123123, binary=True) == "117.4 MiB"
    assert formatsize(123123123123, binary=True) == "114.7 GiB"
    assert formatsize(123123123123123, binary=True) == "123.1 TB"
    assert formatsize(123123123123123123, binary=True) == "123.1 PB"
    assert formatsize(123123123123123123123, binary=True) == "123.1 EB"
    assert formatsize(123123123123123123123123, binary=True) == "123.1 ZB"
    assert formatsize(123123123123123123123123123, binary=True) == "123.1 YB"
    assert formatsize(123123123123123123123123123123, binary=True) == "123123.1 YB"
