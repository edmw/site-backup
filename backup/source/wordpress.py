"""
##      ##  #######  ########  ########  ########  ########  ########  ######   ######
##  ##  ## ##     ## ##     ## ##     ## ##     ## ##     ## ##       ##    ## ##    ##
##  ##  ## ##     ## ##     ## ##     ## ##     ## ##     ## ##       ##       ##
##  ##  ## ##     ## ########  ##     ## ########  ########  ######    ######   ######
##  ##  ## ##     ## ##   ##   ##     ## ##        ##   ##   ##             ##       ##
##  ##  ## ##     ## ##    ##  ##     ## ##        ##    ##  ##       ##    ## ##    ##
 ###  ###   #######  ##     ## ########  ##        ##     ## ########  ######   ######
"""

import re
from pathlib import Path

import pymysql as mysql

from backup.reporter import reporter_check
from backup.utils import slugify

from ._base import Source, SourceConfig
from .errors import SourceError


class WPError(SourceError):
    def __init__(self, wp, message):
        super().__init__()
        self.wp = wp
        self.message = message

    def __str__(self):
        return f"WPError({self.message!r})"


class WPNotFoundError(WPError):
    pass


class WPDatabaseError(WPError):
    pass


class WP(Source):
    def __init__(self, path: Path, config: SourceConfig | None = None):
        super().__init__(path, path / "wp-config.php")

        if not self._check_configuration():
            raise WPNotFoundError(
                self, f"no wordpress instance found at '{self.fspath}'"
            )

        self._parse_configuration()
        self._build_configuration(config)

        title, email = self._query_database()
        self.title = title
        self.description = f"WordPress '{title}'"
        self.email = email

        self.slug = slugify(self.title)

    def _check_configuration(self) -> bool:
        return self.fspath.exists() and self.fsconfig.is_file()

    @reporter_check
    def _parse_configuration(self) -> None:
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
                    if key == "DB_NAME":
                        self.dbname = value
                        continue
                    if key == "DB_HOST":
                        self.dbhost = value
                        continue
                    if key == "DB_USER":
                        self.dbuser = value
                        continue
                    if key == "DB_PASSWORD":
                        self.dbpass = value
                        continue
                    if key == "DB_CHARSET":
                        self.dbcharset = value
                        continue

                m = re_table_prefix.match(line)
                if m:
                    self.dbprefix = m.group(1)
                    continue

        # regular expression for hostname with optional port
        re_hostname = r"^(?P<host>[^:]+):?(?P<port>[0-9]*)$"

        if self.dbhost:
            if m := re.search(re_hostname, self.dbhost):
                host = m.group("host")
                port = m.group("port")
                self.dbhost = host
                self.dbport = int(port) if port else self.dbport

    @reporter_check
    def _query_database(self) -> tuple[str, str]:
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
            cursor.execute(
                f"SELECT option_value FROM {self.dbprefix}options"
                f" WHERE option_name = 'blogname'"
            )
            if row := cursor.fetchone():
                title = row[0]
            else:
                raise WPNotFoundError(self, "blogname not found in options table")
            cursor.execute(
                f"SELECT option_value FROM {self.dbprefix}options"
                f" WHERE option_name = 'admin_email'"
            )
            if row := cursor.fetchone():
                email = row[0]
            else:
                raise WPNotFoundError(self, "email not found in options table")

            return title, email

        except mysql.Error as e:
            raise WPDatabaseError(self, repr(e)) from e

        finally:
            if connection:
                connection.close()
                connection.close()
