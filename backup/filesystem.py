# coding: utf-8

######## #### ##       ########  ######  ##    ##  ######  ######## ######## ##     ## 
##        ##  ##       ##       ##    ##  ##  ##  ##    ##    ##    ##       ###   ### 
##        ##  ##       ##       ##         ####   ##          ##    ##       #### #### 
######    ##  ##       ######    ######     ##     ######     ##    ######   ## ### ## 
##        ##  ##       ##             ##    ##          ##    ##    ##       ##     ## 
##        ##  ##       ##       ##    ##    ##    ##    ##    ##    ##       ##     ## 
##       #### ######## ########  ######     ##     ######     ##    ######## ##     ## 

import os
import logging

from backup.utils import formatkv
from backup.reporter import Reporter, ReporterCheckResult

class FSError(Exception):
  def __init__(self, fs, message):
    self.fs = fs
    self.message = message
  def __str__(self):
    return "FSError(%s)" % repr(self.message)

class FSNotFoundError(FSError):
  pass

class FS(Reporter, object):
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

  @ReporterCheck
  def addToArchive(self, archive):
    logging.debug("add path '%s' to archive '%s'" % (self.path, archive.name))
    archive.addPath(self.path, name=archive.name)
