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

from bip32 import BIP32
from mnemonic import Mnemonic
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QWidget
from rgb_lib import BitcoinNetwork
from rgb_lib import CosignerData
from rgb_lib import MultisigKeys
from rgb_lib import SinglesigKeys

from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import ConfigModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.utils.build_app_path import app_paths
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import INDEXER_URL_MAINNET
from src.utils.constant import INDEXER_URL_REGTEST
from src.utils.constant import INDEXER_URL_TESTNET
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import PROXY_ENDPOINT_MAINNET
from src.utils.constant import PROXY_ENDPOINT_REGTEST
from src.utils.constant import PROXY_ENDPOINT_TESTNET
from src.utils.constant import SAVED_INDEXER_URL
from src.utils.constant import SAVED_PROXY_ENDPOINT
from src.utils.custom_exception import CommonException
from src.utils.gauth import TOKEN_PICKLE_PATH
from src.utils.logging import logger
from src.views.components.toast import ToastManager


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
    if SettingRepository.get_key_storage_type() == KeyStorageType.HARDWARE_WALLET or \
            SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY:
        validate_xpub(mnemonic_phrase)
    else:
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


def validate_xpub(xpub: str) -> bool:
    """
    Returns True if the xpub is valid, False otherwise.
    Uses bip32 to parse and validate the key structure.
    """
    try:
        _ = BIP32.from_xpub(xpub)
        return True
    except Exception:
        return False


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
        network_config = config_mapping.get(type(network)) or {}
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
        NetworkEnumModel.MAINNET: BitcoinNetwork.MAINNET(),
        NetworkEnumModel.TESTNET: BitcoinNetwork.TESTNET(),
        NetworkEnumModel.TESTNET4: BitcoinNetwork.TESTNET4(),
        NetworkEnumModel.SIGNET: BitcoinNetwork.SIGNET(),
        NetworkEnumModel.REGTEST: BitcoinNetwork.REGTEST(),
    }

    try:
        return mapping[network]
    except KeyError as e:
        raise CommonException('Invalid network') from e


def write_rgb_lib_version_file(file_name: str) -> tuple[str, str]:
    """
    Write the rgb_lib version to a .version file in the same directory as the backup file.

    Args:
        file_name (str): The name to use for the version file (e.g., 'wallet.version').

    Returns:
        str: The full path to the created version file.
    """
    version = SettingRepository.get_rgb_lib_version()
    version_file_name = f'{file_name}.version'
    version_file_path = os.path.join(
        app_paths.backup_folder_path, version_file_name,
    )

    try:
        with open(version_file_path, 'w', encoding='utf-8') as f:
            f.write(version)
        return version_file_path, version_file_name
    except OSError as e:
        raise RuntimeError(f"Failed to write version file: {e}") from e


