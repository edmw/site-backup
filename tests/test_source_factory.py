from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backup.source._base import SourceConfig
from backup.source.errors import SourceMultipleError
from backup.source.factory import SourceFactory
from backup.source.humhub import HH, HHError
from backup.source.wordpress import WP, WPError


@pytest.fixture
def factory():
    path = Path("/test/path")
    return SourceFactory(path)


@pytest.fixture
def config():
    return SourceConfig(
        dbname="test_db",
        dbhost="localhost",
        dbport=3306,
        dbuser="test_user",
        dbpass="test_pass",
        dbprefix="wp_",
    )


def test_factory_path_assignment():
    test_path = Path("/custom/test/path")
    factory = SourceFactory(test_path)

    assert factory.path is test_path


@patch("backup.source.factory.WP")
def test_create_returns_wordpress_source_when_successful(mock_wp, factory, config):
    mock_wp_instance = Mock(spec=WP)
    mock_wp.return_value = mock_wp_instance

    result = factory.create(config)

    mock_wp.assert_called_once_with(factory.path, config)
    assert result is mock_wp_instance


@patch("backup.source.factory.HH")
@patch("backup.source.factory.WP")
def test_create_skips_humhub_when_wordpress_succeeds(mock_wp, mock_hh, factory, config):
    mock_wp_instance = Mock(spec=WP)
    mock_wp.return_value = mock_wp_instance

    result = factory.create(config)

    mock_wp.assert_called_once_with(factory.path, config)
    mock_hh.assert_not_called()
    assert result is mock_wp_instance


@patch("backup.source.factory.HH")
@patch("backup.source.factory.WP")
def test_create_returns_humhub_source_when_wordpress_fails(
    mock_wp, mock_hh, factory, config
):
    mock_wp.side_effect = WPError(None, "WordPress not found")
    mock_hh_instance = Mock(spec=HH)
    mock_hh.return_value = mock_hh_instance

    result = factory.create(config)

    mock_wp.assert_called_once_with(factory.path, config)
    mock_hh.assert_called_once_with(factory.path, config)
    assert result is mock_hh_instance


@patch("backup.source.factory.HH")
@patch("backup.source.factory.WP")
def test_create_raises_source_multiple_error_when_both_fail(
    mock_wp, mock_hh, factory, config
):
    wp_error = WPError(None, "WordPress config not found")
    hh_error = HHError(None, "HumHub config not found")

    mock_wp.side_effect = wp_error
    mock_hh.side_effect = hh_error

    with pytest.raises(SourceMultipleError) as exc_info:
        factory.create(config)

    mock_wp.assert_called_once_with(factory.path, config)
    mock_hh.assert_called_once_with(factory.path, config)

    assert exc_info.value.errors == [wp_error, hh_error]
    assert "Can't create source" in str(exc_info.value)


@patch("backup.source.factory.HH")
@patch("backup.source.factory.WP")
def test_create_with_different_wp_error_types(mock_wp, mock_hh, factory, config):
    from backup.source.wordpress import WPDatabaseError, WPNotFoundError

    wp_errors = [
        WPNotFoundError(None, "config file not found"),
        WPDatabaseError(None, "database connection failed"),
    ]

    for wp_error in wp_errors:
        mock_wp.side_effect = wp_error
        mock_hh_instance = Mock(spec=HH)
        mock_hh.return_value = mock_hh_instance

        result = factory.create(config)

        assert result is mock_hh_instance
        mock_hh.reset_mock()
        mock_wp.reset_mock()


@patch("backup.source.factory.HH")
@patch("backup.source.factory.WP")
def test_create_with_different_hh_error_types(mock_wp, mock_hh, factory, config):
    from backup.source.humhub import HHConfigError, HHDatabaseError, HHNotFoundError

    wp_error = WPError(None, "WordPress not found")
    hh_errors = [
        HHNotFoundError(None, "HumHub not found"),
        HHConfigError(None, "config parse error"),
        HHDatabaseError(None, "database error"),
    ]

    for hh_error in hh_errors:
        mock_wp.side_effect = wp_error
        mock_hh.side_effect = hh_error

        with pytest.raises(SourceMultipleError) as exc_info:
            factory.create(config)

        assert len(exc_info.value.errors) == 2
        assert exc_info.value.errors[0] is wp_error
        assert exc_info.value.errors[1] is hh_error

        mock_wp.reset_mock()
        mock_hh.reset_mock()
