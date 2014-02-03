# coding: utf-8

__version__ = "1.0.0"

import sys, os, os.path
import subprocess

from backup.archive import Archive
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.target.s3 import S3, S3Error
from backup.utils import LF, LFLF, SPACE, timestamp

class Backup(object):
  def __init__(self, source, mailto, mailfrom, quiet=False):
    self.source = source
    self.mailto = mailto
    self.mailfrom = mailfrom
    self.quiet = quiet

  def message(self, text):
    if not self.quiet: print text

  def backupDatabase(self, archive):
    self.message("Processing database of %s" % self.source.description)
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
    self.message("Processing filesystem of %s" % self.source.description)
    fs = FS(
          self.source.fspath
        )
    fs.addToArchive(archive)
    return fs

  def sendReport(self, reporters):
    from email.mime.text import MIMEText

    mail = MIMEText(LFLF.join([LF.join([str(reporter), reporter.reportResults()]) for reporter in reporters]))

    mail['Subject'] = "[BACKUP] Archive for %s" % self.source.description
    mail['To'] = self.mailto
    mail['From'] = self.mailfrom

    p = subprocess.Popen(["/usr/sbin/sendmail", "-oi", "-t"], stdin=subprocess.PIPE)
    p.communicate(mail.as_string())

  def execute(self, targets=None, database=False, filesystem=False, attic=None):
    ts = timestamp()

    try:
      reporters = [self.source]

      # create archive

      archive = Archive("%s-%s" % (self.source.slug, ts))
      with archive:
        self.message("Creating archive for %s" % self.source.description)

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
        self.message("Transfering archive to %s" % target.description)
        target.transferArchive(archive)
        reporters.append(target)

      # remove archive

      if attic:
        archive.rename(attic)
      else:
        archive.remove()

      # send report

      if self.mailto:
        self.message("Sending report to %s for %s" % (self.mailto, self.source.description))
        self.sendReport(reporters)

    except (DBError, FSError, S3Error) as e:
      print e
