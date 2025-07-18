"""
######## ##     ## #### ##    ## ##    ## #### ##    ##  ######
   ##    ##     ##  ##  ###   ## ###   ##  ##  ###   ## ##    ##
   ##    ##     ##  ##  ####  ## ####  ##  ##  ####  ## ##
   ##    #########  ##  ## ## ## ## ## ##  ##  ## ## ## ##   ####
   ##    ##     ##  ##  ##  #### ##  ####  ##  ##  #### ##    ##
   ##    ##     ##  ##  ##   ### ##   ###  ##  ##   ### ##    ##
   ##    ##     ## #### ##    ## ##    ## #### ##    ##  ######
"""

import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta
from operator import add, attrgetter
from typing import Protocol, override

from dateutil.relativedelta import relativedelta


class SupportsLessThan(Protocol):
    def __lt__(self, other: object) -> bool: ...


# TODO: needs refactoring
DateLike = datetime | SupportsLessThan


class ThinningStrategy(ABC):

    @classmethod
    def from_argument(cls, string: str) -> "ThinningStrategy":
        # strategy: latest
        # string contains number of latest backups to keep
        match = re.match(r"L([1-9]\d*)|.*", string)
        if match:
            number = match.group(1)
            if number:
                return LatestStrategy(int(number))

        # strategy: thin out by days, weeks and years
        match = re.match(r"([1-9]\d*)D([1-9]\d*)W([1-9]\d*)M|.*", string)
        if match:
            numbers = match.groups()
            if numbers and all(numbers):
                return ThinOutStrategy(*(map(int, numbers)))

        raise ValueError(f"not a valid strategy '{string}'")

    """ Implementation of specific thinning strategy:
        'dates' are guranteed to be sorted from newest to oldest.
    """

    @abstractmethod
    def __execute__(
        self,
        dates: list[DateLike],
        attr: str | None = None,
        fix: datetime | None = None,
    ) -> tuple[set[DateLike], set[DateLike]]:
        raise NotImplementedError

    """ Thinout the given set of dates.

        Returns a set of 'in' dates (all dates which should be kept and
        a set of 'out' dates (all dates which could be discarded.

        The union of in and out dates is equal to the set given. The
        intersection is guaranteed to be the empty set.
    """

    def execute_on(
        self,
        dates: Iterable[DateLike],
        attr: str | None = None,
        fix: datetime | None = None,
    ) -> tuple[set[DateLike], set[DateLike]]:
        if fix is None:
            fix = datetime.now()
        dates = sorted(dates) if attr is None else sorted(dates, key=attrgetter(attr))
        dates = list(reversed(dates))
        return self.__execute__(dates, attr=attr, fix=fix)


class LatestStrategy(ThinningStrategy):
    """Keep the x most recent dates. Discard all others."""

    def __init__(self, number: int):
        assert number > 0
        self.number = number

    def __str__(self):
        return f"LATEST {self.number}"

    @override
    def __execute__(
        self,
        dates: list[DateLike],
        attr: str | None = None,
        fix: datetime | None = None,
    ) -> tuple[set[DateLike], set[DateLike]]:
        assert isinstance(dates, list)

        logging.info("THINNING BY LATEST %d", self.number)

        in_dates = dates[: self.number]
        out_dates = dates[self.number :]

        for in_date in in_dates:
            logging.info("IN:  %r", in_date)
        for out_date in out_dates:
            logging.info("OUT: %r", out_date)

        return (set(in_dates), set(out_dates))


