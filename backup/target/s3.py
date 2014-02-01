# coding: utf-8

########    ###    ########   ######   ######## ########             ######   #######  
   ##      ## ##   ##     ## ##    ##  ##          ##     ##        ##    ## ##     ## 
   ##     ##   ##  ##     ## ##        ##          ##     ##        ##              ## 
   ##    ##     ## ########  ##   #### ######      ##                ######   #######  
   ##    ######### ##   ##   ##    ##  ##          ##     ##              ##        ## 
   ##    ##     ## ##    ##  ##    ##  ##          ##     ##        ##    ## ##     ## 
   ##    ##     ## ##     ##  ######   ########    ##                ######   #######  

import sys, os, os.path

from backup import ReporterMixin
from backup.utils import formatkv

import time
import collections

import boto
import boto.s3.connection
import socket

class S3Error(Exception):
  def __init__(self, s3, message):
    self.s3 = s3
    self.message = message
  def __str__(self):
    return "S3Error(%s)" % repr(self.message)

class S3(ReporterMixin, object):
  def __init__(self, host, accesskey, secretkey, bucket):
    super(S3, self).__init__()

    self.host = host
    self.accesskey = accesskey
    self.secretkey = secretkey
    self.bucket = bucket

    self.connection = boto.connect_s3(
      aws_access_key_id = self.accesskey,
      aws_secret_access_key = self.secretkey,
      host = self.host,
      calling_format = boto.s3.connection.OrdinaryCallingFormat(),
    )

  def __str__(self):
    return formatkv(
      [
        ("S3(Host)", self.host),
        ("S3(Bucket)", self.bucket),
      ],
      title="S3"
    )

  def transferArchive(self, archive):
    self.checkResultAndException(self._transferArchive, archive)
  def _transferArchive(self, archive):
    Result = collections.namedtuple('Result', ['sizeOfKey'])

    try:
      if self.connection.lookup(self.bucket):
        bucket = self.connection.get_bucket(self.bucket)
      else:
        bucket = self.connection.create_bucket(self.bucket)

      key = bucket.new_key(archive.filename)
      key.set_contents_from_filename(archive.filename, cb=self.progress, num_cb=10)

      return Result(key.size)

    except boto.exception.S3ResponseError, e:
      raise S3Error(self, repr(e))
    except socket.gaierror, e:
      raise S3Error(self, repr(e))

  def progress(self, complete, total):
    if sys.stdin.isatty():
      if complete == 0:
        self.progress_stime = time.time()
        sys.stdout.write("|" + "-" * 10 + "|")
        sys.stdout.write("\n")
        sys.stdout.write("|")
      sys.stdout.write(".")
      if complete == total:
        self.progress_etime = time.time()
        sys.stdout.write("|")
        sys.stdout.write("\n")
        sys.stdout.write("%d seconds" % int(self.progress_etime - self.progress_stime))
        sys.stdout.write("\n")
      sys.stdout.flush()

