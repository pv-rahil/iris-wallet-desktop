# pylint: disable=protected-access
"""
Unit tests for the MnemonicStore class, which securely encrypts and decrypts
mnemonic phrases using AES-GCM and PBKDF2. These tests validate encryption,
decryption, file handling, and exception behavior.
"""
from __future__ import annotations

import base64
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.utils.custom_exception import CommonException
from src.utils.wallet_credential_encryption import MnemonicStore


@patch('src.utils.wallet_credential_encryption.os.urandom')
@patch('src.utils.wallet_credential_encryption.AESGCM')
def test_encrypt_success(mock_aesgcm_class, mock_urandom):
    """
    Test that the encrypt method returns correctly encoded encrypted data
    using mocked salt, nonce, and AESGCM behavior.
    """
    password = 'test-password'
    mnemonic = 'test mnemonic phrase'

    # Mock os.urandom to return deterministic values
    mock_urandom.side_effect = [b'salt_123456789012', b'nonce_12345678']
    mock_aesgcm = MagicMock()
    mock_aesgcm.encrypt.return_value = b'ciphertext'
    mock_aesgcm_class.return_value = mock_aesgcm

    store = MnemonicStore()
    encrypted = store.encrypt(password, mnemonic)

    expected = base64.b64encode(
        b'salt_123456789012' + b'nonce_12345678' + b'ciphertext',
    )
    assert encrypted == expected
    mock_aesgcm.encrypt.assert_called_once()


@patch('src.utils.wallet_credential_encryption.Path')
@patch('src.utils.wallet_credential_encryption.AESGCM')
def test_decrypt_success(mock_aesgcm_class, mock_path_class):
    """
    Test that decrypt successfully decodes a valid encrypted file
    and returns the mnemonic using correct credentials.
    """
    password = 'test-password'
    mnemonic = 'secret phrase'
    salt = b'1234567890123456'
    nonce = b'123456789012'
    ciphertext = b'encrypted_data'
    encrypted_data = base64.b64encode(salt + nonce + ciphertext)

    mock_path = MagicMock()
    mock_path.is_file.return_value = True
    mock_path.read_bytes.return_value = encrypted_data
    mock_path_class.return_value = mock_path

    mock_aesgcm = MagicMock()
    mock_aesgcm.decrypt.return_value = mnemonic.encode()
    mock_aesgcm_class.return_value = mock_aesgcm

    store = MnemonicStore()
    result = store.decrypt(password, 'fake_path')

    assert result == mnemonic
    assert store.decrypted_mnemonic == mnemonic
    assert store._path == 'fake_path'
    assert store._password == password


@patch('src.utils.wallet_credential_encryption.Path')
def test_decrypt_file_not_found(mock_path_class):
    """
    Test that decrypt raises a CommonException when the file path does not exist.
    """
    password = 'test'
    mock_path = MagicMock()
    mock_path.is_file.return_value = False
    mock_path_class.return_value = mock_path

    store = MnemonicStore()

    with pytest.raises(CommonException) as exc:
        store.decrypt(password, 'nonexistent')

    assert 'The provided password is incorrect' in str(exc.value)


@patch('src.utils.wallet_credential_encryption.Path')
@patch('src.utils.wallet_credential_encryption.AESGCM')
def test_decrypt_invalid_password(mock_aesgcm_class, mock_path_class):
    """
    Test that decrypt raises a CommonException when AESGCM fails due to an invalid password.
    """
    password = 'wrong-pass'
    salt = b'1234567890123456'
    nonce = b'123456789012'
    ciphertext = b'encrypted_data'
    encrypted_data = base64.b64encode(salt + nonce + ciphertext)

    mock_path = MagicMock()
    mock_path.is_file.return_value = True
    mock_path.read_bytes.return_value = encrypted_data
    mock_path_class.return_value = mock_path

    mock_aesgcm = MagicMock()
    mock_aesgcm.decrypt.side_effect = 'The provided password is incorrect'
    mock_aesgcm_class.return_value = mock_aesgcm

    store = MnemonicStore()

    with pytest.raises(CommonException) as exc:
        store.decrypt(password, 'fake_path')

    assert 'The provided password is incorrect' in str(exc.value)
    assert store.decrypted_mnemonic is None
    assert store._path is None
    assert store._password is None
