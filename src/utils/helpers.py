"""
Utility functions for handling various operations in the application.

These functions provide functionalities such as address shortening, stylesheet loading,
pixmap creation, Google Auth token checking, mnemonic hashing and validation, port checking,
and retrieving configuration arguments for wallet setup.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys

from mnemonic import Mnemonic
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPixmap
from rgb_lib import BitcoinNetwork

from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import ConfigModel
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import INDEXER_URL_MAINNET
from src.utils.constant import INDEXER_URL_REGTEST
from src.utils.constant import INDEXER_URL_TESTNET
from src.utils.constant import PROXY_ENDPOINT_MAINNET
from src.utils.constant import PROXY_ENDPOINT_REGTEST
from src.utils.constant import PROXY_ENDPOINT_TESTNET
from src.utils.constant import SAVED_INDEXER_URL
from src.utils.constant import SAVED_PROXY_ENDPOINT
from src.utils.custom_exception import CommonException
from src.utils.gauth import TOKEN_PICKLE_PATH
from src.utils.logging import logger


def handle_asset_address(address: str, short_len: int = 12) -> str:
    """
    Shortens the given address for display.

    Parameters:
    address (str): The full address to be shortened.
    short_len (int): The number of characters to keep from the start and end of the address. Default is 12.

    Returns:
    str: The shortened address with the first `short_len` and last `short_len` characters displayed.
    """
    new_address = str(address)
    shortened_address = f'{new_address[:short_len]}...{
        new_address[-short_len:]
    }'
    return shortened_address


def load_stylesheet(file: str = 'views/qss/style.qss') -> str:
    """
    Loads the QSS stylesheet from the specified file.

    Parameters:
    file (str): The relative path to the QSS file. Defaults to "views/qss/style.qss".

    Returns:
    str: The content of the QSS file as a string.

    Raises:
    FileNotFoundError: If the QSS file is not found at the specified path.
    """
    if getattr(sys, 'frozen', False):
        # If the application is frozen (compiled with PyInstaller)
        base_path = getattr(
            sys,
            '_MEIPASS',
            os.path.dirname(os.path.abspath(__file__)),
        )
        qss_folder_path = os.path.join(base_path, 'views/qss')
        filename = os.path.basename(file)
        file = os.path.join(qss_folder_path, filename)
    else:
        if not os.path.isabs(file):
            # Get the directory of the current script (helpers.py)
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Construct the full path to the QSS file relative to the script's location
            file = os.path.join(base_path, '..', file)

    try:
        with open(file, encoding='utf-8') as _f:
            stylesheet = _f.read()
        return stylesheet
    except FileNotFoundError:
        logger.error("Error: Stylesheet file '%s' not found.", file)
        raise


def create_circular_pixmap(diameter: int, color: QColor) -> QPixmap:
    """
    Create a circular pixmap with a transparent background.

    This function generates a circular pixmap of the specified diameter,
    filled with the given color, and with a transparent background.
    The resulting pixmap can be used for various graphical purposes
    within a Qt application, such as creating custom icons or buttons with circular shapes.

    Parameters:
    diameter (int): The diameter of the circular pixmap to be created.
    color (QColor): The color to fill the circular pixmap with.

    Returns:
    QPixmap: The generated circular pixmap with the specified color and transparent background.
    """
    pixmap = QPixmap(diameter, diameter)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.end()

    return pixmap


def check_google_auth_token_available() -> bool:
    """
    Check if the Google Auth token is available at the specified location.

    Returns:
    bool: True if the token file exists, False otherwise.
    """
    return os.path.exists(TOKEN_PICKLE_PATH)


def hash_mnemonic(mnemonic_phrase: str) -> str:
    """
    Hashes the given mnemonic phrase.

    Validates the mnemonic phrase and then hashes it using SHA-256,
    followed by Base32 encoding. The result is truncated to the first 10 characters.

    Parameters:
    mnemonic_phrase (str): The mnemonic phrase to be hashed.

    Returns:
    str: The hashed and encoded mnemonic.
    """
    validate_mnemonic(mnemonic_phrase=mnemonic_phrase)

    sha256_hash = hashlib.sha256(mnemonic_phrase.encode()).digest()
    base32_encoded = base64.b32encode(sha256_hash).decode().rstrip('=')

    return base32_encoded[:10]


def validate_mnemonic(mnemonic_phrase: str):
    """
    Validates the given mnemonic phrase.

    Parameters:
    mnemonic_phrase (str): The mnemonic phrase to be validated.

    Raises:
    ValueError: If the mnemonic phrase is invalid.
    """
    mnemonic = Mnemonic('english')
    if not mnemonic.check(mnemonic_phrase):
        raise ValueError('Invalid mnemonic phrase')


def get_build_info() -> dict | None:
    """Load build JSON file and return value in case of freeze."""
    if getattr(sys, 'frozen', False):
        base_path = getattr(
            sys, '_MEIPASS', os.path.dirname(
                os.path.abspath(__file__),
            ),
        )
        build_file_path = os.path.join(base_path, 'build_info.json')

        try:
            with open(build_file_path, encoding='utf-8') as build_file:
                data = json.load(build_file)
            return {
                'build_flavour': data.get('build_flavour'),
                'machine_arch': data.get('machine_arch'),
                'os_type': data.get('os_type'),
                'arch_type': data.get('arch_type'),
                'app-version': data.get('app-version'),
            }
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.error(
                'Exception occurred while get_build_info: %s, Message: %s', type(
                    exc,
                ).__name__, str(exc),
            )
            return None
    # In case of not frozen and not executable return None
    return None


def get_bitcoin_config(network: BitcoinNetwork, password) -> ConfigModel:
    """
    Retrieves and configures Bitcoin wallet settings for the specified network.

    This function maps network-specific configurations (indexer URL and proxy endpoint)
    and combines them with user credentials to create a complete wallet configuration.

    Args:
        network (BitcoinNetwork): The Bitcoin network type (MAINNET, TESTNET, or REGTEST).
        password (str): The wallet password for authentication.

    Returns:
        ConfigModel: A configuration model containing network settings and credentials.

    Raises:
        Exception: If configuration retrieval or processing fails.
    """
    try:

        # Network-specific configurations
        config_mapping = {
            BitcoinNetwork.MAINNET: {
                SAVED_INDEXER_URL: INDEXER_URL_MAINNET,
                SAVED_PROXY_ENDPOINT: PROXY_ENDPOINT_MAINNET,
            },
            BitcoinNetwork.TESTNET: {
                SAVED_INDEXER_URL: INDEXER_URL_TESTNET,
                SAVED_PROXY_ENDPOINT: PROXY_ENDPOINT_TESTNET,
            },
            BitcoinNetwork.REGTEST: {
                SAVED_INDEXER_URL: INDEXER_URL_REGTEST,
                SAVED_PROXY_ENDPOINT: PROXY_ENDPOINT_REGTEST,
            },
        }
        # Retrieve the appropriate configuration based on the network
        network_config = config_mapping.get(network) or {}
        dynamic_config = {}
        for key, value in network_config.items():
            dynamic_config[key] = SettingRepository.get_config_value(
                key, value,
            )

        # Create and return the UnlockRequestModel
        bitcoin_config = ConfigModel(
            indexer_url=dynamic_config[SAVED_INDEXER_URL],
            proxy_endpoint=dynamic_config[SAVED_PROXY_ENDPOINT],
            password=password,
            network=network,
        )
        return bitcoin_config
    except Exception as exc:
        raise exc


def get_bitcoin_network_from_enum(network: NetworkEnumModel | BitcoinNetwork) -> BitcoinNetwork:
    """Map a NetworkEnumModel to its corresponding BitcoinNetwork."""
    if isinstance(network, BitcoinNetwork):
        return network

    mapping = {
        NetworkEnumModel.MAINNET: BitcoinNetwork.MAINNET,
        NetworkEnumModel.TESTNET: BitcoinNetwork.TESTNET,
        NetworkEnumModel.REGTEST: BitcoinNetwork.REGTEST,
    }

    try:
        return mapping[network]
    except KeyError as e:
        raise CommonException('Invalid network') from e
