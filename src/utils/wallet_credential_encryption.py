"""
This module provides secure storage and retrieval of a mnemonic phrase using AES-GCM encryption.
The mnemonic is encrypted with a password-derived key using PBKDF2, and stored as a base64-encoded
file. It includes caching to avoid redundant decryption for repeated accesses with the same credentials.

Classes:
    MnemonicStore: Handles encryption, decryption, and caching of the mnemonic.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_PASSWORD_INCORRECT


class MnemonicStore:
    """
    A utility class for securely encrypting and decrypting a mnemonic phrase
    using AES-GCM and PBKDF2 password-based key derivation.

    Attributes:
        iterations (int): Number of PBKDF2 iterations (default: 100,000).
        key_length (int): AES key length in bytes (default: 32 for AES-256).
        decrypted_mnemonic (str | None): Cached decrypted mnemonic.
        _path (str | None): Cached file path of last successful decryption.
        _password (str | None): Cached password of last successful decryption.
    """

    def __init__(self, iterations: int = 100_000, key_length: int = 32):
        self.iterations = iterations
        self.key_length = key_length
        self.decrypted_mnemonic: str | None = None
        self._path: str | None = None
        self._password: str | None = None

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive a symmetric encryption key from a password and salt using PBKDF2.

        Args:
            password (str): The password to derive the key from.
            salt (bytes): A 16-byte salt value.

        Returns:
            bytes: The derived AES encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
        )
        return kdf.derive(password.encode())

    def encrypt(self, password: str, mnemonic: str) -> bytes:
        """
        Encrypts the given mnemonic using the provided password.

        Args:
            password (str): The password to use for encryption.
            mnemonic (str): The plaintext mnemonic phrase.

        Returns:
            bytes: The base64-encoded encrypted data.

        Raises:
            CommonException: If encryption fails due to invalid input or internal error.
        """
        try:
            if not password or not mnemonic:
                raise ValueError('Password and mnemonic must not be empty.')

            salt = os.urandom(16)
            nonce = os.urandom(12)
            key = self.derive_key(password, salt)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, mnemonic.encode(), None)
            return base64.b64encode(salt + nonce + ciphertext)

        except Exception as exc:
            raise CommonException(
                'Encryption failed', {
                    'name': type(exc).__name__,
                    'original_exception': str(exc),
                },
            ) from exc

    def decrypt(self, password: str, path: str) -> str | None:
        """
        Decrypts the mnemonic stored in the specified path using the provided password.
        Uses caching to avoid repeated decryption if credentials match.

        Args:
            password (str): The password used for decryption.
            path (str): Path to the base64-encoded encrypted mnemonic file.

        Returns:
            str: The decrypted mnemonic phrase.

        Raises:
            CommonException: If decryption fails due to incorrect password or data format.
        """
        if (
            self.decrypted_mnemonic is not None and
            self._password == password and
            self._path == path
        ):
            return self.decrypted_mnemonic  # Return cached result

        try:
            if not Path(path).is_file():
                raise FileNotFoundError(f"No file found at path: {path}")

            data = base64.b64decode(Path(path).read_bytes())
            salt, nonce, ciphertext = data[:16], data[16:28], data[28:]
            key = self.derive_key(password, salt)
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            self.decrypted_mnemonic = plaintext.decode()
            self._password = password
            self._path = path
            return self.decrypted_mnemonic

        except Exception as exc:
            self.decrypted_mnemonic = None
            self._path = None
            self._password = None
            raise CommonException(
                ERROR_PASSWORD_INCORRECT, {
                    'name': type(exc).__name__,
                    'original_exception': str(exc),
                },
            ) from exc


# Singleton instance for global usage
mnemonic_store = MnemonicStore()
