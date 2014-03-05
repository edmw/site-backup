# coding: utf-8

"""
Create a backup archive from a database and a filesystem.
"""

__version__ = "1.0.0"

import sys, os, os.path

from backup.archive import Archive
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.target.s3 import S3, S3Error
from backup.utils import LF, LFLF, SPACE, timestamp

class Backup(object):
    """ Class to create an archive from a database and a filesystem.

    To use initialize with a source and call execute with the desired
    targets. See backup.source for available sources and backup.target for
    available targets.

    """

    def __init__(self, source, mailer=None, quiet=False):
        self.source = source
        self.mailer = mailer
        self.quiet = quiet

    def message(self, text):
        """ Prints a message if not told to be quiet. """
        if not self.quiet:
            print text

    def backupDatabase(self, archive):
        """ Creates a database backup and stores it into the archive.
        """
        self.message("Processing database of %s" \
            % self.source.description
        )

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
        self.message("Processing filesystem of %s" \
            % self.source.description
        )

        fs = FS(
            self.source.fspath
        )
        fs.addToArchive(archive)
        return fs

    def sendReport(self, reporters):
        """ Sends a report with the results of the archive creation.
        """

        reports = []
        for reporter in reporters:
            setup = str(reporter)
            results = reporter.reportResults()
            reports.append(LF.join([setup, results]))
        text = LFLF.join(reports)

        subject = "[BACKUP] Archive for %s" % self.source.description

        if self.mailer:
            self.mailer.sendMail(text, subject=subject)

    def execute(self,
            targets=None, database=False, filesystem=False, attic=None):

        """ Perfoms the creation of an archive.

            The flags database and filesystem specify which data should be
            included in the archive. Setting both flags to False will result
            in an empty archive.

            The archive will be transferred to each of the given targets.

            If attic is given the archive file will be renamed to its value.
            Otherwise the archive file will be deleted (after it was
            transferred to the given targets).

        """
        ts = timestamp()

        try:
            reporters = [self.source]

            # create archive

            archive = Archive("%s-%s" % (self.source.slug, ts))
            with archive:
                self.message("Creating archive for %s" \
                    % self.source.description
                )

                if database is True:
                    reporter = self.backupDatabase(archive)
                    reporters.append(reporter)

                if filesystem is True:
                    reporter = self.backupFilesystem(archive)
                    reporters.append(reporter)

                archive.addManifest(timestamp)

            reporters.append(archive)

            # transfer archive to targets

            for target in targets:
                self.message("Transfering archive to %s" \
                    % target.description
                )
                target.transferArchive(archive)
                reporters.append(target)

            # remove archive

            if attic:
                archive.rename(attic)
            else:
                archive.remove()

            # send report

            if self.mailer:
                self.message("Sending report to %s for %s" % (
                    self.mailer.recipients_as_string(),
                    self.source.description,
                ))
                self.sendReport(reporters)

        except (DBError, FSError, S3Error) as e:
            print e
