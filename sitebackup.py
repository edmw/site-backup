#!/usr/bin/python

"""
Script to backup a Wordpress Blog instance.

Try 'python sitebackup.py -h' for usage information.
"""

import argparse
import functools
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backup import Backup
from backup.source import SourceFactory, SourceMultipleError
from backup.target.s3 import S3
from backup.thinning import ThinningStrategy
from backup.utils.mail import Mailer, Recipient, Sender

"""
    ##     ##    ###    #### ##    ##
    ###   ###   ## ##    ##  ###   ##
    #### ####  ##   ##   ##  ####  ##
    ## ### ## ##     ##  ##  ## ## ##
    ##     ## #########  ##  ##  ####
    ##     ## ##     ##  ##  ##   ###
    ##     ## ##     ## #### ##    ##
"""


DESCRIPTION = """
This script creates a backup of a Wordpress Blog instance.

It generates a compressed tar archive containing a dump
of the wordpress database and a copy of the wordpress filesystem.
"""

EPILOG = """
This script will try to load the wordpress configuration file at
the given path and read the database configuration for the given
wordpress instance from that file.

The database parameters from the configuration file can be overwritten
by specifing the correspondent command line options.

"""


def value_argument(string: str, callee: Callable[[str], Any] | None = None) -> Any:
    """Helper for argparse
    to create a value from the given argument using the given function.
    """
    if callee:
        try:
            return callee(string)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e)) from e
    raise argparse.ArgumentTypeError("Internal Error")


def dir_argument(string: str) -> str:
    """Helper for argparse
    to verify the given argument is an existing directory.
    """
    if not os.path.isdir(string):
        raise argparse.ArgumentTypeError(f"{string!r} is not an existing directory")
    return string


class ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with human friendly help."""

    def print_help(self, file: Any = None) -> None:
        """Print human friendly help."""
        import humanfriendly.terminal

        if file is None:
            humanfriendly.terminal.usage(self.format_help())
        else:
            super().print_help(file=file)


def main(args: list[str] | None = None) -> None:
    """Main: parse arguments and run."""

    parser = ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path", action="store", type=dir_argument, help="path to wordpress instance"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
        default=logging.WARN,
        help="enable log messages",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARN,
        help="enable debug messages",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="do not print status messages"
    )
    parser.add_argument(
        "--dry",
        action="store_true",
        help="perform dry run: do not store or delete any archives",
    )
    parser.add_argument(
        "--database", action="store_true", help="backup wordpress database"
    )
    parser.add_argument(
        "--filesystem", action="store_true", help="backup wordpress filesystem"
    )
    parser.add_argument(
        "--thinning",
        action="store",
        metavar="STRATEGY",
        type=functools.partial(value_argument, callee=ThinningStrategy.from_argument),
        help="thin out backups at targets (except local target) using the specified strategy",
    )

    group_db = parser.add_argument_group("database backup options", "")
    group_db.add_argument(
        "--db", action="store", metavar="NAME", help="name for wordpress db"
    )
    group_db.add_argument(
        "--dbhost", action="store", metavar="HOST", help="hostname for wordpress db"
    )
    group_db.add_argument(
        "--dbport",
        action="store",
        metavar="PORT",
        type=int,
        help="portnumber for wordpress db",
    )
    group_db.add_argument(
        "--dbuser", action="store", metavar="USER", help="username for wordpress db"
    )
    group_db.add_argument(
        "--dbpass", action="store", metavar="PASS", help="password for wordpress db"
    )
    group_db.add_argument(
        "--dbprefix",
        action="store",
        metavar="PREFIX",
        help="prefix for table names in wordpress db",
    )

    group_local = parser.add_argument_group(
        "local target", "options for storing the backup archive on local filesystem"
    )
    group_local.add_argument(
        "--attic",
        action="store",
        metavar="DIR",
        nargs="?",
        const=".",
        default=None,
        type=dir_argument,
        help="local directory to store backup archive",
    )

    group_s3 = parser.add_argument_group(
        "s3 target", "options for copying the backup archive to a s3 service"
    )
    group_s3.add_argument(
        "--s3", action="store", metavar="HOST", help="host for s3 server"
    )
    group_s3.add_argument(
        "--s3accesskey", action="store", metavar="KEY", help="access key for s3 server"
    )
    group_s3.add_argument(
        "--s3secretkey", action="store", metavar="KEY", help="secret key for s3 server"
    )
    group_s3.add_argument(
        "--s3bucket", action="store", metavar="BUCKET", help="bucket at s3 server"
    )

    group_report = parser.add_argument_group("report options", "")
    group_report.add_argument(
        "--mail-from",
        action="store",
        metavar="MAIL",
        help="sender address for report mails",
    )
    group_report.add_argument(
        "--mail-to-admin",
        action="store_true",
        help="send report to wordpress administrator",
    )
    group_report.add_argument(
        "--mail-to",
        action="store",
        metavar="MAIL",
        help="recipient address for report mails",
    )

    arguments = parser.parse_args() if args is None else parser.parse_args(args)

    # logging
    import coloredlogs

    coloredlogs.install(
        level=arguments.loglevel,
        format="%(asctime)s - %(filename)s:%(funcName)s - %(levelname)s - %(message)s",
        isatty=True,
    )

    # initialize source

    try:
        source = SourceFactory(Path(arguments.path)).create(
            {
                "dbname": arguments.db,
                "dbhost": arguments.dbhost,
                "dbport": arguments.dbport,
                "dbuser": arguments.dbuser,
                "dbpass": arguments.dbpass,
                "dbprefix": arguments.dbprefix,
            }
        )
    except SourceMultipleError as exception:
        logging.error(f"Site-Backup: {exception}")
        sys.exit(1)
    else:
        logging.info(f"Site-Backup: Source is {source}")

    # initialize targets

    targets = []

    if arguments.s3:
        # transfer backup to s3 service
        s3target = S3(
            arguments.s3,
            arguments.s3accesskey,
            arguments.s3secretkey,
            arguments.s3bucket if arguments.s3bucket else source.slug,
        )
        targets.append(s3target)

    for target in targets:
        logging.info(f"Site-Backup: Target is {target}")

    # initialize options

    mailer = Mailer() if arguments.mail_from else None
    if mailer:
        if arguments.mail_to_admin:
            mailer.add_recipient(Recipient(source.email))
        if arguments.mail_to:
            mailer.add_recipient(Recipient(arguments.mail_to))
        mailer.set_sender(Sender(arguments.mail_from))

    # initialize and execute backup

    backup = Backup(source, mailer=mailer, quiet=arguments.quiet)
    backup.execute(
        targets=targets,
        database=arguments.database,
        filesystem=arguments.filesystem,
        thinning=arguments.thinning,
        attic=arguments.attic,
        dry=arguments.dry,
    )

    if backup.error:
        logging.error(f"Site-Backup: {backup.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
