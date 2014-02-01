# coding: utf-8

######## #### ##       ########  ######  ##    ##  ######  ######## ######## ##     ## 
##        ##  ##       ##       ##    ##  ##  ##  ##    ##    ##    ##       ###   ### 
##        ##  ##       ##       ##         ####   ##          ##    ##       #### #### 
######    ##  ##       ######    ######     ##     ######     ##    ######   ## ### ## 
##        ##  ##       ##             ##    ##          ##    ##    ##       ##     ## 
##        ##  ##       ##       ##    ##    ##    ##    ##    ##    ##       ##     ## 
##       #### ######## ########  ######     ##     ######     ##    ######## ##     ## 

import sys, os, os.path

from backup import ReporterMixin
from backup.utils import formatkv
from backup.archive import Archive

class FSError(Exception):
  def __init__(self, fs, message):
    self.fs = fs
    self.message = message
  def __str__(self):
    return "FSError(%s)" % repr(self.message)

class FSNotFoundError(FSError):
  pass

class FS(ReporterMixin, object):
  def __init__(self, path):
    super(FS, self).__init__()

    self.path = path

    if not os.path.exists(self.path):
      raise FSNotFoundError(self, "path '%s' not found" % self.path)

    if not os.path.isfile(os.path.join(self.path, "wp-config.php")):
      raise FSError(self, "path '%s' seems not to be a wordpress instance" % self.path)

  def __str__(self):
    return formatkv(
      [
        ("FS", self.path),
      ],
      title="FILESYSTEM"
    )

  def addToArchive(self, archive):
    self.checkException(self._addToArchive, archive)
  def _addToArchive(self, archive):
    archive.addPath(self.path, name=archive.name)
