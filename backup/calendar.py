"""
 ######     ###    ##       ######## ##    ## ########     ###    ########
##    ##   ## ##   ##       ##       ###   ## ##     ##   ## ##   ##     ##
##        ##   ##  ##       ##       ####  ## ##     ##  ##   ##  ##     ##
##       ##     ## ##       ######   ## ## ## ##     ## ##     ## ########
##       ######### ##       ##       ##  #### ##     ## ######### ##   ##
##    ## ##     ## ##       ##       ##   ### ##     ## ##     ## ##    ##
 ######  ##     ## ######## ######## ##    ## ########  ##     ## ##     ##
"""

import calendar
from collections import Counter
from datetime import date
from operator import attrgetter

from backup.archive import Archive


class Calendar(calendar.HTMLCalendar):

    def __init__(self, archives: list[Archive], today: date | None = None) -> None:
        if today is None:
            today = date.today()
        super().__init__()
        self.archives = sorted(archives, key=attrgetter("ctime"))
        self.first_archive = next(iter(self.archives), None)
        self.last_archive = next(reversed(self.archives), None)

        self.today = today

        self.dates = Counter([archive.ctime.date() for archive in archives])

    def formatday(self, day: int, weekday: int) -> str:
        h = super().formatday(day, weekday)
        if day:
            d = date(self.year, self.month, day)
            if d in self.dates:
                c = self.cssclasses[weekday]
                h = h.replace(c, c + " hasarchive")
            if d == self.today:
                c = self.cssclasses[weekday]
                h = h.replace(c, c + " today")
            elif d > self.today:
                c = self.cssclasses[weekday]
                h = h.replace(c, c + " future")
        return h

    def formatmonth(self, theyear: int, themonth: int, withyear: bool = True) -> str:
        self.year = theyear
        self.month = themonth
        return super().formatmonth(theyear, themonth, withyear=withyear)

    CSS = """
    body {
      font-family: "Arial", Helvetica, sans-serif;
      font-size: 1.6vw;
      font-weight: normal;
      line-height: 1.5vw;
      color: #2c3e50;
      background-color: #ecf0f1;
    }
    table, td, th {
      vertical-align: top;
    }
    table.year {
        border-spacing: 0;
        border-collapse: separate;
    }
    table.year td {
        padding: 1vw;
    }
    table.month {
        border-spacing: 1vw;
        border-collapse: separate;
    }
    table.month td {
        width: 3vw;
        height: 3vw;
        padding: 0;
        vertical-align: middle;
        text-align: center;
    }
    th.year {
      font-family: "Arial Black", Gadget, sans-serif;
      font-size: 2em;
      font-weight: bold;
      line-height: 2em;
      color: #3498db;
      background-color: inherit;
    }
    th.month {
      font-family: "Arial Black", Gadget, sans-serif;
      font-size: 1.2em;
      font-weight: bold;
      line-height: 2em;
    }
    th.mon,
    th.tue,
    th.wed,
    th.thu,
    th.fri,
    th.sat,
    th.sun {
      color: #bdc3c7;
      background-color: inherit;
      font-weight: normal;
    }
    .today {
      border-radius: 50%;
      box-shadow: 0 0 0 4px #2ecc71;
    }
    .future {
      color: #bdc3c7;
      background-color: inherit;
    }
    .hasarchive {
        font-weight: bold;
        color: #ecf0f1;
        background-color: #16a085;
        border-radius: 50%;
    }
    """

    def formatpage(self, content: str) -> str:
        h: list[str] = []
        a = h.append
        a("<!DOCTYPE HTML>")
        a("<html>")
        a("<head>")
        a('<meta charset="utf-8">')
        a("<title>Calendar</title>")
        a('<style type="text/css">' + self.CSS + "</style>")
        a("</head>")
        a("<body>")
        a(content)
        a("</body>")
        a("</html>")
        return "".join(h)

    def format(self) -> str:
        first_year = (
            self.first_archive.ctime.year if self.first_archive else self.today.year
        )
        last_year = (
            self.last_archive.ctime.year if self.last_archive else self.today.year
        )
        h: list[str] = []
        a = h.append
        year = first_year
        while year <= last_year:
            dates_in = [date for date in self.dates if date.year == year]
            if len(dates_in):
                a(self.formatyear(year))
            year = year + 1
        return self.formatpage("".join(h))
