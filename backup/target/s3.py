# coding: utf-8

"""
Transfer a backup archive to a cloud service using the S3 API.

########    ###    ########   ######   ######## ########             ######   #######
   ##      ## ##   ##     ## ##    ##  ##          ##     ##        ##    ## ##     ##
   ##     ##   ##  ##     ## ##        ##          ##     ##        ##              ##
   ##    ##     ## ########  ##   #### ######      ##                ######   #######
   ##    ######### ##   ##   ##    ##  ##          ##     ##              ##        ##
   ##    ##     ## ##    ##  ##    ##  ##          ##     ##        ##    ## ##     ##
   ##    ##     ## ##     ##  ######   ########    ##                ######   #######
"""

import sys
import time

from collections import namedtuple

import boto
import boto.s3.connection
import socket

import humanfriendly

from backup.archive import Archive
from backup.reporter import Reporter, ReporterCheck, ReporterCheckResult
from backup.utils import formatkv


class S3Error(Exception):
    """Base Exception for errors while using a cloud service."""

    def __init__(self, s3, message):
        super(S3Error, self).__init__()
        self.s3 = s3
        self.message = message

    def __str__(self):
        return "S3Error({!r})".format(self.message)


class S3Result(namedtuple("Result", ["size", "duration"])):
    """Class for results of s3 operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        return "Result(size={}, duration={})".format(
            humanfriendly.format_size(self.size),
            humanfriendly.format_timespan(self.duration),
        )


class S3ThinningResult(
    namedtuple("ThinningResult", ["archivesRetained", "archivesDeleted"])
):
    """Class for results of s3 thinning operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        return "Result(retained={}, deleted={})".format(
            self.archivesRetained, self.archivesDeleted
        )


class S3(Reporter, object):
    """Class using a cloud service with the S3 API to transfer an archive.

    To use initialize with the configuration of a compatible cloud service
    and call transferArchive with an archive object.

    If stdout is bound to a console a progress indicator will be displayed.

    Uses the reporter mixin and decorators to generate a results report.

    """

    def __init__(self, host, accesskey, secretkey, bucket):
        super(S3, self).__init__()

        self.host = host
        self.accesskey = accesskey
        self.secretkey = secretkey
        self.bucket = bucket

        self.label = "S3"
        self.description = "{} Service at {}".format(self.label, self.host)

        self.connection = boto.connect_s3(
            aws_access_key_id=self.accesskey,
            aws_secret_access_key=self.secretkey,
            host=self.host,
            calling_format=boto.s3.connection.OrdinaryCallingFormat(),
        )

    def __str__(self):
        return formatkv(
            [
                ("S3(Host)", self.host),
                ("S3(Bucket)", self.bucket),
            ],
            title="S3",
        )

    def boto_progress_start(self):
        self.progress_stime = 0
        self.progress_etime = 0

    def boto_progress_duration(self):
        return int(self.progress_etime - self.progress_stime)

    def boto_progress(self, complete, total):
        """Progress handler for boto library.

        Prints a progress indicator to the console.

        If stdout is NOT bound to a console nothing will be displayed.

        """
        if sys.stdin.isatty():
            if complete == 0:
                self.progress_stime = time.monotonic()
                sys.stdout.write("|" + "-" * 10 + "|")
                sys.stdout.write("\n")
                sys.stdout.write("|")
            sys.stdout.write(".")
            if complete == total:
                self.progress_etime = time.monotonic()
                sys.stdout.write("|")
                sys.stdout.write("\n")
                seconds = self.boto_progress_duration()
                sys.stdout.write("{} seconds".format(seconds))
                sys.stdout.write("\n")
            sys.stdout.flush()

    def listArchives(self, label=None):
        try:
            archives = []

            bucket = self.connection.get_bucket(self.bucket)
            for key in bucket.list():
                try:
                    archive = Archive.fromfilename(key.name, check_label=label)
                except ValueError as e:
                    raise S3Error(self, str(e)) from e

                if archive:
                    archives.append(archive)

            return archives

        except boto.exception.S3ResponseError as e:
            raise S3Error(self, repr(e)) from e
        except boto.exception.BotoServerError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e

    @ReporterCheckResult
    def transferArchive(self, archive, dry=False):
        """Transfers the given archive to the configured cloud service.

        If the configured bucket does not exist it will be created.

        Returns the size of the transferred file on success.

        """
        try:
            self.boto_progress_start()

            if self.connection.lookup(self.bucket):
                bucket = self.connection.get_bucket(self.bucket)
            else:
                bucket = self.connection.create_bucket(self.bucket)

            if not dry:
                key = bucket.new_key(archive.filename)
                key.set_contents_from_filename(
                    archive.filename, cb=self.boto_progress, num_cb=10
                )
                return S3Result(key.size, self.boto_progress_duration())

            else:
                return S3Result(0, 0)

        except boto.exception.S3ResponseError as e:
            raise S3Error(self, repr(e)) from e
        except boto.exception.BotoServerError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e

    @ReporterCheckResult
    def performThinning(self, label, thinArchives, dry=False):
        """Deletes obsolete archives from the configured cloud service.

        Collects all archives in the configured bucket and decides which
        archives to keep according the given strategy. Then deletes the
        obsolete archives.

        """
        try:
            archives = self.listArchives(label)

            toRetain, toDelete = thinArchives(archives)

            bucket = self.connection.get_bucket(self.bucket)

            if not dry:
                for archive in toDelete:
                    bucket.delete_key(archive.filename)
                return S3ThinningResult(len(toRetain), len(toDelete))

            else:
                return S3ThinningResult(len(toRetain), len(toDelete))

        except boto.exception.S3ResponseError as e:
            raise S3Error(self, repr(e)) from e
        except boto.exception.BotoServerError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e
