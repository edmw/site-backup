"""
Create a backup archive from a database and a filesystem.
"""

__version__ = "1.0.0"

import functools
import time
from typing import Any

import humanfriendly

from backup.archive import Archive
from backup.calendar import Calendar
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.reporter import Reporter, reporter_inspect
from backup.source import Source
from backup.target.s3 import S3Error
from backup.utils import LF, LFLF, formatkv
from backup.utils.mail import Attachment, Mailer, Priority

"""
    ########     ###     ######  ##    ## ##     ## ########
    ##     ##   ## ##   ##    ## ##   ##  ##     ## ##     ##
    ##     ##  ##   ##  ##       ##  ##   ##     ## ##     ##
    ########  ##     ## ##       #####    ##     ## ########
    ##     ## ######### ##       ##  ##   ##     ## ##
    ##     ## ##     ## ##    ## ##   ##  ##     ## ##
    ########  ##     ##  ######  ##    ##  #######  ##
"""


class Backup(Reporter):
    """Class to create a backup from a database and a filesystem.

    To use initialize with a source and call execute with the desired
    targets. See backup.source for available sources and backup.target for
    available targets.

    """

    def __init__(
        self,
        source: Source,
        mailer: Mailer | None = None,
        quiet: bool = False,
    ) -> None:  # TODO: Type source when base interface exists
        super().__init__()
        self.source = source
        self.mailer = mailer
        self.quiet = quiet
        self.stime = 0
        self.etime = 0
        self.error = None

    def __str__(self) -> str:
        return formatkv(
            [
                (
                    "Execution Time",
                    humanfriendly.format_timespan(self.etime - self.stime),
                ),
                ("Execution Error", str(self.error)),
                ("Report(To)", self.mailer),
            ],
            title="SITEBACKUP",
        )

    def message(self, text: str) -> None:
        """Prints a message if not told to be quiet."""
        if not self.quiet:
            print(text)

    def backup_database(self, archive: Archive) -> DB:
        """Creates a database backup and stores it into the archive."""
        self.message(f"Processing database of {self.source.description}")

        db = DB(
            self.source.dbname,
            self.source.dbhost,
            self.source.dbuser,
            self.source.dbpass,
            self.source.dbprefix,
        )
        db.dump_to_archive(archive)
        return db

    def backup_filesystem(self, archive: Archive) -> FS:
        """Creates filesystem backup and stores it into the archive."""
        self.message(f"Processing filesystem of {self.source.description}")

        fs = FS(self.source.fspath)
        fs.add_to_archive(archive)
        return fs

    def send_report(
        self,
        reporters: list[Any],
        mailer: Mailer,
        attachments: list[Attachment] | None = None,
    ) -> None:  # TODO: Type reporters when base interface exists
        """Sends a report with the results of the archive creation."""

        reports = []
        for reporter in reporters:
            out = [str(reporter)]
            parameters = reporter.report_parameters()
            if parameters:
                out.append(parameters)
            results = reporter.report_results()
            if results:
                out.append(results)
            reports.append(LF.join(out))
        report = LFLF.join(reports) + LFLF

        subject = f"[BACKUP] Archive for {self.source.description}"
        if self.error is None:
            subject = "👍" + subject
        else:
            subject = "❗" + subject

        mailer.send(
            subject,
            report,
            attachments,
            priority=Priority.NORMAL if not self.error else Priority.HIGH,
        )

        self.message(report)

    @reporter_inspect("dry")
    @reporter_inspect("database")
    @reporter_inspect("filesystem")
    @reporter_inspect("thinning")
    def execute(
        self,
        targets,
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    ):
        """Perfoms the creation of a backup.

        The flags database and filesystem specify which data should be
        included in the backup. Setting both flags to False will result
        in an empty backup.

        The backup will be transferred to each of the given targets.

        Each given target will be thinned out according to the given
        thinning strategy.

        If attic is given the backup file will be renamed to its value.
        Otherwise the backup file will be deleted (after it was
        transferred to the given targets, of course).

        """

        def perform_thinning(strategy, archives):
            """Execute the given thinning strategy on the given archives."""
            inarchives, outarchives = strategy.execute_on(archives, attr="ctime")

            return (inarchives, outarchives)

        reporters: list[Reporter] = [self]

        try:
            # start of execution
            self.stime = time.monotonic()

            reporters.append(self.source)

            # create archive (if requested)

            if database or filesystem:

                archive = Archive(self.source.slug)
                with archive:
                    self.message(f"Creating archive for {self.source.description}")

                    if database is True:
                        reporter = self.backup_database(archive)
                        reporters.append(reporter)

                    if filesystem is True:
                        reporter = self.backup_filesystem(archive)
                        reporters.append(reporter)

                    archive.add_manifest(archive.timestamp)

                # transfer archive to targets

                for target in targets:
                    self.message(f"Transfering archive to {target.description}")
                    target.transfer_archive(archive, dry=dry)

            else:
                archive = None

            # thin out target (if requested)

            if thinning:
                for target in targets:
                    self.message(
                        f"Thinning archives on {target.description} using strategy '{thinning}'"
                    )
                    target.perform_thinning(
                        self.source.slug,
                        functools.partial(perform_thinning, thinning),
                        dry=dry,
                    )

            # remove archive

            if archive:
                if attic:
                    archive.rename(attic)
                else:
                    archive.remove()

            # end of execution
            self.etime = time.monotonic()

            # send report

            if archive:
                reporters.append(archive)
            for target in targets:
                reporters.append(target)

            if self.mailer and self.mailer.serviceable():
                self.message(f"Sending report by {self.mailer}")

                attachments = []

                # create celendar attachments
                for target in targets:
                    calendar = Calendar(target.list_archives())
                    doc = calendar.format()
                    if doc:
                        attachments.append(
                            Attachment(
                                f"{self.source.slug}-{target.label}-calendar.html",
                                "text/html",
                                doc,
                            )
                        )

                self.send_report(reporters, self.mailer, attachments)

            return "OK"

        except (DBError, FSError, S3Error) as e:
            self.error = e
            self.etime = time.monotonic()
            if self.mailer and self.mailer.serviceable():
                self.send_report(reporters, self.mailer)
