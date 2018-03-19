# coding: utf-8

   ###    ########   ######  ##     ## #### ##     ## ######## 
  ## ##   ##     ## ##    ## ##     ##  ##  ##     ## ##       
 ##   ##  ##     ## ##       ##     ##  ##  ##     ## ##       
##     ## ########  ##       #########  ##  ##     ## ######   
######### ##   ##   ##       ##     ##  ##   ##   ##  ##       
##     ## ##    ##  ##    ## ##     ##  ##    ## ##   ##       
##     ## ##     ##  ######  ##     ## ####    ###    ######## 

import sys, os, os.path, logging

from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult
from backup.utils import formatkv

import time
import collections

import tarfile

from io import StringIO, BytesIO

import humanfriendly

class ArchiveResult(collections.namedtuple('Result', ['size'])):
    """ Class for results of archive operations with proper formatting. """

    __slots__ = ()

    def __str__(self):
        return "Result(size=%s)" % (humanfriendly.format_size(self.size))

class ArchiveFile(object):
  def __init__(self, name, binmode=False):
    super(ArchiveFile, self).__init__()

    self.name = name

    self.binmode = binmode

    self.ctime = time.time()
    self.mtime = self.ctime

    self.handle = BytesIO()

  def write(self, data):
    self.handle.write(data if self.binmode else data.encode())

  def writeline(self, data):
    self.handle.write(data if self.binmode else data.encode())
    self.handle.write(b'\n')

  def size(self):
    self.handle.seek(0, os.SEEK_END)
    return self.handle.tell()

  def fileobject(self):
    self.handle.seek(0)
    return self.handle

class Archive(Reporter, object):
  def __init__(self, name):
    super(Archive, self).__init__()

    self.name = name
    self.path = '.'

    self.filename = "%s.tgz" % self.name

    self.tar = None

  def __str__(self):
    return formatkv([("Name", self.name)], title="ARCHIVE")

  def tarname(self, path=None):
    if not path:
      path = self.path
    return os.path.join(path, self.filename)

  def __enter__(self):
    self.tar = tarfile.open(self.tarname(), 'w:gz',
      debug=1 if logging.getLogger().getEffectiveLevel() == logging.DEBUG else 0
    )
    return self

  def __exit__(self, type, value, traceback):
    self.tar.close()

    self.storeResult("createArchive", ArchiveResult(os.path.getsize(self.tarname())))

  def createArchiveFile(self, name, binmode=False):
    return ArchiveFile(name, binmode=binmode)

  @ReporterCheckResult
  def addArchiveFile(self, archivefile):
    tarinfo = tarfile.TarInfo(archivefile.name)
    tarinfo.mtime = archivefile.mtime
    tarinfo.size = archivefile.size()
    self.tar.addfile(tarinfo, archivefile.fileobject())
    return archivefile.name

  @ReporterCheckResult
  def addPath(self, path, name=None):
    self.tar.add(path, arcname=name)
    return path

  @ReporterCheck
  def addManifest(self, timestamp):
    f = self.createArchiveFile("MANIFEST")
    f.writeline("Timestamp: %s" % timestamp)
    self.addArchiveFile(f)

  @ReporterCheck
  def rename(self, path):
    tarname = self.tarname()
    if not path == self.path:
      self.path = path
      os.rename(tarname, self.tarname())

  @ReporterCheck
  def remove(self):
    tarname = self.tarname()
    if os.path.isfile(tarname):
      os.remove(tarname)
      
