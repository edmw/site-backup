#!/usr/bin/python
# coding: utf-8
#
# Dependencies:
# pip install MySQL-python
# pip install boto3
# pip install humanfriendly
#
# Dependencies (2.6):
# pip install argparse

"""
Script to backup a Wordpress Blog instance.

Try 'python sitebackup.py -h' for usage information.
"""

import sys, os, os.path
import argparse
import logging

from backup import Backup
from backup.source.wordpress import WP, WPError
from backup.target.s3 import S3

##     ##    ###    #### ##    ##
###   ###   ## ##    ##  ###   ##
#### ####  ##   ##   ##  ####  ##
## ### ## ##     ##  ##  ## ## ##
##     ## #########  ##  ##  ####
##     ## ##     ##  ##  ##   ###
##     ## ##     ## #### ##    ##

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

def dir_argument(string):
    """ Helper for argparse
    to verify the given argument is an existing directory
    """
    if not os.path.isdir(string):
        raise argparse.ArgumentTypeError(
                "%r is not an existing directory" % string
            )
    return string

class ArgumentParser(argparse.ArgumentParser):

    def print_help(self):
        import humanfriendly.terminal
        humanfriendly.terminal.usage(self.format_help())

def main(args=None):
    """ Main: parse arguments and run. """

    parser = ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('path', action='store',
        type=dir_argument,
        help='path to wordpress instance')
    parser.add_argument('-v', '--verbose', action='store_const',
        dest='loglevel', const=logging.INFO, default=logging.WARN,
        help='enable log messages')
    parser.add_argument('-d', '--debug', action='store_const',
        dest='loglevel', const=logging.DEBUG, default=logging.WARN,
        help='enable debug messages')
    parser.add_argument('-q', '--quiet', action='store_true',
        help='do not print status messages')
    parser.add_argument('--database', action='store_true',
        help='backup wordpress database')
    parser.add_argument('--filesystem', action='store_true',
        help='backup wordpress filesystem')

    group_db = parser.add_argument_group(
        'database backup options', '')
    group_db.add_argument('--db', action='store', metavar='NAME',
        help='name for wordpress db')
    group_db.add_argument('--dbhost', action='store', metavar='HOST',
        help='hostname for wordpress db')
    group_db.add_argument('--dbport', action='store', metavar='PORT',
        type=int,
        help='portnumber for wordpress db')
    group_db.add_argument('--dbuser', action='store', metavar='USER',
        help='username for wordpress db')
    group_db.add_argument('--dbpass', action='store', metavar='PASS',
        help='password for wordpress db')
    group_db.add_argument('--dbprefix', action='store', metavar='PREFIX',
        help='prefix for table names in wordpress db')

    group_local = parser.add_argument_group(
        'local target',
        'options for storing the backup archive on local filesystem')
    group_local.add_argument('--attic', action='store', metavar='DIR',
        nargs='?', const='.', default=None,
        type=dir_argument,
        help='local directory to store backup archive')

    group_s3 = parser.add_argument_group(
        's3 target',
        'options for copying the backup archive to a s3 service')
    group_s3.add_argument('--s3', action='store', metavar='HOST',
        help='host for s3 server')
    group_s3.add_argument('--s3accesskey', action='store', metavar='KEY',
        help='access key for s3 server')
    group_s3.add_argument('--s3secretkey', action='store', metavar='KEY',
        help='secret key for s3 server')
    group_s3.add_argument('--s3bucket', action='store', metavar='BUCKET',
        help='bucket at s3 server')

    group_report = parser.add_argument_group(
        'report options', '')
    group_report.add_argument('--mail-from', action='store', metavar='MAIL',
        help='sender address for report mails')
    group_report.add_argument('--mail-to-admin', action='store_true',
        help='send report to wordpress administrator')

    arguments = parser.parse_args() if args == None else parser.parse_args(args)

    # logging
    logging.basicConfig(
        level=arguments.loglevel,
        format='%(asctime)s - %(filename)s:%(funcName)s - %(levelname)s - %(message)s'
    )

    # initialize source

    try:
        source = WP(
            unicode(arguments.path),
            dbname=arguments.db,
            dbhost=arguments.dbhost,
            dbport=arguments.dbport,
            dbuser=arguments.dbuser,
            dbpass=arguments.dbpass,
            dbprefix=arguments.dbprefix
        )
    except WPError as exception:
        print exception
        sys.exit(1)

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

    # initialize options

    mailto = source.email if arguments.mail_to_admin else None
    mailfrom = arguments.mail_from

    # initialize and execute backup

    backup = Backup(source, mailto, mailfrom, quiet=arguments.quiet)
    backup.execute(
        targets=targets,
        database=arguments.database,
        filesystem=arguments.filesystem,
        attic=arguments.attic
    )

if __name__ == "__main__":
    main()
