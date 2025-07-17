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

import os
import socket
import sys
import time
from collections import namedtuple

import boto3
import humanfriendly
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    SSLError,
)

from backup.archive import Archive
from backup.reporter import Reporter, reporter_check_result
from backup.utils import formatkv


class S3Error(Exception):
    """Base Exception for errors while using a cloud service."""

    def __init__(self, s3, message):
        super().__init__()
        self.s3 = s3
        self.message = message

    def __str__(self):
        return f"S3Error({self.message!r})"


class S3Result(namedtuple("Result", ["size", "duration"])):
    """Class for results of s3 operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        size = humanfriendly.format_size(self.size)
        duration = humanfriendly.format_timespan(self.duration)
        return f"Result(size={size}, duration={duration})"


class S3ThinningResult(
    namedtuple("ThinningResult", ["archivesRetained", "archivesDeleted"])
):
    """Class for results of s3 thinning operations with proper formatting."""

    __slots__ = ()

    def __str__(self):
        return (
            f"Result(retained={self.archivesRetained}, deleted={self.archivesDeleted})"
        )


class S3(Reporter):
    """Class using a cloud service with the S3 API to transfer an archive.

    To use initialize with the configuration of a compatible cloud service
    and call transferArchive with an archive object.

    If stdout is bound to a console a progress indicator will be displayed.

    Uses the reporter mixin and decorators to generate a results report.

    """

    def __init__(self, host, accesskey, secretkey, bucket, port=None, is_secure=True):
        super().__init__()

        self.host = host
        self.port = port
        self.accesskey = accesskey
        self.secretkey = secretkey
        self.bucket = bucket

        self.label = "S3"
        self.description = f"{self.label} Service at {self.host}"

        # Configure endpoint URL for custom S3-compatible services
        if port:
            endpoint_url = f"{'https' if is_secure else 'http'}://{host}:{port}"
        else:
            endpoint_url = f"{'https' if is_secure else 'http'}://{host}"

        # Initialize boto3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.accesskey,
            aws_secret_access_key=self.secretkey,
            endpoint_url=endpoint_url,
            use_ssl=is_secure,
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
                sys.stdout.write(f"{seconds} seconds")
                sys.stdout.write("\n")
            sys.stdout.flush()

    def list_archives(self, label=None):
        try:
            archives = []

            # List objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket)

            if "Contents" in response:
                for obj in response["Contents"]:
                    try:
                        archive = Archive.fromfilename(obj["Key"], check_label=label)
                    except ValueError as e:
                        raise S3Error(self, str(e)) from e

                    if archive:
                        archives.append(archive)

            return archives

        except ClientError as e:
            raise S3Error(self, repr(e)) from e
        except NoCredentialsError as e:
            raise S3Error(self, repr(e)) from e
        except EndpointConnectionError as e:
            raise S3Error(self, repr(e)) from e
        except SSLError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e

    @reporter_check_result
    def transfer_archive(self, archive, dry=False):
        """Transfers the given archive to the configured cloud service.

        If the configured bucket does not exist it will be created.

        Returns the size of the transferred file on success.

        """
        try:
            self.boto_progress_start()

            # Check if bucket exists, create if not
            try:
                self.s3_client.head_bucket(Bucket=self.bucket)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    # Bucket doesn't exist, create it
                    self.s3_client.create_bucket(Bucket=self.bucket)
                else:
                    raise

            if not dry:
                # Upload the file with progress callback
                file_size = os.path.getsize(archive.filename)

                def progress_callback(bytes_transferred):
                    self.boto_progress(bytes_transferred, file_size)

                self.s3_client.upload_file(
                    archive.filename,
                    self.bucket,
                    archive.filename,
                    Callback=progress_callback,
                )

                self.progress_etime = time.monotonic()
                return S3Result(file_size, self.boto_progress_duration())
            else:
                return S3Result(0, 0)

        except ClientError as e:
            raise S3Error(self, repr(e)) from e
        except NoCredentialsError as e:
            raise S3Error(self, repr(e)) from e
        except EndpointConnectionError as e:
            raise S3Error(self, repr(e)) from e
        except SSLError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e

    @reporter_check_result
    def perform_thinning(self, label, thin_archives, dry=False):
        """Deletes obsolete archives from the configured cloud service.

        Collects all archives in the configured bucket and decides which
        archives to keep according the given strategy. Then deletes the
        obsolete archives.

        """
        try:
            archives = self.list_archives(label)

            to_retain, to_delete = thin_archives(archives)

            if not dry:
                for archive in to_delete:
                    self.s3_client.delete_object(
                        Bucket=self.bucket, Key=archive.filename
                    )
                return S3ThinningResult(len(to_retain), len(to_delete))
            else:
                return S3ThinningResult(len(to_retain), len(to_delete))

        except ClientError as e:
            raise S3Error(self, repr(e)) from e
        except NoCredentialsError as e:
            raise S3Error(self, repr(e)) from e
        except EndpointConnectionError as e:
            raise S3Error(self, repr(e)) from e
        except SSLError as e:
            raise S3Error(self, repr(e)) from e
        except socket.gaierror as e:
            raise S3Error(self, repr(e)) from e
