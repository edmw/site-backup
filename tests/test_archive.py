import os
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import humanfriendly
import pytest

from backup.archive import Archive, ArchiveFile, ArchiveResult


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


class TestArchive:
    """Test cases for Archive class."""

    def test_archive_creation_with_label(self):
        """Test that Archive can be created with a label."""
        with patch("backup.archive.timestamp4now") as mock_timestamp:
            mock_timestamp.return_value = "20250129120000"
            archive = Archive("test-backup")
            assert archive.name == "test-backup-20250129120000"
            assert archive.filename == "test-backup-20250129120000.tgz"
            assert archive.timestamp == "20250129120000"
            assert archive.path == "."
            assert archive.tar is None

    def test_archive_creation_with_custom_timestamp(self):
        """Test Archive creation with a custom timestamp."""
        archive = Archive("test-backup", "20240101000000")
        assert archive.name == "test-backup-20240101000000"
        assert archive.filename == "test-backup-20240101000000.tgz"
        assert archive.timestamp == "20240101000000"

    @patch("backup.archive.timestamp2date")
    def test_archive_ctime_set_from_timestamp(self, mock_timestamp2date):
        """Test that ctime is set from timestamp."""
        from datetime import datetime

        mock_date = datetime(2024, 1, 1, 0, 0, 0)
        mock_timestamp2date.return_value = mock_date

        archive = Archive("test", "20240101000000")
        assert archive.ctime == mock_date
        mock_timestamp2date.assert_called_once_with("20240101000000")

    def test_archive_fromfilename_valid(self):
        """Test creating Archive from a valid filename."""
        archive = Archive.fromfilename("backup-test-20240101123456.tgz")
        assert archive.name == "backup-test-20240101123456"
        assert archive.timestamp == "20240101123456"
        assert archive.filename == "backup-test-20240101123456.tgz"

    def test_archive_fromfilename_with_label_check(self):
        """Test creating Archive from filename with label validation."""
        archive = Archive.fromfilename("mybackup-20240101123456.tgz", "mybackup")
        assert archive.name == "mybackup-20240101123456"
        assert archive.timestamp == "20240101123456"

    def test_archive_fromfilename_invalid_format(self):
        """Test error when filename has invalid format."""
        with pytest.raises(ValueError, match="filename 'invalid.tgz' invalid format"):
            Archive.fromfilename("invalid.tgz")

    def test_archive_fromfilename_label_mismatch(self):
        """Test error when filename doesn't match expected label."""
        with pytest.raises(
            ValueError,
            match="filename 'backup-20240101123456.tgz' not matching label 'different'",
        ):
            Archive.fromfilename("backup-20240101123456.tgz", "different")

    def test_archive_repr(self):
        """Test string representation of Archive."""
        archive = Archive("test", "20240101123456")
        expected = "Archive[name=test-20240101123456, timestamp=20240101123456]"
        assert repr(archive) == expected

    @patch("backup.archive.formatkv")
    def test_archive_str(self, mock_formatkv):
        """Test string formatting of Archive."""
        mock_formatkv.return_value = "ARCHIVE\nName: test-20240101123456"
        archive = Archive("test", "20240101123456")
        result = str(archive)
        mock_formatkv.assert_called_once_with(
            [("Name", "test-20240101123456")], title="ARCHIVE"
        )
        assert result == "ARCHIVE\nName: test-20240101123456"

    def test_archive_tarname_default_path(self):
        """Test tarname with default path."""
        archive = Archive("test", "20240101123456")
        expected = os.path.join(".", "test-20240101123456.tgz")
        assert archive.tarname() == expected

    def test_archive_tarname_custom_path(self):
        """Test tarname with custom path."""
        archive = Archive("test", "20240101123456")
        custom_path = "/tmp/backups"
        expected = os.path.join(custom_path, "test-20240101123456.tgz")
        assert archive.tarname(custom_path) == expected

    def test_archive_tarname_with_updated_path(self):
        """Test tarname after updating archive path."""
        archive = Archive("test", "20240101123456")
        archive.path = "/custom/path"
        expected = os.path.join("/custom/path", "test-20240101123456.tgz")
        assert archive.tarname() == expected

    def test_archive_create_archive_file(self):
        """Test creating an ArchiveFile through Archive."""
        archive = Archive("test", "20240101123456")
        archive_file = archive.create_archive_file("test.txt")
        assert isinstance(archive_file, ArchiveFile)
        assert archive_file.name == "test.txt"
        assert archive_file.binmode is False

    def test_archive_create_archive_file_binmode(self):
        """Test creating binary ArchiveFile through Archive."""
        archive = Archive("test", "20240101123456")
        archive_file = archive.create_archive_file("test.bin", binmode=True)
        assert isinstance(archive_file, ArchiveFile)
        assert archive_file.name == "test.bin"
        assert archive_file.binmode is True

    @pytest.fixture
    def temp_dir(self):
        """Provide a temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_archive_context_manager_creation(self, temp_dir):
        """Test Archive as context manager creates tarfile."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 1024
            with archive:
                assert archive.tar == mock_tar
            expected_tarname = os.path.join(temp_dir, "test-20240101123456.tgz")
            mock_open.assert_called_once_with(expected_tarname, "w:gz", debug=0)
            mock_tar.close.assert_called_once()

    def test_archive_context_manager_with_debug_logging(self, temp_dir):
        """Test Archive context manager with debug logging enabled."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("backup.archive.logging.getLogger") as mock_get_logger,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_logger = Mock()
            mock_logger.getEffectiveLevel.return_value = 10  # DEBUG level
            mock_get_logger.return_value = mock_logger
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 2048
            with archive:
                pass
            expected_tarname = os.path.join(temp_dir, "test-20240101123456.tgz")
            mock_open.assert_called_once_with(expected_tarname, "w:gz", debug=1)

    def test_archive_context_manager_exit_error_no_tar(self):
        """Test Archive context manager exit with no tar file opened."""
        archive = Archive("test", "20240101123456")
        with patch("backup.archive.tarfile.open") as mock_open:
            mock_open.return_value = None
            with pytest.raises(RuntimeError, match="archive not opened"):
                with archive:
                    archive.tar = None

    def test_archive_context_manager_stores_result(self, temp_dir):
        """Test that context manager stores archive result."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 1024
            with patch.object(archive, "store_result") as mock_store:
                with archive:
                    pass
                mock_store.assert_called_once()
                call_args = mock_store.call_args[0]
                assert call_args[0] == "createArchive"
                assert isinstance(call_args[1], ArchiveResult)
                assert call_args[1].size == 1024

    def test_archive_add_archive_file_success(self, temp_dir):
        """Test successfully adding an ArchiveFile to archive."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        archive_file = ArchiveFile("test.txt")
        archive_file.write("test content")
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 1024
            with archive:
                result = archive.add_archive_file(archive_file)
                assert result == "test.txt"
                mock_tar.addfile.assert_called_once()
                call_args = mock_tar.addfile.call_args[0]
                tarinfo = call_args[0]
                assert tarinfo.name == "test.txt"
                assert tarinfo.size == 12  # len("test content")
                assert tarinfo.mtime == archive_file.mtime

    def test_archive_add_archive_file_no_tar(self):
        """Test error when adding ArchiveFile without opened tar."""
        archive = Archive("test", "20240101123456")
        archive_file = ArchiveFile("test.txt")
        with pytest.raises(RuntimeError, match="archive not opened"):
            archive.add_archive_file(archive_file)

    def test_archive_add_path_success(self, temp_dir):
        """Test successfully adding a path to archive."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        test_file = Path(temp_dir) / "testfile.txt"
        test_file.write_text("test content")
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 2048
            with archive:
                result = archive.add_path(test_file, "custom_name.txt")
                assert result == test_file
                mock_tar.add.assert_called_once_with(
                    str(test_file), arcname="custom_name.txt"
                )

    def test_archive_add_path_no_tar(self, temp_dir):
        """Test error when adding path without opened tar."""
        archive = Archive("test", "20240101123456")
        test_file = Path(temp_dir) / "testfile.txt"
        with pytest.raises(RuntimeError, match="archive not opened"):
            archive.add_path(test_file)

    def test_archive_add_manifest(self, temp_dir):
        """Test adding manifest to archive."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        with (
            patch("backup.archive.tarfile.open") as mock_open,
            patch("os.path.getsize") as mock_getsize,
        ):
            mock_tar = Mock()
            mock_open.return_value = mock_tar
            mock_getsize.return_value = 512
            with archive:
                archive.add_manifest("20240101123456")
                mock_tar.addfile.assert_called_once()
                call_args = mock_tar.addfile.call_args[0]
                tarinfo = call_args[0]
                assert tarinfo.name == "MANIFEST"

    def test_archive_rename_same_path(self, temp_dir):
        """Test renaming archive with same path (no operation)."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        tarfile_path = os.path.join(temp_dir, "test-20240101123456.tgz")
        Path(tarfile_path).touch()
        result = archive.rename(temp_dir)
        assert result == tarfile_path
        assert archive.path == temp_dir

    def test_archive_rename_different_path(self, temp_dir):
        """Test renaming archive to different path."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        source_path = os.path.join(temp_dir, "test-20240101123456.tgz")
        Path(source_path).touch()
        new_dir = os.path.join(temp_dir, "new_location")
        os.makedirs(new_dir)
        expected_dest = os.path.join(new_dir, "test-20240101123456.tgz")
        with patch("os.rename") as mock_rename:
            result = archive.rename(new_dir)
            assert result == expected_dest
            assert archive.path == new_dir
            mock_rename.assert_called_once_with(source_path, expected_dest)

    def test_archive_remove_existing_file(self, temp_dir):
        """Test removing existing archive file."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        tarfile_path = os.path.join(temp_dir, "test-20240101123456.tgz")
        Path(tarfile_path).touch()
        result = archive.remove()
        assert result == tarfile_path
        assert not os.path.exists(tarfile_path)

    def test_archive_remove_nonexistent_file(self, temp_dir):
        """Test removing non-existent archive file."""
        archive = Archive("test", "20240101123456")
        archive.path = temp_dir
        tarfile_path = os.path.join(temp_dir, "test-20240101123456.tgz")
        result = archive.remove()
        assert result == tarfile_path

    def test_archive_integration_full_workflow(self, temp_dir):
        """Test complete Archive workflow integration."""
        archive = Archive("integration-test", "20240101123456")
        archive.path = temp_dir
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello World")
        with archive:
            archive.add_path(test_file, "backup/test.txt")
            archive_file = archive.create_archive_file("metadata.txt")
            archive_file.writeline("Created: 2024-01-01")
            archive_file.writeline("Size: 11 bytes")
            archive.add_archive_file(archive_file)
            archive.add_manifest("20240101123456")
        tarfile_path = os.path.join(temp_dir, "integration-test-20240101123456.tgz")
        assert os.path.exists(tarfile_path)
        with tarfile.open(tarfile_path, "r:gz") as tar:
            names = tar.getnames()
            assert "backup/test.txt" in names
            assert "metadata.txt" in names
            assert "MANIFEST" in names
            backup_file = tar.extractfile("backup/test.txt")
            assert backup_file is not None
            assert backup_file.read() == b"Hello World"
            metadata_file = tar.extractfile("metadata.txt")
            assert metadata_file is not None
            metadata_content = metadata_file.read().decode()
            assert "Created: 2024-01-01" in metadata_content
            assert "Size: 11 bytes" in metadata_content
            manifest_file = tar.extractfile("MANIFEST")
            assert manifest_file is not None
            manifest_content = manifest_file.read().decode()
            assert "Timestamp: 20240101123456" in manifest_content
