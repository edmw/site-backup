import humanfriendly
import pytest

from backup.archive import ArchiveResult


class TestArchiveResult:
    """Test cases for ArchiveResult class."""

    def test_archiveresult_creation(self):
        """Test that ArchiveResult can be created with a size."""
        result = ArchiveResult(1024)
        assert result.size == 1024

    def test_archiveresult_creation_with_zero_size(self):
        """Test that ArchiveResult can be created with zero size."""
        result = ArchiveResult(0)
        assert result.size == 0

    def test_archiveresult_creation_with_large_size(self):
        """Test that ArchiveResult can be created with large size."""
        large_size = 1024 * 1024 * 1024  # 1 GB
        result = ArchiveResult(large_size)
        assert result.size == large_size

    def test_archiveresult_is_namedtuple(self):
        """Test that ArchiveResult behaves like a namedtuple."""
        result = ArchiveResult(1024)
        # Test tuple unpacking
        (size,) = result
        assert size == 1024
        # Test indexing
        assert result[0] == 1024
        # Test that it's immutable
        with pytest.raises(AttributeError):
            result.size = 2048  # type: ignore[assignment]  # noqa: E501

    def test_archiveresult_str_formatting(self):
        """Test the string representation of ArchiveResult."""
        result = ArchiveResult(1024)
        expected = f"Result(size={humanfriendly.format_size(1024)})"
        assert str(result) == expected

    def test_archiveresult_str_with_zero_size(self):
        """Test string representation with zero size."""
        result = ArchiveResult(0)
        expected = f"Result(size={humanfriendly.format_size(0)})"
        assert str(result) == expected

    def test_archiveresult_str_with_various_sizes(self):
        """Test string representation with various file sizes."""
        test_cases = [
            (512, "Result(size=512 bytes)"),
            (1024, "Result(size=1.02 KB)"),
            (1048576, "Result(size=1.05 MB)"),
            (1073741824, "Result(size=1.07 GB)"),
        ]
        for size, expected in test_cases:
            result = ArchiveResult(size)
            assert str(result) == expected

    def test_archiveresult_equality(self):
        """Test equality comparison between ArchiveResult instances."""
        result1 = ArchiveResult(1024)
        result2 = ArchiveResult(1024)
        result3 = ArchiveResult(2048)
        assert result1 == result2
        assert result1 != result3

    def test_archiveresult_repr(self):
        """Test the repr representation of ArchiveResult."""
        result = ArchiveResult(1024)
        assert repr(result) == "ArchiveResult(size=1024)"

    def test_archiveresult_hashable(self):
        """Test that ArchiveResult can be used as dict keys or in sets."""
        result1 = ArchiveResult(1024)
        result2 = ArchiveResult(2048)
        result_set = {result1, result2}
        assert len(result_set) == 2
        result_dict = {result1: "first", result2: "second"}
        assert result_dict[result1] == "first"
        assert result_dict[result2] == "second"

    def test_archiveresult_field_access(self):
        """Test accessing fields by name and position."""
        result = ArchiveResult(1024)
        assert result.size == 1024
        assert result[0] == 1024

    def test_archiveresult_with_negative_size(self):
        """Test ArchiveResult with negative size (edge case)."""
        result = ArchiveResult(-1)
        assert result.size == -1
        assert str(result) == "Result(size=-1 bytes)"

    def test_archiveresult_asdict(self):
        """Test converting ArchiveResult to dictionary."""
        result = ArchiveResult(1024)
        result_dict = result._asdict()
        assert result_dict == {"size": 1024}

    def test_archiveresult_replace(self):
        """Test the _replace method of namedtuple."""
        result = ArchiveResult(1024)
        new_result = result._replace(size=2048)
        assert result.size == 1024
        assert new_result.size == 2048
