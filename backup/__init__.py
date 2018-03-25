# coding: utf-8

"""
Create a backup archive from a database and a filesystem.
"""
from __future__ import print_function

__version__ = "1.0.0"

import subprocess
import functools

from backup.archive import Archive
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.target.s3 import S3, S3Error
from backup.utils import LF, LFLF


"""
    ########     ###     ######  ##    ## ##     ## ########
    ##     ##   ## ##   ##    ## ##   ##  ##     ## ##     ##
    ##     ##  ##   ##  ##       ##  ##   ##     ## ##     ##
    ########  ##     ## ##       #####    ##     ## ########
    ##     ## ######### ##       ##  ##   ##     ## ##
    ##     ## ##     ## ##    ## ##   ##  ##     ## ##
    ########  ##     ##  ######  ##    ##  #######  ##
"""


class Backup(object):
    """ Class to create a backup from a database and a filesystem.

    To use initialize with a source and call execute with the desired
    targets. See backup.source for available sources and backup.target for
    available targets.

    """

    def __init__(self, source, mailto, mailfrom, quiet=False):
        self.source = source
        self.mailto = mailto
        self.mailfrom = mailfrom
        self.quiet = quiet

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

    def sendReport(self, reporters):
        """ Sends a report with the results of the archive creation.
        """
        from email.mime.text import MIMEText
        from email.header import Header

        reports = []
        for reporter in reporters:
            setup = str(reporter)
            results = reporter.reportResults()
            reports.append(LF.join([setup, results]))
        report = LFLF.join(reports)

        self.message(report)

        subject = "[BACKUP] Archive for {}".format(self.source.description)

        mail = MIMEText(report.encode('utf-8'), 'plain', 'utf-8')
        mail['Subject'] = Header(subject, 'utf-8')
        mail['To'] = self.mailto
        mail['From'] = self.mailfrom

        process = subprocess.Popen(
            ["/usr/sbin/sendmail", "-oi", "-t"],
            stdin=subprocess.PIPE,
        )
        process.communicate(mail.as_bytes())

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
            reporters = [self.source]

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

            # send report

            if archive:
                reporters.append(archive)
            if target:
                reporters.append(target)

            if self.mailto:
                self.message("Sending report to {} for {}".format(
                    self.mailto, self.source.description
                ))
                self.sendReport(reporters)

        except (DBError, FSError, S3Error) as e:
            print(e)
