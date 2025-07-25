__version__ = "1.0.0"

import re
from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
from typing import Any

LF = "\n"
LFLF = "\n\n"
SPACE = " "
SPACER = "    "
COMMASPACE = ", "

SUPERSCRIPT = dict(
    zip(
        [ord(char) for char in "0123456789"],
        "⁰¹²³⁴⁵⁶⁷⁸⁹",
        strict=True,
    )
)
FULLWIDTH = dict(
    zip(
        [ord(char) for char in "0123456789"],
        "０１２３４５６７８９",
        strict=True,
    )
)

TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"


def timestamp4now(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now()
    return now.strftime(TIMESTAMP_FORMAT)


def timestamp2date(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT)


def slugify(value: str) -> str:
    assert value is not None, "value must not be None"
    assert value != "", "value must not be empty"

    import unicodedata

    if value.startswith("https://"):
        value = value[8:]
    elif value.startswith("http://"):
        value = value[7:]

    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)

    if value:
        return value
    else:
        return sha256(value.encode("utf-8")).hexdigest()


def superscript(string: str) -> str:
    return string.translate(SUPERSCRIPT)


def fullwidth(string: str) -> str:
    return string.translate(FULLWIDTH)


def formatkv(kv: Iterable[tuple[str, Any]], title: str | None = None):
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
                        a(f"{SPACER}{key}: {line}")
                    else:
                        a(f"{SPACER}{SPACER}{line}")
            else:
                a(f"{SPACER}{key}: None")
        else:
            a(f"{SPACER}{key}: None")

    return "\n".join(o)


def formatsize(size: int | float, binary: bool = False, format: str = "{:.1f}") -> str:
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
        return f"{bytes} Bytes"

    unit = base ** (len(suffixes) + 1)
    suffix = suffixes[-1]
    for i, s in enumerate(suffixes):
        u = base ** (i + 2)
        if bytes < u:
            unit = u
            suffix = s
            break
    s = format.format(base * bytes / unit)
    return f"{s} {suffix}"
