# coding: utf-8

"""
########     ###    ########    ###    ########     ###     ######  ########
##     ##   ## ##      ##      ## ##   ##     ##   ## ##   ##    ## ##
##     ##  ##   ##     ##     ##   ##  ##     ##  ##   ##  ##       ##
##     ## ##     ##    ##    ##     ## ########  ##     ##  ######  ######
##     ## #########    ##    ######### ##     ## #########       ## ##
##     ## ##     ##    ##    ##     ## ##     ## ##     ## ##    ## ##
########  ##     ##    ##    ##     ## ########  ##     ##  ######  ########
"""

# 8 data types
import collections

# 17 concurrent execution
import subprocess

import humanfriendly

from backup.reporter import Reporter, ReporterCheckResult
from backup.utils import formatkv


class DBError(Exception):
    def __init__(self, db, message):
        self.db = db
        self.message = message

    def __str__(self):
        return f"DBError({self.message!r})"


class DBAccessDeniedError(DBError):
    pass


class DBResult(collections.namedtuple("Result", ["size", "numberOfTables"])):
    """Class for results of db operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        size = humanfriendly.format_size(self.size)
        return f"Result(size={size}, numberOfTables={self.numberOfTables})"


class DB(Reporter, object):
    def __init__(self, db, host, user, password, prefix):
        super(DB, self).__init__()

        self.db = db
        self.host = host
        self.user = user
        self.password = password
        self.prefix = prefix

    def __str__(self):
        return formatkv(
            [
                ("DB", self.db),
            ],
            title="DATABASE",
        )

    def tables(self):
        # get list of tables
        if self.prefix:
            execute = f'show tables like "{self.prefix}%%"'
        else:
            execute = "show tables"
        p = subprocess.Popen(
            [
                "mysql",
                self.db,
                f"--host={self.host}",
                f"--user={self.user}",
                f"--password={self.password}",
                "--batch",
                "--skip-column-names",
                f"--execute={execute}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        (stdoutdata, stderrdata) = p.communicate()

        if not p.returncode == 0:
            message = f"RC={p.returncode}"
            if stderrdata:
                message = str(stderrdata).strip()
                if stderrdata.startswith("ERROR 1045"):
                    raise DBAccessDeniedError(self, message)
            raise DBError(self, message)

        return [line for line in stdoutdata.splitlines() if len(line.strip()) > 0]

    @ReporterCheckResult
    def dumpToArchive(self, archive):
        tables = self.tables()
        if not tables:
            raise DBError(self, "no tables to dump")

        p = subprocess.Popen(
            [
                "mysqldump",
                f"--host={self.host}",
                f"--user={self.user}",
                f"--password={self.password}",
                "--opt",
                self.db,
            ]
            + tables,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        (stdoutdata, stderrdata) = p.communicate()

        if not p.returncode == 0:
            message = f"RC={p.returncode}"
            if stderrdata:
                message = str(stderrdata).strip()
            raise DBError(self, message)

        f = archive.createArchiveFile(f"{archive.name}-db.sql", binmode=True)
        f.write(stdoutdata)
        archive.addArchiveFile(f)

        return DBResult(len(stdoutdata), len(tables))
