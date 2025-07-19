"""
##     ## ##     ## ##     ## ##     ## ##     ## ########
##     ## ##     ## ###   ### ##     ## ##     ## ##     ##
##     ## ##     ## #### #### ##     ## ##     ## ##     ##
######### ##     ## ## ### ## ######### ##     ## ########
##     ## ##     ## ##     ## ##     ## ##     ## ##     ##
##     ## ##     ## ##     ## ##     ## ##     ## ##     ##
##     ##  #######  ##     ## ##     ##  #######  ########
"""

import logging
import os
import re
from pathlib import Path

import pymysql as mysql
from phply import phplex
from phply.phpast import Array, Return
from phply.phpparse import make_parser

from backup.reporter import reporter_check
from backup.source._base import BaseSource, SourceConfig
from backup.utils import slugify

from .errors import SourceError


class HHError(SourceError):
    def __init__(self, hh, message):
        super().__init__()
        self.hh = hh
        self.message = message

    def __str__(self):
        return f"HHError({self.message!r})"


class HHNotFoundError(HHError):
    pass


class HHConfigError(HHError):
    pass


class HHDatabaseError(HHError):
    pass


class HH(BaseSource):
    def __init__(self, path: Path, config: SourceConfig | None = None):
        super().__init__(path, path / "protected/config/dynamic.php")

        if not self.check_configuration():
            raise HHNotFoundError(self, f"no humhub instance found at '{self.fspath}'")

        self.parse_configuration()

        if config:
            self.dbname = config.get("dbname", self.dbname)
            self.dbhost = config.get("dbhost", self.dbhost)
            self.dbport = config.get("dbport", self.dbport)
            self.dbuser = config.get("dbuser", self.dbuser)
            self.dbpass = config.get("dbpass", self.dbpass)
            self.dbprefix = config.get("dbprefix", self.dbprefix)

        self.title, self.description, self.email = self.query_database()
        self.slug = slugify(self.title)

    def check_configuration(self):
        return os.path.exists(self.fspath) and os.path.isfile(self.fsconfig)

    @reporter_check
    def parse_configuration(self):
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
                logging.debug("HH.parseConfiguration: title=%s", self.title)
                components = array_get(r, "components")
                if components:
                    db = array_get(components, "db")
                    if db:
                        dsn = array_get(db, "dsn")
                        if dsn:
                            logging.debug("HH.parseConfiguration: dsn=%", dsn)
                            m = dns_re.match(dsn)
                            if m:
                                self.dbhost = m.group(1)
                                self.dbname = m.group(2)
                                self.dbuser = array_get(db, "username")
                                self.dbpass = array_get(db, "password")
                if not self.dbhost or not self.dbname:
                    raise HHConfigError(self, "no database given")

    @reporter_check
    def query_database(self) -> tuple[str, str, str]:
        assert self.dbname, "database name not set"
        assert self.dbhost, "database host not set"
        assert self.dbuser, "database user not set"
        assert self.dbpass, "database password not set"
        assert self.dbprefix, "database prefix not set"

        connection = None
        try:
            connection = mysql.connect(
                db=self.dbname,
                host=self.dbhost,
                port=self.dbport,
                user=self.dbuser,
                password=self.dbpass,
                charset=self.dbcharset,
            )
            cursor = connection.cursor()
            cursor.execute("SELECT value FROM setting" " WHERE name = 'name'")
            if row := cursor.fetchone():
                title = row[0]
            else:
                raise HHNotFoundError(self, "title not found in setting table")
            logging.debug("HH.queryDatabase: title=%s", title)
            cursor.execute(
                "SELECT value FROM setting" " WHERE name = 'mailer.systemEmailAddress'"
            )
            if row := cursor.fetchone():
                email = row[0]
            else:
                raise HHNotFoundError(self, "email not found in setting table")
            logging.debug("HH.queryDatabase: email=%s", email)

            return title, f"Humhub '{title}'", email

        except mysql.Error as e:
            raise HHDatabaseError(self, repr(e)) from e

        finally:
            if connection:
                connection.close()
