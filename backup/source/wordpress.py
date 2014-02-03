# coding: utf-8

##      ##  #######  ########  ########  ########  ########  ########  ######   ######  
##  ##  ## ##     ## ##     ## ##     ## ##     ## ##     ## ##       ##    ## ##    ## 
##  ##  ## ##     ## ##     ## ##     ## ##     ## ##     ## ##       ##       ##       
##  ##  ## ##     ## ########  ##     ## ########  ########  ######    ######   ######  
##  ##  ## ##     ## ##   ##   ##     ## ##        ##   ##   ##             ##       ## 
##  ##  ## ##     ## ##    ##  ##     ## ##        ##    ##  ##       ##    ## ##    ## 
 ###  ###   #######  ##     ## ########  ##        ##     ## ########  ######   ######  

import sys, os, os.path
import re

from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult
from backup.utils import slugify, formatkv

import MySQLdb

class WPError(Exception):
  def __init__(self, wp, message):
    self.wp = wp
    self.message = message
  def __str__(self):
    return "WPError(%s)" % repr(self.message)

class WPNotFoundError(WPError):
  pass

class WPDatabaseError(WPError):
  pass

class WP(Reporter, object):
  def __init__(self, path):
    super(WP, self).__init__()

    self.fspath = path
    self.fsconfig = os.path.join(path, "wp-config.php")

    self.dbname = None
    self.dbhost = None
    self.dbprefix = None
    self.dbuser = None
    self.dbpass = None

    self.title = None
    self.email = None
    self.description = None
    self.slug = None

    # check preconditions
    if not os.path.exists(self.fspath) or not os.path.isfile(self.fsconfig):
      raise WPNotFoundError(self, "no wordpress instance found at '%s'" % self.fspath)

    self.parseConfiguration()
    self.queryDatabase()

    self.description = "Wordpress Blog '%s'" % self.title
    self.slug = slugify(self.title)

  def __str__(self):
    return formatkv(
      [
        ("Slug", self.slug),
        ("WP(Title)", self.title),
        ("WP(Email)", self.email),
        ("DB(Name)", self.dbname),
        ("DB(Host)", self.dbhost),
        ("DB(Prefix)", self.dbprefix),
        ("DB(User)", self.dbuser),
        ("DB(Pass)", "XXXXXX" if self.dbpass else "-"),
      ],
      title = "WORDPRESS",
    )

  @ReporterCheck
  def parseConfiguration(self):
    # regular expression for php defines: define('KEY', 'VALUE');
    re_define = re.compile(r"^\s*define\([\'\"]([^\'\"]+)[\'\"]\s*,\s*[\'\"]([^\'\"]+)[\'\"]\s*\)\s*;")
    # regular expression for php table prefix assignment: $table_prefix = 'PREFIX';
    re_table_prefix = re.compile(r"^\s*\$table_prefix\s*=\s*[\'\"]([^\'\"]+)[\'\"]\s*;")

    with open(self.fsconfig) as f:
      for line in f.readlines():

        m = re_define.match(line)
        if m:
          key = m.group(1)
          value = m.group(2)
          if key == 'DB_NAME': self.dbname = value; continue
          if key == 'DB_HOST': self.dbhost = value; continue
          if key == 'DB_USER': self.dbuser = value; continue
          if key == 'DB_PASSWORD': self.dbpass = value; continue

        m = re_table_prefix.match(line)
        if m:
          self.dbprefix = m.group(1)
          continue

  @ReporterCheck
  def queryDatabase(self):
    connection = None
    try:
      connection = MySQLdb.connect(db=self.dbname, host=self.dbhost, user=self.dbuser, passwd=self.dbpass)
      cursor = connection.cursor()
      cursor.execute("SELECT option_value FROM %soptions WHERE option_name = 'blogname'" % self.dbprefix)
      self.title = unicode(cursor.fetchone()[0])
      cursor.execute("SELECT option_value FROM %soptions WHERE option_name = 'admin_email'" % self.dbprefix)
      self.email = unicode(cursor.fetchone()[0])

    except MySQLdb.Error, e:
      raise WPDatabaseError(self, repr(e))

    finally:
      if connection:
        connection.close()
