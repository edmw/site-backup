#!/usr/bin/python
# coding: utf-8

import os, os.path
import subprocess

from backup.archive import Archive
from backup.database import DB, DBError
from backup.filesystem import FS, FSError
from backup.source.wordpress import WP, WPError
from backup.target.s3 import S3, S3Error
from backup.utils import timestamp

def sendReport(mailto, mailfrom, reporters):
  from email.mime.text import MIMEText

  mail = MIMEText("\n\n".join([reporter.report() for reporter in reporters]))

  mail['Subject'] = "[WPBACKUP] Archive %s of Wordpress Blog '%s'" % (archive.name, wordpress.title)
  mail['From'] = mailfrom
  mail['To'] = mailto

  p = subprocess.Popen(["/usr/sbin/sendmail", "-oi", "-t"], stdin=subprocess.PIPE)
  p.communicate(mail.as_string())

##     ##    ###    #### ##    ## 
###   ###   ## ##    ##  ###   ## 
#### ####  ##   ##   ##  ####  ## 
## ### ## ##     ##  ##  ## ## ## 
##     ## #########  ##  ##  #### 
##     ## ##     ##  ##  ##   ### 
##     ## ##     ## #### ##    ## 

description = """
This script creates a backup of a Wordpress Blog instance.

It generates a compressed tar archive containing a dump
of the wordpress database and copies of the wordpress filesystem.
"""

epilog = """
This script will try to load the wordpress configuration file at
the given path and read the database configuration for the given
wordpress instance from that file.

The database parameters from the configuration file can be overwritten
by specifing the correspondent command line options.

"""

def dir_argument(string):
  if not os.path.isdir(string):
    raise argparse.ArgumentTypeError("%r is not an existing directory" % string)
  return string

if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('path', action='store', help='path to wordpress instance', type=dir_argument)
  parser.add_argument('-q', '--quiet', action='store_true', help='do not print status messages')
  parser.add_argument('--database', action='store_true', help='backup wordpress database')
  parser.add_argument('--filesystem', action='store_true', help='backup wordpress filesystem')
  group_db = parser.add_argument_group('database backup options', '')
  group_db.add_argument('--db', action='store', help='name for wordpress db', metavar='NAME')
  group_db.add_argument('--dbhost', action='store', help='hostname for wordpress db', metavar='HOST')
  group_db.add_argument('--dbuser', action='store', help='username for wordpress db', metavar='USER')
  group_db.add_argument('--dbpass', action='store', help='password for wordpress db', metavar='PASS')
  group_db.add_argument('--dbprefix', action='store', help='prefix for table names in wordpress db', metavar='PREFIX')
  group_local = parser.add_argument_group('local target', 'options for storing the backup archive on local filesystem')
  group_local.add_argument('--attic', action='store', help='local directory to store backup archive', metavar='DIR', type=dir_argument, nargs='?', const='.', default=None)
  group_s3 = parser.add_argument_group('s3 target', 'options for copying the backup archive to a s3 service')
  group_s3.add_argument('--s3', action='store', help='host for s3 server', metavar='HOST')
  group_s3.add_argument('--s3accesskey', action='store', help='access key for s3 server', metavar='KEY')
  group_s3.add_argument('--s3secretkey', action='store', help='secret key for s3 server', metavar='KEY')
  group_s3.add_argument('--s3bucket', action='store', help='bucket at s3 server', metavar='BUCKET')
  group_report = parser.add_argument_group('report options', '')
  group_report.add_argument('--mail-from', action='store', help='sender address for report mails', metavar='MAIL')
  group_report.add_argument('--mail-to-admin', action='store_true', help='send report to wordpress administrator')

  arguments = parser.parse_args()

  def message(text):
    if not arguments.quiet: print text
    
  try:
    wordpress = WP(arguments.path)
  except WPError, x:
    print x
    sys.exit(1)

  if not arguments.db is None:
    wordpress.db = arguments.db
  if not arguments.dbhost is None:
    wordpress.dbhost = arguments.dbhost
  if not arguments.dbuser is None:
    wordpress.dbuser = arguments.dbuser
  if not arguments.dbpass is None:
    wordpress.dbpass = arguments.dbpass
  if not arguments.dbprefix is None:
    wordpress.dbprefix = arguments.dbprefix

  timestamp = timestamp()
  try:
    reporters = [wordpress]

    archive = Archive("%s-%s" % (wordpress.slug, timestamp))
    with archive:
      message("Creating archive for Wordpress Blog '%s'" % wordpress.title)

      if arguments.database is True:
        message("Processing database of Wordpress Blog '%s'" % wordpress.title)
        db = DB(wordpress.dbname, wordpress.dbhost, wordpress.dbuser, wordpress.dbpass, wordpress.dbprefix)
        db.dumpToArchive(archive)
        reporters.append(db)

      if arguments.filesystem is True:
        message("Processing filesystem of Wordpress Blog '%s'" % wordpress.title)
        fs = FS(wordpress.fspath)
        fs.addToArchive(archive)
        reporters.append(fs)

      archive.addManifest(timestamp)

    reporters.append(archive)

    if arguments.s3:
      # transfer archive to s3 service
      message("Transfering archive to S3 Service at %s" % arguments.s3)
      s3 = S3(
        arguments.s3,
        arguments.s3accesskey,
        arguments.s3secretkey,
        arguments.s3bucket if arguments.s3bucket else wordpress.slug,
      )
      s3.transferArchive(archive)
      reporters.append(s3)

    if arguments.attic:
      archive.rename(arguments.attic)
    else:
      archive.remove()

    if arguments.mail_to_admin:
      message("Send report to administrator %s of Wordpress Blog '%s'" % (wordpress.email, wordpress.title))
      sendReport(wordpress.email, arguments.mail_from, reporters)

  except DBError, x:
    print x.db
    print x
    sys.exit(1)
  except FSError, x:
    print x.fs
    print x
    sys.exit(1)
  except S3Error, x:
    print x.s3
    print x
    sys.exit(1)
