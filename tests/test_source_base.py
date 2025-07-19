from pathlib import Path
from unittest.mock import patch

import pytest

from backup.source._base import BaseSource


@pytest.fixture
def paths():
    return (Path("/test/instance/path"), Path("/test/config/path"))


@patch("backup.source._base.Reporter.__init__", return_value=None)
def test_initialization(mock_reporter_init, paths):
    source = BaseSource(*paths)

    mock_reporter_init.assert_called_once()

    assert source.fspath == paths[0]
    assert source.fsconfig == paths[1]

    assert source.title is None
    assert source.slug is None
    assert source.description == ""
    assert source.email is None

    assert source.dbname is None
    assert source.dbhost is None
    assert source.dbport == 3306
    assert source.dbuser is None
    assert source.dbpass is None
    assert source.dbprefix is None
    assert source.dbcharset == "utf8mb4"


@patch("backup.source._base.Reporter.__init__", return_value=None)
def test_str(mock_reporter_init, paths):
    source = BaseSource(*paths)

    source.title = "Test Title"
    source.slug = "test-title"
    source.description = "Test Description"
    source.email = "test@test.invalid"
    source.dbname = "test_db"
    source.dbhost = "localhost"
    source.dbuser = "test_user"
    source.dbpass = "test_pass"
    source.dbprefix = "test_"

    assert str(source) == (
        "BASESOURCE\n"
        "    Slug: test-title\n"
        "    WP(Title): Test Title\n"
        "    WP(Email): test@test.invalid\n"
        "    DB(Name): test_db\n"
        "    DB(Host): localhost\n"
        "    DB(Port): 3306\n"
        "    DB(Prefix): test_\n"
        "    DB(User): test_user\n"
        "    DB(Pass): *******"
    )
