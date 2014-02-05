# coding: utf-8

import pytest, mock

from sitebackup import main
from backup.source.wordpress import WPError

def testHelp():
    with pytest.raises(SystemExit) as exceptioninfo:
        result = main(["-h",])
    assert exceptioninfo.value.code == 0

import backup

def setupMockedWP(MockWP):
    m = MockWP()
    m.dbname = None
    m.dbhost = None
    m.dbuser = None
    m.dbpass = None
    m.dbprefix = None
    MockWP.reset_mock()
    return m

@mock.patch('sitebackup.os.path.isdir', return_value=True)
@mock.patch('sitebackup.WP')
@mock.patch('sitebackup.Backup')
def testWithNoArguments(MockBackup, MockWP, *args):
    mockedWP = setupMockedWP(MockWP)
    result = main(["path_for_test_with_no_arguments"])
    assert MockWP.mock_calls == [mock.call('path_for_test_with_no_arguments')]
    assert mockedWP.dbname == None
    assert mockedWP.dbhost == None
    assert mockedWP.dbuser == None
    assert mockedWP.dbpass == None
    assert mockedWP.dbprefix == None

@mock.patch('sitebackup.os.path.isdir', return_value=True)
@mock.patch('sitebackup.WP')
@mock.patch('sitebackup.Backup')
def testWithDBArguments(MockBackup, MockWP, *args):
    mockedWP = setupMockedWP(MockWP)
    result = main(["--db=wpdb", "--dbhost=localhost", "--dbuser=michael", "--dbpass=123456", "--dbprefix=wp", "path_for_test_with_db_arguments"])
    # configuration should be taken from arguments
    assert MockWP.mock_calls == [mock.call('path_for_test_with_db_arguments')]
    assert mockedWP.dbname == "wpdb"
    assert mockedWP.dbhost == "localhost"
    assert mockedWP.dbuser == "michael"
    assert mockedWP.dbpass == "123456"
    assert mockedWP.dbprefix == "wp"