def read_rgb_lib_version_file(file_name: str) -> str:
    """
    Read the rgb_lib version from a .version file in the same directory as the backup file.

    Args:
        file_name (str): The name of the version file (e.g., 'wallet.version').
        backup_path (str): The full path to the backup file (used to derive the directory).

    Returns:
        str: The RGB library version if available, otherwise "unknown".
    """
    version_file_path = os.path.join(app_paths.restore_folder_path, file_name)

    try:
        with open(version_file_path, encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'unknown'
    except OSError as e:
        raise RuntimeError(f"Failed to read version file: {e}") from e


def build_keys_from_data(
    account_xpub_vanilla: str,
    account_xpub_colored: str,
    master_fingerprint: str,
    mnemonic: str | None = None,
    vanilla_keychain: int | None = None,
) -> SinglesigKeys | MultisigKeys:
    """Build SinglesigKeys or MultisigKeys based on wallet signature type."""
    is_multisig = (
        SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
    )

    if is_multisig:
        # Build MultisigKeys
        m, n = SettingRepository.get_multisig_config()
        if not m or not n:
            raise CommonException('Multisig configuration not set.')

        # Retrieve stored cosigners (cosigners 2, 3, ..., N)
        cosigners_data = SettingRepository.get_cosigners()
        if len(cosigners_data) != (n - 1):
            raise CommonException(
                f'Expected {n-1} cosigners, found {len(cosigners_data)}.',
            )

        # Build cosigners list: start with self (cosigner 1)
        cosigners = [
            CosignerData(
                account_xpub_vanilla=account_xpub_vanilla,
                account_xpub_colored=account_xpub_colored,
                vanilla_keychain=vanilla_keychain,
                master_fingerprint=master_fingerprint,
            ),
        ]

        # Add other cosigners from stored data
        for c in cosigners_data:
            cosigners.append(
                CosignerData(
                    account_xpub_vanilla=c[ACCOUNT_XPUB_VANILLA],
                    account_xpub_colored=c[ACCOUNT_XPUB_COLORED],
                    vanilla_keychain=c.get('vanilla_keychain'),
                    master_fingerprint=c[MASTER_FINGERPRINT],
                ),
            )

        return MultisigKeys(
            cosigners=cosigners,
            threshold_colored=m,
            threshold_vanilla=m,
        )

    # Build SinglesigKeys
    return SinglesigKeys(
        mnemonic=mnemonic,
        account_xpub_vanilla=account_xpub_vanilla,
        account_xpub_colored=account_xpub_colored,
        master_fingerprint=master_fingerprint,
        vanilla_keychain=vanilla_keychain if vanilla_keychain is not None else 1,
    )


def set_widgets_visible(widgets: list[QWidget | None], visible: bool) -> None:
    """
    Set the visibility of a list of widgets.
    """
    for widget in widgets:
        if widget is None:
            continue
        try:
            widget.setVisible(visible)
        except Exception:
            try:
                if visible:
                    widget.show()
                else:
                    widget.hide()
            except Exception:
                pass


def connect_multisig_pending_signal(view_model, update_callback):
    """
    Connects the multisig pending state signal to the provided callback.

    Args:
        view_model: The view model object (must have header_frame_view_model).
        update_callback: The method to call when state changes.
    """
    try:
        if view_model:
            view_model.header_frame_view_model.multisig_pending_state_changed.connect(
                update_callback,
            )
            # Initial update
            update_callback(
                view_model.header_frame_view_model.is_multisig_pending,
            )
    except Exception as e:
        logger.error('Failed to connect multisig pending signal: %s', e)


def register_multisig_button(
    view_model,
    button,
    normal_handler,
    pending_handler=None,
):
    """
    Registers a button to automatically react to multisig pending state changes.

    This helper encapsulates the entire setup: checking for multisig wallet type,
    connecting the signal, and handling the button state updates. It replaces
    manual connection logic in views.

    Args:
        view_model: The view model object.
        button: The QPushButton to manage.
        normal_handler: The function to call when button is clicked in normal state.
        pending_handler: Optional. Function to call when pending. Defaults to showing toast.
    """

    # Default to standard toast if no specific pending handler provided
    if pending_handler is None:
        def default_pending_handler():
            ToastManager.info(
                description='A multisig transaction is already pending or under review. '
                'Please complete it before creating a new transaction.',
            )
        pending_handler = default_pending_handler

    # Define the callback that will update the button state
    def state_update_callback(is_pending: bool):
        if not isinstance(button, QPushButton):
            return

        if is_pending:
            # Set pending property to trigger QSS [pending="true"] selector
            button.setProperty('pending', 'true')
            button.style().polish(button)
            # Disconnect all existing handlers
            try:
                button.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            # Connect pending handler
            button.clicked.connect(pending_handler)
        else:
            # Remove pending property to restore normal QSS styling
            button.setProperty('pending', 'false')
            button.style().polish(button)
            # Disconnect pending handler
            try:
                button.clicked.disconnect(pending_handler)
            except (TypeError, RuntimeError):
                pass
            # Reconnect normal handler if provided
            if normal_handler is not None:
                # Disconnect normal handler first to avoid duplicates
                try:
                    button.clicked.disconnect(normal_handler)
                except (TypeError, RuntimeError):
                    pass
                button.clicked.connect(normal_handler)

    # Connect the signal using the existing helper
    connect_multisig_pending_signal(view_model, state_update_callback)
