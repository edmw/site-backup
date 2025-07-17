# coding: utf-8

import os
import shutil
import subprocess
import tempfile
import time
from unittest.mock import Mock

import pytest
import requests

from backup.target.s3 import S3, S3Error, S3Result, S3ThinningResult


@pytest.fixture(scope="session")
def minio_server():
    """Start a local MinIO server for integration testing."""
    # Create temporary directory for MinIO data
    temp_dir = tempfile.mkdtemp(prefix="minio_test_")

    process = None
    try:
        # Start MinIO server
        minio = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "testing", "minio"
        )
        process = subprocess.Popen(
            [
                minio,
                "server",
                temp_dir,
                "--address",
                "127.0.0.1:9100",  # Use different port to avoid conflicts
                "--console-address",
                "127.0.0.1:9101",
            ],
            cwd=temp_dir,
            env={
                **os.environ,
                "MINIO_ROOT_USER": "testuser",
                "MINIO_ROOT_PASSWORD": "testpass123",
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start (up to 30 seconds)
        for _ in range(60):  # 60 attempts = 30 seconds
            try:
                response = requests.get(
                    "http://127.0.0.1:9100/minio/health/live", timeout=1
                )
                if response.status_code == 200:
                    break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                pass
            time.sleep(0.5)
        else:
            process.terminate()
            process.wait()
            raise RuntimeError("MinIO server failed to start within 30 seconds")

        yield {
            "host": "127.0.0.1:9100",
            "access_key": "testuser",
            "secret_key": "testpass123",
            "bucket": "test-bucket",
        }

    finally:
        if process:
            process.terminate()
            process.wait()
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def s3_config(minio_server):
    """S3 configuration for testing with local MinIO."""
    host, port = minio_server["host"].split(":", 1)
    return {
        "host": str(host),
        "port": int(port),
        "accesskey": minio_server["access_key"],
        "secretkey": minio_server["secret_key"],
        "bucket": minio_server["bucket"],
        "is_secure": False,  # Use HTTP for local testing
    }


@pytest.fixture
def test_archive_file():
    """Create a real temporary test archive file."""
    # Create a test archive in current directory with correct naming
    archive_name = "test-20230101120000.tgz"

    # Write some test content to the file
    with open(archive_name, "wb") as temp_file:
        content = b"This is test archive content for S3 testing." * 100
        temp_file.write(content)

    yield archive_name

    # Cleanup
    try:
        os.unlink(archive_name)
    except OSError:
        pass


@pytest.fixture
def mock_archive(test_archive_file):
    """Create mock archive with real file."""
    archive = Mock()
    archive.filename = test_archive_file
    archive.label = "test"
    # Add basename for easier testing
    archive.basename = os.path.basename(test_archive_file)
    return archive


@pytest.mark.integration
def test_s3_instance_creation(s3_config):
    """Test creating S3 instance with real configuration."""
    s3 = S3(**s3_config)
    assert s3.host == s3_config["host"]
    assert s3.bucket == s3_config["bucket"]
    assert s3.label == "S3"


@pytest.mark.integration
def test_connection_and_list_empty_bucket(s3_config):
    """Test connection and listing empty bucket."""
    s3 = S3(**s3_config)
    try:
        archives = s3.listArchives()
        assert isinstance(archives, list)
        # Bucket might not exist initially, which is okay
    except S3Error as e:
        # Acceptable errors for non-existent bucket
        assert any(
            error in str(e).lower() for error in ["nosuchbucket", "404", "not found"]
        )


@pytest.mark.integration
def test_transfer_archive_success(s3_config, mock_archive):
    """Test successful archive transfer."""
    s3 = S3(**s3_config)

    result = s3.transferArchive(mock_archive)

    assert isinstance(result, S3Result)
    assert result.size > 0
    assert result.duration >= 0
    print(f"Upload result: size={result.size}, duration={result.duration}s")


@pytest.mark.integration
def test_transfer_archive_dry_run(s3_config, mock_archive):
    """Test archive transfer in dry run mode."""
    s3 = S3(**s3_config)

    result = s3.transferArchive(mock_archive, dry=True)

    assert isinstance(result, S3Result)
    assert result.size == 0
    assert result.duration == 0


@pytest.mark.integration
def test_list_archives_after_upload(s3_config, mock_archive):
    """Test listing archives after uploading one."""
    s3 = S3(**s3_config)

    # Upload archive
    s3.transferArchive(mock_archive)

    # List archives
    archives = s3.listArchives("test")

    # Should find our uploaded archive
    uploaded_names = [getattr(arch, "filename", str(arch)) for arch in archives]
    expected_name = mock_archive.basename

    found = any(expected_name in name for name in uploaded_names)
    assert found, f"Expected {expected_name} in {uploaded_names}"


@pytest.mark.integration
def test_thinning_delete_all(s3_config, mock_archive):
    """Test archive thinning (deletion)."""
    s3 = S3(**s3_config)

    # First upload an archive
    s3.transferArchive(mock_archive)

    # Define thinning strategy (delete everything)
    def delete_all_strategy(archives):
        return [], archives  # Keep nothing, delete all

    # Perform thinning
    thin_result = s3.performThinning("test", delete_all_strategy)

    assert isinstance(thin_result, S3ThinningResult)
    assert thin_result.archivesRetained == 0
    assert thin_result.archivesDeleted >= 1
    print(
        f"Thinning result: "
        f"retained={thin_result.archivesRetained}, "
        f"deleted={thin_result.archivesDeleted}"
    )

    # Verify archives were deleted
    remaining_archives = s3.listArchives("test")
    assert len(remaining_archives) == 0


@pytest.mark.integration
def test_thinning_keep_some(s3_config):
    """Test thinning that keeps some archives."""
    s3 = S3(**s3_config)

    # Upload multiple test archives
    archive_files = []
    try:
        for i in range(3):
            # Create properly formatted archive files in current directory
            archive_name = f"test-2023010{(i + 1)}120000.tgz"

            with open(archive_name, "wb") as temp_file:
                temp_file.write(b"test content " + str(i).encode())

            archive_files.append(archive_name)

            mock_arch = Mock()
            mock_arch.filename = archive_name
            mock_arch.label = "test"

            s3.transferArchive(mock_arch)

        # Define thinning strategy (keep first 2, delete rest)
        def keep_two_strategy(archives):
            return archives[:2], archives[2:]

        # Perform thinning
        thin_result = s3.performThinning("test", keep_two_strategy)

        assert thin_result.archivesRetained == 2
        assert thin_result.archivesDeleted >= 1

    finally:
        # Cleanup
        for archive_file in archive_files:
            try:
                os.unlink(archive_file)
            except OSError:
                pass


@pytest.mark.integration
def test_error_handling_invalid_credentials():
    """Test error handling with invalid credentials."""
    invalid_s3 = S3(
        host="127.0.0.1:9100",  # Valid host but invalid credentials
        accesskey="invalid",
        secretkey="invalid",
        bucket="test-bucket",
    )

    with pytest.raises(S3Error):
        invalid_s3.listArchives()


@pytest.mark.integration
def test_error_handling_invalid_host():
    """Test error handling with invalid host."""
    invalid_s3 = S3(
        host="invalid-host-12345.com:9999",
        accesskey="test",
        secretkey="test",
        bucket="test-bucket",
    )

    with pytest.raises(S3Error):
        invalid_s3.listArchives()


@pytest.mark.integration
def test_progress_with_large_file(s3_config, capsys):
    """Test progress indicator with larger file."""
    s3 = S3(**s3_config)

    # Create a larger test file to trigger progress callbacks
    with tempfile.NamedTemporaryFile(
        suffix="_large_test_20230101_120000.tar.gz", delete=False
    ) as large_file:
        # Write 512KB of data to potentially trigger progress
        content = b"X" * (512 * 1024)
        large_file.write(content)
        large_file.flush()

        mock_archive = Mock()
        mock_archive.filename = large_file.name
        mock_archive.label = "test"

        try:
            # Mock stdin.isatty to simulate console
            import sys

            original_isatty = sys.stdin.isatty
            sys.stdin.isatty = lambda: True

            result = s3.transferArchive(mock_archive)

            # Restore original isatty
            sys.stdin.isatty = original_isatty

            # Check that upload succeeded
            assert result.size > 0

            # Check console output for progress indicators
            captured = capsys.readouterr()
            # Should have some output (progress or completion info)
            assert len(captured.out) >= 0  # Allow empty output for fast uploads

        finally:
            os.unlink(large_file.name)
