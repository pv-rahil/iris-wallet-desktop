"""
Unit tests for `src/utils/biscuit_auth.py`.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

from src.utils.biscuit_auth import generate_and_store_token


@patch('src.utils.biscuit_auth.SettingRepository')
def test_generate_and_store_token_existing(mock_setting_repo):
    """Test when token already exists."""
    # Case 1: Token already exists
    mock_setting_repo.get_bridge_token.return_value = 'existing_token'
    assert generate_and_store_token() == 'existing_token'
    mock_setting_repo.get_bridge_token.assert_called_once()


@patch('src.utils.biscuit_auth.SettingRepository')
def test_generate_and_store_token_missing_xpub(mock_setting_repo):
    """Test when Colored Account XPUB is missing."""
    # Case 2: Missing Colored Account XPUB
    mock_setting_repo.get_bridge_token.return_value = None
    mock_setting_repo.get_config_value.return_value = None
    assert generate_and_store_token() is None


@patch('src.utils.biscuit_auth.SettingRepository')
@patch('os.path.exists')
def test_generate_and_store_token_missing_key_file(mock_exists, mock_setting_repo):
    """Test when private-key-file is missing."""
    # Case 3: Missing private-key-file
    mock_setting_repo.get_bridge_token.return_value = None
    mock_setting_repo.get_config_value.return_value = 'some_xpub'
    mock_exists.return_value = False
    assert generate_and_store_token() is None


@patch('src.utils.biscuit_auth.SettingRepository')
@patch('os.path.exists')
@patch('subprocess.run')
def test_generate_and_store_token_success(mock_run, mock_exists, mock_setting_repo):
    """Test successful token generation."""
    # Case 4: Successful generation
    mock_setting_repo.get_bridge_token.return_value = None
    mock_setting_repo.get_config_value.return_value = 'some_xpub'
    mock_exists.side_effect = lambda path: 'private-key-file' in path

    mock_result = MagicMock()
    mock_result.stdout = 'new_token\n'
    mock_run.return_value = mock_result

    assert generate_and_store_token() == 'new_token'
    mock_setting_repo.set_bridge_token.assert_called_with('new_token')


@patch('src.utils.biscuit_auth.SettingRepository')
@patch('os.path.exists')
@patch('subprocess.run')
def test_generate_and_store_token_empty_output(mock_run, mock_exists, mock_setting_repo):
    """Test when biscuit returns empty output."""
    # Case 5: Empty output from biscuit
    mock_setting_repo.get_bridge_token.return_value = None
    mock_setting_repo.get_config_value.return_value = 'some_xpub'
    mock_exists.return_value = True

    mock_result = MagicMock()
    mock_result.stdout = ''
    mock_run.return_value = mock_result

    assert generate_and_store_token() is None


@patch('src.utils.biscuit_auth.SettingRepository')
@patch('os.path.exists')
@patch('subprocess.run')
def test_generate_and_store_token_subprocess_error(mock_run, mock_exists, mock_setting_repo):
    """Test when subprocess.run raises CalledProcessError."""
    # Case 6: subprocess.CalledProcessError
    mock_setting_repo.get_bridge_token.return_value = None
    mock_setting_repo.get_config_value.return_value = 'some_xpub'
    mock_exists.return_value = True

    mock_run.side_effect = subprocess.CalledProcessError(
        1, 'cmd', stderr='error',
    )

    assert generate_and_store_token() is None


@patch('src.utils.biscuit_auth.SettingRepository')
def test_generate_and_store_token_general_exception(mock_setting_repo):
    """Test when general exception occurs."""
    # Case 7: General exception
    mock_setting_repo.get_bridge_token.side_effect = Exception(
        'unexpected error',
    )
    assert generate_and_store_token() is None
