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

import pymysql as mysql

class WPError(Exception):
    def __init__(self, wp, message):
        super(WPError, self).__init__()
        self.wp = wp
        self.message = message
    def __str__(self):
        return "WPError(%s)" % repr(self.message)

class WPNotFoundError(WPError):
    pass

class WPDatabaseError(WPError):
    pass

class WP(Reporter, object):
    def __init__(self, path, **kwargs):
        super(WP, self).__init__()

        self.fspath = path
        self.fsconfig = os.path.join(path, "wp-config.php")

        self.dbname = None
        self.dbhost = None
        self.dbport = 3306
        self.dbprefix = None
        self.dbuser = None
        self.dbpass = None
        self.dbcharset = "utf-8"

        self.title = None
        self.email = None

        self.description = None
        self.slug = None

        # check preconditions
        if not self.checkConfig():
            raise WPNotFoundError(self,
                "no wordpress instance found at '%s'" % self.fspath
            )

        self.parseConfiguration()

        if kwargs:
            if kwargs["dbname"]:
                self.dbname = kwargs["dbname"]
            if kwargs["dbhost"]:
                self.dbhost = kwargs["dbhost"]
            if kwargs["dbport"]:
                self.dbport = kwargs["dbport"]
            if kwargs["dbuser"]:
                self.dbuser = kwargs["dbuser"]
            if kwargs["dbpass"]:
                self.dbpass = kwargs["dbpass"]
            if kwargs["dbprefix"]:
                self.dbprefix = kwargs["dbprefix"]

        self.queryDatabase()

        self.description = "Wordpress Blog '%s'" % self.title
        self.slug = slugify(self.title)

    def checkConfig(self):
        return os.path.exists(self.fspath) and os.path.isfile(self.fsconfig)

    def __str__(self):
        return formatkv(
            [
                ("Slug", self.slug),
                ("WP(Title)", self.title),
                ("WP(Email)", self.email),
                ("DB(Name)", self.dbname),
                ("DB(Host)", self.dbhost),
                ("DB(Port)", self.dbport),
                ("DB(Prefix)", self.dbprefix),
                ("DB(User)", self.dbuser),
                ("DB(Pass)", "*******" if self.dbpass else "-"),
            ],
            title="WORDPRESS",
        )

    @ReporterCheck
    def parseConfiguration(self):
        # regular expression for php defines:
        #   define('KEY', 'VALUE');
        re_define = re.compile(
            r"^\s*define\("
            r"[\'\"]([^\'\"]+)[\'\"]"
            r"\s*,\s*"
            r"[\'\"]([^\'\"]+)[\'\"]"
            r"\s*\)\s*;"
        )
        # regular expression for php table prefix assignment:
        #   $table_prefix = 'PREFIX';
        re_table_prefix = re.compile(
            r"^\s*\$table_prefix\s*=\s*[\'\"]([^\'\"]+)[\'\"]\s*;"
        )

        with open(self.fsconfig) as f:
            lines = f.read()
            for line in lines.splitlines():

                m = re_define.match(line)
                if m:
                    key = m.group(1)
                    value = m.group(2)
                    if key == 'DB_NAME':
                        self.dbname = value
                        continue
                    if key == 'DB_HOST':
                        self.dbhost = value
                        continue
                    if key == 'DB_USER':
                        self.dbuser = value
                        continue
                    if key == 'DB_PASSWORD':
                        self.dbpass = value
                        continue
                    if key == 'DB_CHARSET':
                        self.dbcharset = value
                        continue

                m = re_table_prefix.match(line)
                if m:
                    self.dbprefix = m.group(1)
                    continue

        # regular expression for hostname with optional port
        re_hostname = r"^(?P<host>[^:]+):?(?P<port>[0-9]*)$"

        m = re.search(re_hostname, self.dbhost)
        if (m):
            host = m.group("host")
            port = m.group("port")
            self.dbhost = host
            self.dbport = int(port) if port else self.dbport


    @ReporterCheck
    def queryDatabase(self):
        connection = None
        try:
            connection = mysql.connect(
                db=self.dbname,
                host=self.dbhost,
                port=self.dbport,
                user=self.dbuser,
                password=self.dbpass,
                charset=self.dbcharset,
                use_unicode=True
            )
            cursor = connection.cursor()
            cursor.execute(
                "SELECT option_value FROM %soptions"
                " WHERE option_name = 'blogname'" % self.dbprefix
            )
            self.title = cursor.fetchone()[0]
            cursor.execute(
                "SELECT option_value FROM %soptions"
                " WHERE option_name = 'admin_email'" % self.dbprefix
            )
            self.email = cursor.fetchone()[0]

        except MySQLdb.Error as e:
            raise WPDatabaseError(self, repr(e))

        finally:
            if connection:
                connection.close()
