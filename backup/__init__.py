# coding: utf-8

"""
Create a backup archive from a database and a filesystem.
"""
from __future__ import print_function

__version__ = "1.0.0"

import time
import functools
import logging

import humanfriendly

from backup.reporter import Reporter, ReporterInspect
from backup.archive import Archive
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.target.s3 import S3, S3Error
from backup.calendar import Calendar
from backup.utils import LF, LFLF, formatkv
from backup.utils.mail import Mailer, Priority, Attachment


"""
    ########     ###     ######  ##    ## ##     ## ########
    ##     ##   ## ##   ##    ## ##   ##  ##     ## ##     ##
    ##     ##  ##   ##  ##       ##  ##   ##     ## ##     ##
    ########  ##     ## ##       #####    ##     ## ########
    ##     ## ######### ##       ##  ##   ##     ## ##
    ##     ## ##     ## ##    ## ##   ##  ##     ## ##
    ########  ##     ##  ######  ##    ##  #######  ##
"""


class Backup(Reporter, object):
    """ Class to create a backup from a database and a filesystem.

    To use initialize with a source and call execute with the desired
    targets. See backup.source for available sources and backup.target for
    available targets.

    """

    def __init__(self, source, mailer=None, quiet=False):
        super(Backup, self).__init__()
        self.source = source
        self.mailer = mailer
        self.quiet = quiet
        self.stime = 0
        self.etime = 0
        self.error = None

    def __str__(self):
        return formatkv(
            [
                ("Execution Time", humanfriendly.format_timespan(self.etime - self.stime)),
                ("Execution Error", str(self.error)),
                ("Report(To)", self.mailer),
            ],
            title="SITEBACKUP",
        )

    def message(self, text):
        """ Prints a message if not told to be quiet. """
        if not self.quiet:
            print(text)

    def backupDatabase(self, archive):
        """ Creates a database backup and stores it into the archive.
        """
        self.message("Processing database of {}".format(self.source.description))

        db = DB(
            self.source.dbname,
            self.source.dbhost,
            self.source.dbuser,
            self.source.dbpass,
            self.source.dbprefix
        )
        db.dumpToArchive(archive)
        return db

    def backupFilesystem(self, archive):
        """ Creates filesystem backup and stores it into the archive.
        """
        self.message("Processing filesystem of {}".format(self.source.description))

        fs = FS(
            self.source.fspath
        )
        fs.addToArchive(archive)
        return fs

    def sendReport(self, reporters, mailer, attachments=None):
        """ Sends a report with the results of the archive creation.
        """

        reports = []
        for reporter in reporters:
            out = [str(reporter)]
            parameters = reporter.reportParameters()
            if parameters:
                out.append(parameters)
            results = reporter.reportResults()
            if results:
                out.append(results)
            reports.append(LF.join(out))
        report = LFLF.join(reports) + LFLF

        subject = "[BACKUP] Archive for {}".format(self.source.description)
        if self.error is None:
            subject = '👍' + subject
        else:
            subject = '❗' + subject

        mailer.send(
            subject,
            report,
            attachments,
            priority=Priority.NORMAL if not self.error else Priority.HIGH
        )

        self.message(report)

    @ReporterInspect('dry')
    @ReporterInspect('database')
    @ReporterInspect('filesystem')
    @ReporterInspect('thinning')
    def execute(
        self, targets=None, database=False, filesystem=False, thinning=None, attic=None, dry=False
    ):

        """ Perfoms the creation of a backup.

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
            """ Execute the given thinning strategy on the given archives. """
            inarchives, outarchives = strategy.executeOn(
                archives, attr='ctime'
            )

            return (inarchives, outarchives)

        try:
            # start of execution
            self.stime = time.monotonic()

            reporters = [self]

            reporters.append(self.source)

            # create archive (if requested)

            if database or filesystem:

                archive = Archive(self.source.slug)
                with archive:
                    self.message("Creating archive for {}".format(self.source.description))

                    if database is True:
                        reporter = self.backupDatabase(archive)
                        reporters.append(reporter)

                    if filesystem is True:
                        reporter = self.backupFilesystem(archive)
                        reporters.append(reporter)

                    archive.addManifest(archive.timestamp)

                # transfer archive to targets

                for target in targets:
                    self.message("Transfering archive to {}".format(target.description))
                    target.transferArchive(archive, dry=dry)

            else:
                archive = None

            # thin out target (if requested)

            if thinning:
                for target in targets:
                    self.message("Thinning archives on {} using strategy '{}'".format(
                        target.description, thinning
                    ))
                    target.performThinning(
                        self.source.slug,
                        functools.partial(perform_thinning, thinning),
                        dry=dry
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
                self.message("Sending report by {}".format(self.mailer))

                attachments = []

                # create celendar attachments
                for target in targets:
                    calendar = Calendar(target.listArchives())
                    doc = calendar.format()
                    if doc:
                        attachments.append(
                            Attachment(
                                "{}-{}-calendar.html".format(self.source.slug, target.label),
                                "text/html",
                                doc
                            )
                        )

                self.sendReport(reporters, self.mailer, attachments)

            return "OK"

        except (DBError, FSError, S3Error) as e:
            self.error = e
            self.etime = time.monotonic()
            if self.mailer and self.mailer.serviceable():
                self.sendReport(reporters, self.mailer)
