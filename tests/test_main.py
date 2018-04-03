# coding: utf-8

import pytest  # noqa: 401
from mock import mock, patch

from sitebackup import main
from backup.source.wordpress import WPError
from backup.utils.mail import Sender, Recipient


def testHelp():
    with pytest.raises(SystemExit) as exceptioninfo:
        main(["-h", ])
    assert exceptioninfo.value.code == 0


def setupWP(mock):
    m = mock()
    mock.reset_mock()
    return m


@patch('sitebackup.os.path.isdir', return_value=True)
@patch('sitebackup.Mailer')
@patch('sitebackup.WP')
@patch('sitebackup.Backup')
def testWithNoArguments(patchedBackup, patchedWP, patchedMailer, *args):
    mailer = patchedMailer()
    wp = setupWP(patchedWP)
    bup = patchedBackup()
    main(["path_for_test_with_no_arguments"])
    patchedWP.assert_called_once_with(
        'path_for_test_with_no_arguments',
        dbhost=None,
        dbname=None,
        dbpass=None,
        dbport=None,
        dbprefix=None,
        dbuser=None
    )
    # calls to backup
    patchedBackup.assert_called_with(wp, mailer=mailer, quiet=False)
    bup.execute.assert_called_once_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False
    )


@patch('sitebackup.os.path.isdir', return_value=True)
@patch('sitebackup.Mailer')
@patch('sitebackup.WP')
@patch('sitebackup.Backup')
def testWithArguments(patchedBackup, patchedWP, patchedMailer, *args):
    mailer = patchedMailer()
    wp = setupWP(patchedWP)
    wp.email = "michael@localhost"
    bup = patchedBackup()

    # test 1: overwrite database configuration
    main([
        "--db=wpdb",
        "--dbhost=localhost",
        "--dbuser=michael",
        "--dbpass=123456",
        "--dbprefix=wp",
        "path_for_test_with_db_arguments"
    ])
    # configuration should be taken from arguments
    patchedWP.assert_called_once_with(
        'path_for_test_with_db_arguments',
        dbhost='localhost',
        dbname='wpdb',
        dbpass='123456',
        dbport=None,
        dbprefix='wp',
        dbuser='michael'
    )
    # calls to backup
    patchedBackup.assert_called_with(wp, mailer=mailer, quiet=False)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False
    )

    # test 2: configure mail reporting
    main([
        "-q",
        "--mail-to-admin",
        "--mail-from=admin@localhost",
        "--mail-to=example@localhost",
        "."
    ])
    # configuration should be taken from arguments
    mailer.setSender.assert_called_with(
        Sender("admin@localhost")
    )
    assert[
        mock.call(Recipient("michael@localhost")),
        mock.call(Recipient("example@localhost"))
    ] == mailer.addRecipient.mock_calls
    # calls to backup
    patchedBackup.assert_called_with(wp, mailer=mailer, quiet=True)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False
    )

    # test 3: switch on database processing and configure attic with no parameter
    main([
        "--database",
        "--attic",
        "--",
        "."
    ])
    # calls to backup
    patchedBackup.assert_called_with(wp, mailer=mailer, quiet=False
    )
    bup.execute.assert_called_with(
        targets=[],
        database=True,
        filesystem=False,
        thinning=None,
        attic=".",
        dry=False
    )

    # test 4: switch on filesystem processing and configure attic with parameter
    main([
        "--filesystem",
        "--attic=path_to_attic",
        "."
    ])
    # calls to backup
    patchedBackup.assert_called_with(wp, mailer=mailer, quiet=False
    )
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=True,
        thinning=None,
        attic="path_to_attic",
        dry=False
    )


@patch('sitebackup.os.path.isdir', return_value=True)
@patch('sitebackup.WP')
@patch('sitebackup.S3')
@patch('sitebackup.Backup')
def testWithS3Arguments(patchedBackup, patchedS3, patchedWP, *args):
    wp = setupWP(patchedWP)
    wp.slug = "wordpress-instance-to-backup"
    s3 = patchedS3()
    bup = patchedBackup()

    # test: configure s3 targets with bucket
    main([
        "--s3=s3.host.com",
        "--s3accesskey=ABCDEF",
        "--s3secretkey=000000",
        "--s3bucket=bucket",
        "."
    ])
    patchedS3.assert_called_with(
        "s3.host.com", "ABCDEF", "000000", "bucket"
    )
    bup.execute.assert_called_once_with(
        targets=[s3],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False
    )

    # test: configure s3 target with no bucket (bucket should be wp.slug)
    main([
        "--s3=s3.host.com",
        "--s3accesskey=ABCDEF",
        "--s3secretkey=000000",
        "."
    ])
    patchedS3.assert_called_with(
        "s3.host.com", "ABCDEF", "000000", "wordpress-instance-to-backup"
    )
    bup.execute.assert_called_with(
        targets=[s3],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False
    )
