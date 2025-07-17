from dataclasses import dataclass
from datetime import datetime, timedelta
from random import randint

import pytest

from backup.thinning import (
    LatestStrategy,
    SupportsLessThan,
    ThinningStrategy,
    ThinOutStrategy,
)
from backup.utils import timestamp2date


def everyday(lastday: datetime) -> set[datetime]:
    date = lastday
    dates = set()
    delta = timedelta(hours=6)
    for _ in range(4000):
        jitter = timedelta(seconds=randint(-6000, +6000))
        dates.add(date + jitter)
        date = date - delta
    delta = timedelta(days=1)
    for _ in range(2000):
        jitter = timedelta(seconds=randint(-60000, +60000))
        dates.add(date + jitter)
        date = date - delta
    return dates


@dataclass(frozen=True)
class Day(SupportsLessThan):
    timestamp: datetime

    def __str__(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Day):
            return self.timestamp < other.timestamp
        elif isinstance(other, datetime):
            return self.timestamp < other
        raise TypeError(f"Cannot compare Day with {type(other)}")


def somedays() -> list[Day]:
    timestamps = """
20140201213106
20150208051039
20160207050939
20170219040403
20170716040403
20170723040402
20170730040403
20170806040403
20170813040402
20170820040402
20170827040403
20170903040402
20170910040403
20170917040404
20170924040403
20171001040402
20171008040402
20171015040402
20171022040403
20171029040403
20171105040402
20171112040402
20171119040402
20171126040403
20171203040403
20171210040402
20171217040403
20171224040402
20171231040402
20180107040403
20180114040402
20180121040403
20180128040403
20180204040402
20180211040402
20180218040403
20180225040403
20180304040403
20180311040403
20180312010603
20180318064806
""".strip().split(
        "\n"
    )
    return list(map(Day, map(timestamp2date, timestamps)))


def test_argument_factory():
    # invalid parameters
    with pytest.raises(ValueError):
        ThinningStrategy.from_argument("A")
    with pytest.raises(ValueError):
        ThinningStrategy.from_argument("L0")
    with pytest.raises(ValueError):
        ThinningStrategy.from_argument("-1")
    # valid parameters
    s = ThinningStrategy.from_argument("L17")
    assert type(s) is LatestStrategy


def assert_thinning_on(dates, indates, outdates):
    if len(dates):
        assert next(reversed(sorted(dates))) in indates
    assert len(dates) == len(indates) + len(outdates)
    assert indates.isdisjoint(outdates)
    assert indates.union(outdates) == set(dates)


def test_thinning_latest():
    lastday = datetime(2222, 2, 2, 22, 22, 22)
    dates = everyday(lastday)
    (indates, outdates) = LatestStrategy(17).execute_on(dates)
    assert_thinning_on(dates, indates, outdates)
    assert len(indates) == 17
    assert len(outdates) == len(dates) - 17
    min_indate = min(indates)
    assert all(outdate < min_indate for outdate in outdates)
    (indates, outdates) = LatestStrategy(17171717).execute_on(dates)
    assert_thinning_on(dates, indates, outdates)
    assert len(indates) == len(dates)
    assert len(outdates) == 0
    min_indate = min(indates)
    assert all(outdate < min_indate for outdate in outdates)


def test_thin_out():
    lastday = datetime(2222, 2, 2, 22, 22, 22)
    fixdate = datetime(2222, 1, 31)

    # test empty
    (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on([], fix=fixdate)
    assert_thinning_on([], indates, outdates)
    assert len(indates) == 0
    assert len(outdates) == 0
    (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(
        [], fix=fixdate, attr="timestamp"
    )
    assert_thinning_on([], indates, outdates)
    assert len(indates) == 0
    assert len(outdates) == 0

    dates = everyday(lastday)
    (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(dates, fix=fixdate)
    assert_thinning_on(dates, indates, outdates)
    # thin out again - must be the same result
    (indates2, outdates2) = ThinOutStrategy(2, 3, 2).execute_on(indates, fix=fixdate)
    assert_thinning_on(indates, indates2, outdates2)
    assert len(indates2) == len(indates)
    assert len(outdates2) == 0
    # fast forward
    for _ in range(0, 100):
        fixdate = fixdate + timedelta(weeks=1)
        (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(indates, fix=fixdate)
    assert len(indates) == 10  # there must always be 9 yearly dates + latest
    # fast forward again (add a date first)
    indates.add(fixdate)
    for _ in range(0, 100):
        fixdate = fixdate + timedelta(weeks=1)
        (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(indates, fix=fixdate)
    assert len(indates) == 10  # there must always be 10 yearly dates now

    fixdate = datetime(2018, 3, 21)
    dates = somedays()
    (indates, outdates) = ThinOutStrategy(7, 7, 7).execute_on(
        dates, fix=fixdate, attr="timestamp"
    )
    assert_thinning_on(dates, indates, outdates)
    assert len(indates) == 21
    # thin out again - must be the same result
    (indates2, outdates2) = ThinOutStrategy(7, 7, 7).execute_on(
        indates, fix=fixdate, attr="timestamp"
    )
    assert_thinning_on(indates, indates2, outdates2)
    assert len(indates2) == len(indates)
    assert len(indates2) == 21
    assert len(outdates2) == 0
    # fast forward (days)
    for _ in range(0, 100):
        fixdate = fixdate + timedelta(days=1)
        (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(
            indates, fix=fixdate, attr="timestamp"
        )
    assert len(indates) == 6
    # fast forward (weeks)
    for _ in range(0, 100):
        fixdate = fixdate + timedelta(weeks=1)
        (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(
            indates, fix=fixdate, attr="timestamp"
        )
    assert len(indates) == 6
    # what happens if we go back in time
    fixdate = datetime(2018, 3, 21)
    for _ in range(0, 100):
        fixdate = fixdate - timedelta(days=1)
        (indates, outdates) = ThinOutStrategy(2, 3, 2).execute_on(
            indates, fix=fixdate, attr="timestamp"
        )
    assert len(indates) == 6
