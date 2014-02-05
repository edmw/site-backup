# coding: utf-8

import pytest, mock

from backup.source.wordpress import WP, WPError

TEST_CONFIG="""
define('DB_NAME', 'name');
define('DB_USER', 'michael');
define('DB_PASSWORD', '123456');
define('DB_HOST', 'localhost');
define('DB_CHARSET', 'utf8');
$table_prefix  = 'wp_';
"""

@mock.patch.object(WP, "checkConfig", return_value = True)
def testConstruction(*args):
	with mock.patch("backup.source.wordpress.open", mock.mock_open(read_data=TEST_CONFIG), create=True) as m:
		wp = WP("path_to_instance")
	assert wp.dbname == "name"
	assert wp.dbhost == "localhost"
	assert wp.dbuser == "michael"
	assert wp.dbpass == "123456"
	assert wp.dbprefix == "wp_"
	print m.mock_calls
	m.assert_called_once_with('path_to_instance/wp-config.php')
	# NEXT: add mock for database and test it
	