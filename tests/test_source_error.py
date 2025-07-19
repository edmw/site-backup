# filepath: /Users/michael/Projekte/Arbeitsbereich/MiB Script Site-Backup/tests/test_source_error.py

import pytest

from backup.source.errors import SourceError, SourceMultipleError


def test_source_error_with_message():
    message = "Test error message"
    with pytest.raises(SourceError) as exc_info:
        raise SourceError(message)
    assert str(exc_info.value) == message


def test_source_error_without_message():
    with pytest.raises(SourceError) as exc_info:
        raise SourceError()
    assert str(exc_info.value) == ""


def test_source_multiple_error_initialization():
    message = "Multiple errors occurred"
    errors: list[Exception] = [ValueError("Error 1"), RuntimeError("Error 2")]
    error = SourceMultipleError(message, errors)
    assert error.errors == errors
    assert str(error) == f"{message}: {[str(e) for e in errors]}"


def test_source_multiple_error_with_empty_errors():
    message = "No errors"
    errors: list[Exception] = []
    error = SourceMultipleError(message, errors)
    assert error.errors == []
    assert str(error) == f"{message}: []"


def test_source_multiple_error_with_single_error():
    message = "Single error occurred"
    errors: list[Exception] = [ValueError("Only error")]
    error = SourceMultipleError(message, errors)
    assert error.errors == errors
    assert str(error) == f"{message}: ['Only error']"


def test_source_multiple_error_can_be_raised():
    message = "Test multiple error"
    errors: list[Exception] = [ValueError("Error 1")]
    with pytest.raises(SourceMultipleError) as exc_info:
        raise SourceMultipleError(message, errors)
    assert exc_info.value.errors == errors
    assert str(exc_info.value) == f"{message}: ['Error 1']"
