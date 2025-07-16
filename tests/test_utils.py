# coding: utf-8

import pytest  # noqa: 401

from backup.utils import formatsize, slugify, timestamp2date, timestamp4now


def testTimestamp():
    from datetime import datetime

    now = datetime.now().replace(microsecond=0)
    timestamp = timestamp4now(now=now)
    assert timestamp2date(timestamp) == now


def testSlugify():
    assert slugify(None) is None
    assert slugify("") == ""
    assert slugify("This") == "this"
    assert slugify("is") == "is"
    assert slugify("the end") == "the-end"
    assert slugify("Hold your breath ") == "hold-your-breath"
    assert slugify(" and count to ten") == "and-count-to-ten"
    assert slugify("Feel the 34r7|-| move and then") == "feel-the-34r7-move-and-then"
    assert slugify("-- Hear my heart burst again") == "-hear-my-heart-burst-again"


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
    assert formatsize(123123123123123, binary=True) == "112.0 TiB"
    assert formatsize(123123123123123123, binary=True) == "109.4 PiB"
    assert formatsize(123123123123123123123, binary=True) == "106.8 EiB"
    assert formatsize(123123123123123123123123, binary=True) == "104.3 ZiB"
    assert formatsize(123123123123123123123123123, binary=True) == "101.8 YiB"
    assert formatsize(123123123123123123123123123123, binary=True) == "101845.1 YiB"
