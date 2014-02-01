# coding: utf-8

########     ###    ########    ###    ########     ###     ######  ######## 
##     ##   ## ##      ##      ## ##   ##     ##   ## ##   ##    ## ##       
##     ##  ##   ##     ##     ##   ##  ##     ##  ##   ##  ##       ##       
##     ## ##     ##    ##    ##     ## ########  ##     ##  ######  ######   
##     ## #########    ##    ######### ##     ## #########       ## ##       
##     ## ##     ##    ##    ##     ## ##     ## ##     ## ##    ## ##       
########  ##     ##    ##    ##     ## ########  ##     ##  ######  ######## 

import sys, os, os.path

import collections
import subprocess

from backup import ReporterMixin
from backup.utils import formatkv
from backup.archive import Archive

class DBError(Exception):
  def __init__(self, db, message):
    self.db = db
    self.message = message
  def __str__(self):
    return "DBError(%s)" % repr(self.message)

class DBAccessDeniedError(DBError):
  pass

class DB(ReporterMixin, object):
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
      title="DATABASE"
    )

  def tables(self):
    # get list of tables for prefix
    p = subprocess.Popen(
      [
        "mysql", self.db,
        "--host=%s" % self.host,
        "--user=%s" % self.user,
        "--password=%s" % self.password,
        "--batch",
        "--skip-column-names",
        "--execute=show tables like \"%s%%\"" % self.prefix,
      ],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    (stdoutdata, stderrdata) = p.communicate()

    if not p.returncode == 0:
      message = "RC=%d" % p.returncode
      if stderrdata:
        message = str(stderrdata).strip()
        if stderrdata.startswith("ERROR 1045"):
          raise DBAccessDeniedError(self, message)
      raise DBError(self, message) 

    return [line for line in stdoutdata.split('\n') if len(line.strip()) > 0]

  def dumpToArchive(self, archive):
    self.checkResultAndException(self._dumpToArchive, archive)
  def _dumpToArchive(self, archive):
    Result = collections.namedtuple('Result', ['lengthOfDump', 'numberOfTables'])

    tables = self.tables()

    p = subprocess.Popen(
      [
        "mysqldump",
        "--host=%s" % self.host,
        "--user=%s" % self.user,
        "--password=%s" % self.password,
        "--opt",
        self.db,
      ] + tables,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    (stdoutdata, stderrdata) = p.communicate()

    if not p.returncode == 0:
      message = "RC=%d" % p.returncode
      if stderrdata:
        message = str(stderrdata).strip()
      raise DBError(self, message)

    f = archive.createArchiveFile("%s-db.sql" % archive.name)
    f.write(stdoutdata)
    archive.addArchiveFile(f)

    return Result(len(stdoutdata), len(tables))
