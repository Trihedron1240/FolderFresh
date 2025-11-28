# conftest.py
"""
Pytest configuration and shared fixtures for FolderFresh test suite.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Add src to path so imports work
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing, clean up after test."""
    test_dir = tempfile.mkdtemp(prefix="folderfresh_test_")
    yield test_dir
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture
def test_structure(temp_dir):
    """Create a test directory structure with subdirectories."""
    source_dir = os.path.join(temp_dir, "source")
    dest_dir = os.path.join(temp_dir, "dest")
    copy_dir = os.path.join(temp_dir, "copy")

    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(copy_dir, exist_ok=True)

    return {
        "base": temp_dir,
        "source": source_dir,
        "dest": dest_dir,
        "copy": copy_dir
    }


@pytest.fixture
def test_file_factory(temp_dir):
    """Factory for creating test files with various properties."""
    def create_file(directory, filename, content="test content", size_kb=0):
        filepath = os.path.join(directory, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if size_kb > 0:
            # Create file of specific size
            with open(filepath, "wb") as f:
                f.write(b"x" * (size_kb * 1024))
        else:
            # Create file with content
            with open(filepath, "w") as f:
                f.write(content)

        return filepath

    return create_file


@pytest.fixture
def clear_activity_log():
    """Clear activity log before and after test."""
    from folderfresh.activity_log import ACTIVITY_LOG

    ACTIVITY_LOG.clear()
    yield
    ACTIVITY_LOG.clear()


@pytest.fixture
def clear_undo_manager():
    """Clear undo manager before and after test."""
    from folderfresh.undo_manager import UNDO_MANAGER

    UNDO_MANAGER.clear_history()
    yield
    UNDO_MANAGER.clear_history()


@pytest.fixture
def basic_config():
    """Return a basic config dict for testing."""
    return {
        "dry_run": False,
        "safe_mode": True,
        "skip_hidden": True,
        "age_filter_days": 0,
        "smart_mode": False
    }


@pytest.fixture
def dry_run_config():
    """Return a dry_run config dict."""
    return {
        "dry_run": True,
        "safe_mode": True,
        "skip_hidden": True,
        "age_filter_days": 0
    }


# Pytest hooks for better output

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: slow tests"
    )
