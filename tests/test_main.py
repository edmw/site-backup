# coding: utf-8

import pytest, mock

from sitebackup import main
from backup.source.wordpress import WPError

def testHelp():
    with pytest.raises(SystemExit) as exceptioninfo:
        result = main(["-h",])
    assert exceptioninfo.value.code == 0

import backup

def setupWP(mock):
    m = mock()
    m.dbname = None
    m.dbhost = None
    m.dbuser = None
    m.dbpass = None
    m.dbprefix = None
    m.title = None
    m.email = None
    mock.reset_mock()
    return m

@mock.patch('sitebackup.os.path.isdir', return_value=True)
@mock.patch('sitebackup.WP')
@mock.patch('sitebackup.Backup')
def testWithNoArguments(patchedBackup, patchedWP, *args):
    wp = setupWP(patchedWP)
    bup = patchedBackup()
    result = main(["path_for_test_with_no_arguments"])
    patchedWP.assert_called_once_with('path_for_test_with_no_arguments', dbhost=None, dbname=None, dbpass=None, dbport=None, dbprefix=None, dbuser=None)
    # configuration should be unchanged
    assert wp.dbname == None
    assert wp.dbhost == None
    assert wp.dbuser == None
    assert wp.dbpass == None
    assert wp.dbprefix == None
    # calls to backup
    patchedBackup.assert_called_with(wp, None, None, quiet=False)
    bup.execute.assert_called_once_with(targets=[], database=False, filesystem=False, attic=None)

@mock.patch('sitebackup.os.path.isdir', return_value=True)
@mock.patch('sitebackup.WP')
@mock.patch('sitebackup.Backup')
def testWithArguments(patchedBackup, patchedWP, *args):
    wp = setupWP(patchedWP)
    wp.email = "michael@localhost"
    bup = patchedBackup()

    # test 1: overwrite database configuration
    result = main(["--db=wpdb", "--dbhost=localhost", "--dbuser=michael", "--dbpass=123456", "--dbprefix=wp", "path_for_test_with_db_arguments"])
    # configuration should be taken from arguments
    patchedWP.assert_called_once_with('path_for_test_with_db_arguments', dbhost='localhost', dbname='wpdb', dbpass='123456', dbport=None, dbprefix='wp', dbuser='michael')
    assert wp.dbname == "wpdb"
    assert wp.dbhost == "localhost"
    assert wp.dbuser == "michael"
    assert wp.dbpass == "123456"
    assert wp.dbprefix == "wp"
    # calls to backup
    patchedBackup.assert_called_with(wp, None, None, quiet=False)
    bup.execute.assert_called_once_with(targets=[], database=False, filesystem=False, attic=None)

    # test 2: configure mail reporting
    result = main(["-q", "--mail-to-admin", "--mail-from=admin@localhost", "."])
    # calls to backup
    patchedBackup.assert_called_with(wp, "michael@localhost", "admin@localhost", quiet=True)
    bup.execute.assert_called_with(targets=[], database=False, filesystem=False, attic=None)

    # test 3: switch on database processing and configure attic with no parameter
    result = main(["--database", "--attic", "--", "."])
    # calls to backup
    patchedBackup.assert_called_with(wp, None, None, quiet=False)
    bup.execute.assert_called_with(targets=[], database=True, filesystem=False, attic=".")

    # test 4: switch on filesystem processing and configure attic with parameter
    result = main(["--filesystem", "--attic=path_to_attic", "."])
    # calls to backup
    patchedBackup.assert_called_with(wp, None, None, quiet=False)
    bup.execute.assert_called_with(targets=[], database=False, filesystem=True, attic="path_to_attic")

@mock.patch('sitebackup.os.path.isdir', return_value=True)
@mock.patch('sitebackup.WP')
@mock.patch('sitebackup.S3')
@mock.patch('sitebackup.Backup')
def testWithS3Arguments(patchedBackup, patchedS3, patchedWP, *args):
    wp = setupWP(patchedWP)
    wp.slug = "wordpress-instance-to-backup"
    s3 = patchedS3()
    bup = patchedBackup()

    # test: configure s3 targets with bucket
    result = main(["--s3=s3.host.com", "--s3accesskey=ABCDEF", "--s3secretkey=000000", "--s3bucket=bucket", "."])
    patchedS3.assert_called_with("s3.host.com", "ABCDEF", "000000", "bucket")
    bup.execute.assert_called_once_with(targets=[s3], database=False, filesystem=False, attic=None)

    # test: configure s3 target with no bucket (bucket should be wp.slug)
    result = main(["--s3=s3.host.com", "--s3accesskey=ABCDEF", "--s3secretkey=000000", "."])
    patchedS3.assert_called_with("s3.host.com", "ABCDEF", "000000", "wordpress-instance-to-backup")
    bup.execute.assert_called_with(targets=[s3], database=False, filesystem=False, attic=None)
