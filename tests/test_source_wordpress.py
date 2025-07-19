from pathlib import Path
from unittest.mock import mock_open, patch

from backup.source.wordpress import WP

TEST_CONFIG = """
define('DB_NAME', 'name');
define('DB_USER', 'michael');
define('DB_PASSWORD', '123456');
define('DB_HOST', 'localhost');
define('DB_CHARSET', 'utf8');
$table_prefix  = 'wp_';
"""


@patch.object(WP, "check_configuration", return_value=True)
@patch.object(WP, "query_database", return_value=("title", "description", "email"))
def test_construction(_mock_query, _mock_check):
    with patch(
        "backup.source.wordpress.open", mock_open(read_data=TEST_CONFIG), create=True
    ) as m:
        wp = WP(Path("path_to_instance"))
    assert wp.dbname == "name"
    assert wp.dbhost == "localhost"
    assert wp.dbuser == "michael"
    assert wp.dbpass == "123456"
    assert wp.dbprefix == "wp_"
    m.assert_called_once_with(Path("path_to_instance/wp-config.php"))


@patch.object(WP, "check_configuration", return_value=True)
@patch.object(WP, "query_database", return_value=("title", "description", "email"))
def test_construction_with_given_arguments(_mock_query, _mock_check):
    with patch(
        "backup.source.wordpress.open", mock_open(read_data=TEST_CONFIG), create=True
    ) as m:
        wp = WP(
            Path("path_to_instance"), {"dbhost": "otherhost", "dbpass": "otherpass"}
        )
    assert wp.dbname == "name"
    assert wp.dbhost == "otherhost"
    assert wp.dbuser == "michael"
    assert wp.dbpass == "otherpass"
    assert wp.dbprefix == "wp_"
    m.assert_called_once_with(Path("path_to_instance/wp-config.php"))
    # NEXT: add mock for database and test it
