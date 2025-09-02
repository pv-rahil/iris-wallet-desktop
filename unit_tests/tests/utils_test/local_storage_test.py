"""Unit test for local store"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
from __future__ import annotations

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings

from src.utils.constant import APP_NAME
from src.utils.constant import ORGANIZATION_DOMAIN
from src.utils.local_store import LocalStore


@pytest.fixture
def mock_qsettings():
    """Fixture to mock QSettings."""
    with patch('PySide6.QtCore.QSettings', autospec=True) as mock_qsettings:
        yield mock_qsettings


@pytest.fixture
def mock_qdir():
    """Fixture to mock QDir."""
    with patch('PySide6.QtCore.QDir', autospec=True) as mock_qdir:
        mock_qdir.return_value.filePath.return_value = '/mock/path'
        mock_qdir.return_value.mkpath = MagicMock()
        yield mock_qdir


@pytest.fixture
def local_store(tmp_path, mock_qsettings):
    """Fixture to initialize LocalStore in a temp sandbox path."""
    # Point writableLocation to a temporary directory to avoid touching real data
    with patch('PySide6.QtCore.QStandardPaths.writableLocation', return_value=str(tmp_path)):
        return LocalStore(APP_NAME, ORGANIZATION_DOMAIN)


def test_set_value(local_store):
    """Test that set_value sets the value in settings."""
    local_store.settings.setValue = MagicMock()
    local_store.set_value('test_key', 'test_value')
    local_store.settings.setValue.assert_called_once_with(
        'test_key', 'test_value',
    )


def test_get_value(local_store):
    """Test that get_value retrieves the value from settings."""
    local_store.settings.value = MagicMock(return_value='test_value')
    result = local_store.get_value('test_key')
    assert result == 'test_value'
    local_store.settings.value.assert_called_once_with('test_key')


def test_get_value_with_type_conversion(local_store):
    """Test that get_value converts the value to the specified type."""
    local_store.settings.value = MagicMock(return_value='123')
    result = local_store.get_value('test_key', int)
    assert result == 123


def test_get_value_conversion_failure(local_store):
    """Test that get_value returns None if type conversion fails."""
    local_store.settings.value = MagicMock(return_value='not_an_int')
    result = local_store.get_value('test_key', int)
    assert result is None


def test_remove_key(local_store):
    """Test that remove_key removes the key from settings."""
    local_store.settings.remove = MagicMock()
    local_store.remove_key('test_key')
    local_store.settings.remove.assert_called_once_with('test_key')


def test_clear_settings(local_store):
    """Test that clear_settings clears all settings."""
    local_store.settings.clear = MagicMock()
    local_store.clear_settings()
    local_store.settings.clear.assert_called_once()


def test_all_keys(local_store):
    """Test that all_keys returns all keys."""
    local_store.settings.allKeys = MagicMock(return_value=['key1', 'key2'])
    result = local_store.all_keys()
    assert result == ['key1', 'key2']
    local_store.settings.allKeys.assert_called_once()


def test_get_path(local_store):
    """Test that get_path returns the base path."""
    local_store.get_path = MagicMock(return_value='/mock/path/regtest')

    result = local_store.get_path()
    assert result == '/mock/path/regtest'


def test_create_folder(local_store):
    """Test that create_folder creates a folder and returns its path under base path."""
    result = local_store.create_folder('test_folder')
    assert os.path.isdir(result)
    assert result.startswith(local_store.get_path())


def test_write_to_file_text_and_bytes(local_store):
    """Test that write_to_file creates files with correct content."""
    # write text under base path
    file_rel = 'notes.txt'
    path = local_store.write_to_file(file_rel, value='hello')
    assert os.path.isfile(path)
    with open(path, encoding='utf-8') as f:
        assert f.read() == 'hello'

    # write bytes
    path2 = local_store.write_to_file('bytes.txt', value=b'world')
    with open(path2, encoding='utf-8') as f:
        assert f.read() == 'world'

    # explicit file_path
    explicit = os.path.join(local_store.get_path(), 'explicit.txt')
    path3 = local_store.write_to_file('ignored', file_path=explicit, value='x')
    assert path3 == explicit and os.path.isfile(explicit)


def test_refresh_file_reinits_qsettings(local_store):
    """Test that refresh_file reinitializes QSettings."""
    # swap out current settings with a mock to observe sync()
    old_settings = local_store.settings = MagicMock(spec=QSettings)
    with patch('src.utils.local_store.QSettings') as mock_qsettings:
        local_store.refresh_file()
        old_settings.sync.assert_called_once()
        mock_qsettings.assert_called_once()  # re-init called


def test_remove_file_true_false_and_exception(local_store):
    """Test that remove_file returns True/False and handles exceptions."""
    # create file to remove
    victim = local_store.write_to_file('todelete.txt', value='bye')
    assert local_store.remove_file('todelete.txt') is True
    # already removed
    assert local_store.remove_file('todelete.txt') is False

    # simulate exception path
    with patch('src.utils.local_store.os.path.exists', return_value=True), \
            patch('src.utils.local_store.os.remove', side_effect=OSError('err')):
        assert local_store.remove_file('ignored', file_path=victim) is False
