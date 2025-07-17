from unittest import mock
from unittest.mock import patch

import pytest

from backup.utils.mail import Recipient, Sender
from sitebackup import main


def test_help():
    with pytest.raises(SystemExit) as exceptioninfo:
        main(
            [
                "-h",
            ]
        )
    assert exceptioninfo.value.code == 0


def setup_source(mock_class):
    m = mock_class()
    return m


@patch("sitebackup.os.path.isdir", return_value=True)
@patch("sitebackup.Mailer")
@patch("sitebackup.SourceFactory")
@patch("sitebackup.Backup")
def test_with_no_arguments(
    mock_backup, mock_source_factory, _mock_mailer, _mock_os_isdir
):
    # Mock SourceFactory and its create method
    source_factory = mock_source_factory.return_value
    source = setup_source(mock.Mock)
    source_factory.create.return_value = source

    bup = mock_backup()
    bup.error = None  # Ensure no error to prevent sys.exit(1)

    main(["path_for_test_with_no_arguments"])

    mock_source_factory.assert_called_once_with("path_for_test_with_no_arguments")
    source_factory.create.assert_called_once_with(
        dbhost=None,
        dbname=None,
        dbpass=None,
        dbport=None,
        dbprefix=None,
        dbuser=None,
    )
    # calls to backup (mailer is None because no --mail-from argument)
    mock_backup.assert_called_with(source, mailer=None, quiet=False)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    )


@patch("sitebackup.os.path.isdir", return_value=True)
@patch("sitebackup.Mailer")
@patch("sitebackup.SourceFactory")
@patch("sitebackup.Backup")
def test_with_arguments(mock_backup, mock_source_factory, mock_mailer, _mock_os_isdir):
    mailer = mock_mailer()

    # Mock SourceFactory and its create method
    source_factory = mock_source_factory.return_value
    source = setup_source(mock.Mock)
    source.email = "michael@localhost"
    source_factory.create.return_value = source

    bup = mock_backup()
    bup.error = None  # Ensure no error to prevent sys.exit(1)

    # test 1: overwrite database configuration
    main(
        [
            "--db=wpdb",
            "--dbhost=localhost",
            "--dbuser=michael",
            "--dbpass=123456",
            "--dbprefix=wp",
            "path_for_test_with_db_arguments",
        ]
    )
    # configuration should be taken from arguments
    mock_source_factory.assert_called_once_with("path_for_test_with_db_arguments")
    source_factory.create.assert_called_once_with(
        dbhost="localhost",
        dbname="wpdb",
        dbpass="123456",
        dbport=None,
        dbprefix="wp",
        dbuser="michael",
    )
    # calls to backup (mailer is None because no --mail-from argument)
    mock_backup.assert_called_with(source, mailer=None, quiet=False)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    )

    # test 2: configure mail reporting
    main(
        [
            "-q",
            "--mail-to-admin",
            "--mail-from=admin@localhost",
            "--mail-to=example@localhost",
            ".",
        ]
    )
    # configuration should be taken from arguments
    mailer.set_sender.assert_called_with(Sender("admin@localhost"))
    assert [
        mock.call(Recipient("michael@localhost")),
        mock.call(Recipient("example@localhost")),
    ] == mailer.add_recipient.mock_calls
    # calls to backup (now mailer should be provided)
    mock_backup.assert_called_with(source, mailer=mailer, quiet=True)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    )

    # test 3: switch on database processing and configure attic with no parameter
    main(["--database", "--attic", "--", "."])
    # calls to backup
    mock_backup.assert_called_with(source, mailer=None, quiet=False)
    bup.execute.assert_called_with(
        targets=[], database=True, filesystem=False, thinning=None, attic=".", dry=False
    )

    # test 4: switch on filesystem processing and configure attic with parameter
    main(["--filesystem", "--attic=path_to_attic", "."])
    # calls to backup
    mock_backup.assert_called_with(source, mailer=None, quiet=False)
    bup.execute.assert_called_with(
        targets=[],
        database=False,
        filesystem=True,
        thinning=None,
        attic="path_to_attic",
        dry=False,
    )


@patch("sitebackup.os.path.isdir", return_value=True)
@patch("sitebackup.SourceFactory")
@patch("sitebackup.S3")
@patch("sitebackup.Backup")
def test_with_s3_arguments(mock_backup, mock_s3, mock_source_factory, _mock_os_isdir):
    # Mock SourceFactory and its create method
    source_factory = mock_source_factory.return_value
    source = setup_source(mock.Mock)
    source.slug = "wordpress-instance-to-backup"
    source_factory.create.return_value = source

    s3 = mock_s3()
    bup = mock_backup()
    bup.error = None  # Ensure no error to prevent sys.exit(1)

    # test: configure s3 targets with bucket
    main(
        [
            "--s3=s3.host.com",
            "--s3accesskey=ABCDEF",
            "--s3secretkey=000000",
            "--s3bucket=bucket",
            ".",
        ]
    )
    mock_s3.assert_called_with("s3.host.com", "ABCDEF", "000000", "bucket")
    bup.execute.assert_called_once_with(
        targets=[s3],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    )

    # test: configure s3 target with no bucket (bucket should be source.slug)
    main(["--s3=s3.host.com", "--s3accesskey=ABCDEF", "--s3secretkey=000000", "."])
    mock_s3.assert_called_with(
        "s3.host.com", "ABCDEF", "000000", "wordpress-instance-to-backup"
    )
    bup.execute.assert_called_with(
        targets=[s3],
        database=False,
        filesystem=False,
        thinning=None,
        attic=None,
        dry=False,
    )
