from unittest.mock import patch

import humanfriendly
import pytest

from backup.archive import ArchiveFile, ArchiveResult


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


class TestArchiveFile:
    """Test cases for ArchiveFile class."""

    def test_archivefile_creation(self):
        """Test that ArchiveFile can be created with a name."""
        archive_file = ArchiveFile("test.txt")
        assert archive_file.name == "test.txt"
        assert archive_file.binmode is False
        assert archive_file.ctime == archive_file.mtime

    def test_archivefile_creation_with_binmode(self):
        """Test that ArchiveFile can be created with binary mode."""
        archive_file = ArchiveFile("test.bin", binmode=True)
        assert archive_file.name == "test.bin"
        assert archive_file.binmode is True

    @patch("backup.archive.time.time")
    def test_archivefile_timestamps(self, mock_time):
        """Test that timestamps are set correctly during creation."""
        mock_time.return_value = 1234567890.0
        archive_file = ArchiveFile("test.txt")
        assert archive_file.ctime == 1234567890.0
        assert archive_file.mtime == 1234567890.0

    def test_archivefile_write_string(self):
        """Test writing string data to ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World"

    def test_archivefile_write_bytes(self):
        """Test writing bytes data to ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write(b"Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World"

    def test_archivefile_write_string_binmode(self):
        """Test writing string data in binary mode."""
        archive_file = ArchiveFile("test.txt", binmode=True)
        archive_file.write("Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World"

    def test_archivefile_writeline_string(self):
        """Test writing string with newline to ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        archive_file.writeline("Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World\n"

    def test_archivefile_writeline_bytes(self):
        """Test writing bytes with newline to ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        archive_file.writeline(b"Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World\n"

    def test_archivefile_writeline_string_binmode(self):
        """Test writing string with newline in binary mode."""
        archive_file = ArchiveFile("test.txt", binmode=True)
        archive_file.writeline("Hello World")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World\n"

    def test_archivefile_multiple_writes(self):
        """Test multiple writes to the same ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello ")
        archive_file.write("World")
        archive_file.writeline("!")
        archive_file.write("More content")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World!\nMore content"

    def test_archivefile_size_empty(self):
        """Test size of empty ArchiveFile."""
        archive_file = ArchiveFile("test.txt")
        assert archive_file.size() == 0

    def test_archivefile_size_with_content(self):
        """Test size calculation with content."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello World")
        assert archive_file.size() == 11

    def test_archivefile_size_with_writeline(self):
        """Test size calculation with writeline content."""
        archive_file = ArchiveFile("test.txt")
        archive_file.writeline("Hello")
        assert archive_file.size() == 6  # "Hello" + "\n"

    def test_archivefile_size_after_multiple_operations(self):
        """Test size after multiple write operations."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello")
        archive_file.writeline(" World")
        archive_file.write("!")
        assert archive_file.size() == 13

    def test_archivefile_fileobject_returns_bytesio(self):
        """Test that fileobject returns a BytesIO object."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("test content")
        file_obj = archive_file.fileobject()
        assert hasattr(file_obj, "read")
        assert hasattr(file_obj, "seek")
        assert hasattr(file_obj, "tell")

    def test_archivefile_fileobject_positioned_at_start(self):
        """Test that fileobject is positioned at start when returned."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("test content")
        file_obj = archive_file.fileobject()
        assert file_obj.tell() == 0
        content = file_obj.read()
        assert content == b"test content"

    def test_archivefile_size_preserves_position(self):
        """Test that size() method preserves the handle position after multiple calls."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("test content")
        size1 = archive_file.size()
        size2 = archive_file.size()
        assert size1 == size2 == 12
        archive_file.write(" more")
        assert archive_file.size() == 17

    def test_archivefile_mixed_string_bytes_operations(self):
        """Test mixing string and bytes operations."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello ")
        archive_file.write(b"World ")
        archive_file.writeline("from")
        archive_file.writeline(b"Python")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"Hello World from\nPython\n"

    def test_archivefile_unicode_content(self):
        """Test handling unicode content."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("Hello 世界")
        archive_file.writeline("🚀")
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        expected = "Hello 世界🚀\n".encode("utf-8")  # noqa: UP012
        assert content == expected

    def test_archivefile_large_content(self):
        """Test handling larger content."""
        archive_file = ArchiveFile("test.txt")
        large_content = "A" * 1_000_000
        archive_file.write(large_content)
        assert archive_file.size() == 1_000_000
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert len(content) == 1_000_000
        assert content == large_content.encode()

    def test_archivefile_empty_writes(self):
        """Test writing empty strings and bytes."""
        archive_file = ArchiveFile("test.txt")
        archive_file.write("")
        archive_file.write(b"")
        archive_file.writeline("")
        archive_file.writeline(b"")
        assert archive_file.size() == 2
        file_obj = archive_file.fileobject()
        content = file_obj.read()
        assert content == b"\n\n"
