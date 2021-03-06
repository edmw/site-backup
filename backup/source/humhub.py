# coding: utf-8

"""
    ##     ## ##     ## ##     ## ##     ## ##     ## ########  
    ##     ## ##     ## ###   ### ##     ## ##     ## ##     ## 
    ##     ## ##     ## #### #### ##     ## ##     ## ##     ## 
    ######### ##     ## ## ### ## ######### ##     ## ########  
    ##     ## ##     ## ##     ## ##     ## ##     ## ##     ## 
    ##     ## ##     ## ##     ## ##     ## ##     ## ##     ## 
    ##     ##  #######  ##     ## ##     ##  #######  ########  
"""

import os
import re
import logging

from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult
from backup.utils import slugify, formatkv

import pymysql as mysql

from phply import phplex
from phply.phpparse import make_parser
from phply.phpast import *

from .error import SourceError

class HHError(SourceError):
    def __init__(self, hh, message):
        super(HHError, self).__init__()
        self.hh = hh
        self.message = message

    def __str__(self):
        return "HHError({!r})".format(self.message)


class HHNotFoundError(HHError):
    pass


class HHConfigError(HHError):
    pass


class HHDatabaseError(HHError):
    pass


class HH(Reporter, object):
    def __init__(self, path, **kwargs):
        super(HH, self).__init__()

        self.fspath = path
        self.fsconfig = os.path.join(path, "protected/config/dynamic.php")

        self.dbname = None
        self.dbhost = None
        self.dbport = 3306
        self.dbprefix = None
        self.dbuser = None
        self.dbpass = None
        self.dbcharset = "utf8mb4"

        self.title = None

        self.slug = None

        # check preconditions
        if not self.checkConfig():
            raise HHNotFoundError(
                self, "no humhub instance found at '{}'".format(self.fspath)
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

        self.description = "Humhub '{}'".format(self.title)
        self.slug = slugify(self.title)

    def checkConfig(self):
        return os.path.exists(self.fspath) and os.path.isfile(self.fsconfig)

    def __str__(self):
        return formatkv(
            [
                ("Slug", self.slug),
                ("WP(Title)", self.title),
                ("DB(Name)", self.dbname),
                ("DB(Host)", self.dbhost),
                ("DB(Port)", self.dbport),
                ("DB(Prefix)", self.dbprefix),
                ("DB(User)", self.dbuser),
                ("DB(Pass)", "*******" if self.dbpass else "-"),
            ],
            title="HUMHUB",
        )

    @ReporterCheck
    def parseConfiguration(self):
        dns_re = re.compile(r"^mysql:host=([^;]+);dbname=(.+)$")

        def array_get(array, key):
            if isinstance(array, Array):
                for element in array.nodes:
                    if element.key == key:
                        return element.value
            return None

        parser = make_parser()
        with open(self.fsconfig) as f:
            ast = parser.parse(f.read(), lexer=phplex.lexer.clone())
            if ast and isinstance(ast[0], Return):
                r = ast[0].node
                self.title = array_get(r, "name")
                if not self.title:
                    raise HHConfigError(self, "no title given")
                logging.debug("HH.parseConfiguration: title={}".format(self.title))
                components = array_get(r, "components")
                if components:
                    db = array_get(components, "db")
                    if db:
                        dsn = array_get(db, "dsn")
                        if dsn:
                            logging.debug("HH.parseConfiguration: dsn={}".format(dsn))
                            m = dns_re.match(dsn)
                            if m:
                                self.dbhost = m.group(1)
                                self.dbname = m.group(2)
                                self.dbuser = array_get(db, "username")
                                self.dbpass = array_get(db, "password")
                if not self.dbhost or not self.dbname:
                    raise HHConfigError(self, "no database given")
                
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
                "SELECT value FROM setting"
                " WHERE name = 'name'"
            )
            self.title = cursor.fetchone()[0]
            logging.debug("HH.queryDatabase: title={}".format(self.title))
            cursor.execute(
                "SELECT value FROM setting"
                " WHERE name = 'mailer.systemEmailAddress'"
            )
            self.email = cursor.fetchone()[0]
            logging.debug("HH.queryDatabase: email={}".format(self.email))

        except mysql.Error as e:
            raise HHDatabaseError(self, repr(e))

        finally:
            if connection:
                connection.close()