class ThinOutStrategy(ThinningStrategy):

    def __init__(self, days, weeks, months):
        assert days > 0
        assert weeks > 0
        assert months > 0
        self.days = days
        self.weeks = weeks
        self.months = months

    def __str__(self):
        return f"THIN OUT {self.days}D{self.weeks}W{self.months}M"

    @override
    def __execute__(
        self, dates: list[DateLike], attr=None, fix=None
    ) -> tuple[set[DateLike], set[DateLike]]:
        assert isinstance(dates, list)
        assert fix is not None

        fix = fix.replace(microsecond=0, second=0, minute=0, hour=0)

        logging.info("THINNING BY THIN OUT DAILY FOR %s DAYS", self.days)
        logging.info("THINNING BY THIN OUT WEEKLY FOR %s WEEKS", self.weeks)
        logging.info("THINNING BY THIN OUT MONTHLY FOR %s MONTHS", self.months)
        logging.info("THINNING BY THIN OUT YEARLY FOREVER")

        def head(dates):
            d = next(iter(dates), None)
            return d if d is None or attr is None else getattr(d, attr)

        def tail(dates):
            d = next(reversed(dates), None)
            return d if d is None or attr is None else getattr(d, attr)

        def date_is_after(d, fix):
            return d > fix if attr is None else getattr(d, attr) > fix

        def date_is_before(d, fix):
            return d <= fix if attr is None else getattr(d, attr) <= fix

        def date_is_same_day(obj, day):
            date = obj.date() if attr is None else getattr(obj, attr).date()
            return date == day.date()

        def date_is_in_span(obj, start, end):
            date = obj.date() if attr is None else getattr(obj, attr).date()
            return start.date() <= date and date < end.date()

        def split_dates_in_span(start, end):
            in_dates = []
            out_dates = []
            dates_in_span = [d for d in dates if date_is_in_span(d, start, end)]
            if len(dates_in_span):
                in_date = dates_in_span[-1]
                in_dates.append(in_date)
                out_dates = dates_in_span[:-1]
            for in_date in in_dates:
                logging.info("KEEP: %r", in_date)
            for out_date in out_dates:
                logging.info("DROP: %r", out_date)
            return in_dates, out_dates

        in_dates = []
        out_dates = []

        # always keep the newest date
        if len(dates):
            in_dates.append(dates.pop(0))
        # keep all dates which are newer than the fix date
        in_dates = in_dates + [d for d in dates if date_is_after(d, fix)]
        logging.info("BEGIN FUTURE AND LATEST")
        for date in in_dates:
            logging.info("KEEP: %r", date)
        logging.info("END FUTURE AND LATEST")

        # next, keep one date per day for self.days
        for d in range(0, self.days):
            day = fix - timedelta(days=d + 1)
            logging.info("BEGIN DAY %s", day.date())
            day_dates = [d for d in dates if date_is_same_day(d, day)]
            if len(day_dates):
                in_date = day_dates[-1]
                in_dates.append(in_date)
                logging.info("KEEP: %r", in_date)
                other_dates = day_dates[:-1]
                for out_date in other_dates:
                    logging.info("DROP: %r", out_date)
                out_dates = out_dates + other_dates
            logging.info("END DAY %s", day.date())

        # next keep one date per week for self.weeks
        for w in range(0, self.weeks):
            week_end = fix - timedelta(days=self.days, weeks=w)
            week_start = week_end - timedelta(weeks=1)
            logging.info("BEGIN WEEK %s - %s", week_start.date(), week_end.date())
            in_dates, out_dates = map(
                add, [in_dates, out_dates], split_dates_in_span(week_start, week_end)
            )
            logging.info("END WEEK %s - %s", week_start.date(), week_end.date())

        # this is tricky: adjust to months (keep all dates inbetween)
        weeks_end = fix - timedelta(days=self.days, weeks=self.weeks)
        fix_month = weeks_end.replace(day=1)
        logging.info("BEGIN ADJUSTMENT %s - %s", fix_month, weeks_end)
        adjustment_dates = [
            d for d in dates if date_is_in_span(d, fix_month, weeks_end)
        ]
        if len(adjustment_dates):
            for in_date in adjustment_dates:
                logging.info("KEEP: %r", in_date)
            in_dates = in_dates + adjustment_dates
        logging.info("END ADJUSTMENT %s - %s", fix_month, weeks_end)

        # next keep one date per month for self.months
        for m in range(0, self.months):
            month_end = fix_month - relativedelta(months=m)
            month_start = month_end - relativedelta(months=1)
            logging.info("BEGIN MONTH %s - %s", month_start.date(), month_end.date())
            in_dates, out_dates = map(
                add, [in_dates, out_dates], split_dates_in_span(month_start, month_end)
            )
            logging.info("END MONTH %s - %s", month_start.date(), month_end.date())

        # finally keep one date per year forever
        year_end = fix_month - relativedelta(months=self.months)
        year_start = year_end - relativedelta(years=1)
        last_date = tail(dates)
        while last_date and last_date < year_end:
            logging.info("BEGIN YEAR %s - %s", year_start.date(), year_end.date())
            in_dates, out_dates = map(
                add, [in_dates, out_dates], split_dates_in_span(year_start, year_end)
            )
            logging.info("END YEAR %s - %s", year_start.date(), year_end.date())
            year_end = year_end - relativedelta(years=1)
            year_start = year_end - relativedelta(years=1)

        in_dates = set(in_dates)
        out_dates = set(out_dates)

        return (set(in_dates), set(out_dates))
