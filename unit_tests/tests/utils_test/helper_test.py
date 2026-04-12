# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments
"""unit tests for helper.py"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QPushButton
from rgb_lib import BitcoinNetwork
from rgb_lib import MultisigKeys

from src.model.common_operation_model import ConfigModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.utils.custom_exception import CommonException
from src.utils.helpers import build_keys_from_data
from src.utils.helpers import check_google_auth_token_available
from src.utils.helpers import connect_multisig_pending_signal
from src.utils.helpers import create_circular_pixmap
from src.utils.helpers import get_bitcoin_config
from src.utils.helpers import get_bitcoin_network_from_enum
from src.utils.helpers import get_build_info
from src.utils.helpers import handle_asset_address
from src.utils.helpers import hash_mnemonic
from src.utils.helpers import load_stylesheet
from src.utils.helpers import read_rgb_lib_version_file
from src.utils.helpers import register_multisig_button
from src.utils.helpers import set_widgets_visible
from src.utils.helpers import validate_mnemonic
from src.utils.helpers import validate_xpub
from src.utils.helpers import write_rgb_lib_version_file


# Constants for mocking
MOCK_INDEXER_URL = 'mock_indexer_url'
MOCK_PROXY_ENDPOINT = 'mock_proxy_endpoint'
MOCK_PASSWORD = 'mock_password'
SAVED_INDEXER_URL = 'saved_indexer_url'
SAVED_PROXY_ENDPOINT = 'saved_proxy_endpoint'


@pytest.fixture
def mock_token_file():
    """Fixture to create a temporary file to simulate a token file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'token data')
        temp_file.flush()
        yield temp_file.name
        os.remove(temp_file.name)


@pytest.fixture
def mock_local_store():
    """Fixture to mock the local_store used in utility functions."""
    with patch('src.utils.helpers.local_store') as mock:
        yield mock


def test_handle_asset_address():
    """Test the `handle_asset_address` function to ensure it correctly shortens the address."""
    address = '1234567890abcdef'
    short_len = 4
    expected = '1234...cdef'
    assert handle_asset_address(address, short_len) == expected


def test_check_google_auth_token_available(mock_token_file):
    """Test the `check_google_auth_token_available` function to ensure it returns True when the token file is available."""
    with patch('src.utils.helpers.TOKEN_PICKLE_PATH', mock_token_file):
        assert check_google_auth_token_available() is True


def test_hash_mnemonic():
    """Test the `hash_mnemonic` function to ensure it returns a hashed mnemonic of the expected length."""
    mnemonic_phrase = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
    hashed = hash_mnemonic(mnemonic_phrase)
    assert len(hashed) == 10


def test_validate_mnemonic_valid():
    """Test the `validate_mnemonic` function to ensure it does not raise an error for a valid mnemonic phrase."""
    mnemonic_phrase = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
    try:
        validate_mnemonic(mnemonic_phrase)
    except ValueError:
        pytest.fail('validate_mnemonic raised ValueError unexpectedly!')


def test_validate_mnemonic_invalid():
    """Test the `validate_mnemonic` function to ensure it raises a ValueError for an invalid mnemonic phrase."""
    mnemonic_phrase = 'invalid mnemonic phrase'
    with pytest.raises(ValueError):
        validate_mnemonic(mnemonic_phrase)


def test_get_build_info(mocker):
    """Test the `get_build_info` function to ensure it correctly parses and returns the build information."""
    build_info = {
        'build_flavour': 'release',
        'machine_arch': 'x86_64',
        'os_type': 'Linux',
        'arch_type': 'x86_64',
        'app-version': '1.0.0',
    }

    mocker.patch('builtins.open', mock_open(read_data=json.dumps(build_info)))

    with patch('src.utils.helpers.sys') as mock_sys:
        mock_sys.frozen = True

        with patch('src.utils.helpers.logger') as mock_logger:
            result = get_build_info()
            assert result == build_info
            mock_logger.error.assert_not_called()


def test_get_build_info_when_none_return(mocker):
    """Test the `get_build_info` function to ensure it returns None when the build info file is not found."""
    mocker.patch('builtins.open', side_effect=FileNotFoundError)
    with mocker.patch('src.utils.helpers.logger'):
        result = get_build_info()
        assert result is None


def test_load_stylesheet_success(mocker):
    """Test load_stylesheet_success helper."""
    qss_content = 'QWidget { background-color: #000; }'
    mocker.patch('builtins.open', mock_open(read_data=qss_content))
    mocker.patch('os.path.isabs', return_value=False)
    mocker.patch('os.path.abspath', return_value='/mock/path/helpers.py')
    mocker.patch('os.path.dirname', return_value='/mock/path')
    mocker.patch('os.path.join', return_value='/mock/path/views/qss/style.qss')
    result = load_stylesheet()
    assert result == qss_content


def test_load_stylesheet_file_not_found(mocker):
    """Test when file not found."""
    mocker.patch('builtins.open', side_effect=FileNotFoundError)
    mocker.patch('os.path.isabs', return_value=False)
    mocker.patch('os.path.abspath', return_value='/mock/path/helpers.py')
    mocker.patch('os.path.dirname', return_value='/mock/path')
    mocker.patch('os.path.join', return_value='/mock/path/views/qss/style.qss')
    with pytest.raises(FileNotFoundError):
        load_stylesheet()


def test_load_stylesheet_frozen(mocker):
    """Test the `load_stylesheet` function to ensure it correctly loads and returns a stylesheet."""
    with patch('src.utils.helpers.sys') as mock_sys:
        mock_sys.frozen = True
        qss_content = 'QWidget { background-color: #000; }'
        mocker.patch('builtins.open', mock_open(read_data=qss_content))
        mocker.patch(
            'os.path.join',
            return_value='/frozen/path/views/qss/style.qss',
        )
        result = load_stylesheet()
        assert result == qss_content


def test_load_stylesheet_non_absolute_path(mocker):
    """Load stylesheet when non absolute path."""
    qss_content = 'QWidget { background-color: #000; }'
    mocker.patch('builtins.open', mock_open(read_data=qss_content))
    mocker.patch('os.path.isabs', return_value=False)
    mocker.patch('os.path.abspath', return_value='/mock/path/helpers.py')
    mocker.patch('os.path.dirname', return_value='/mock/path')
    mocker.patch('os.path.join', return_value='/mock/path/views/qss/style.qss')
    result = load_stylesheet(file='views/qss/style.qss')
    assert result == qss_content


@patch('src.utils.helpers.Qt')
@patch('src.utils.helpers.QPixmap')
@patch('src.utils.helpers.QPainter')
@patch('src.utils.helpers.QColor')
def test_create_circular_pixmap(mock_qcolor, mock_qpainter, mock_qpixmap, mock_qt):
    """Test the `create_circular_pixmap` function to ensure it returns a circular QPixmap."""
    mock_qt.NoPen = 'NoPenValue'
    mock_qt.transparent = 'TransparentValue'
    mock_qpainter.Antialiasing = 'AntialiasingValue'

    diameter = 100
    color = mock_qcolor
    mock_pixmap_instance = MagicMock()
    mock_qpixmap.return_value = mock_pixmap_instance
    mock_painter_instance = MagicMock()
    mock_qpainter.return_value = mock_painter_instance

    result = create_circular_pixmap(diameter, color)
    mock_qpixmap.assert_called_once_with(diameter, diameter)
    mock_pixmap_instance.fill.assert_called_once_with('TransparentValue')
    mock_qpainter.assert_called_once_with(mock_pixmap_instance)
    mock_painter_instance.setRenderHint.assert_called_once_with(
        'AntialiasingValue',
    )
    mock_painter_instance.setBrush.assert_called_once_with(color)
    mock_painter_instance.setPen.assert_called_once_with('NoPenValue')
    mock_painter_instance.drawEllipse.assert_called_once_with(
        0, 0, diameter, diameter,
    )
    mock_painter_instance.end.assert_called_once()
    assert result == mock_pixmap_instance


@pytest.mark.parametrize(
    'network_enum, expected_network', [
        (NetworkEnumModel.MAINNET, BitcoinNetwork.MAINNET),
        (NetworkEnumModel.TESTNET, BitcoinNetwork.TESTNET),
        (NetworkEnumModel.REGTEST, BitcoinNetwork.REGTEST),
        # Already BitcoinNetwork
        (BitcoinNetwork.MAINNET, BitcoinNetwork.MAINNET),
    ],
)
def test_get_bitcoin_network_from_enum_valid(network_enum, expected_network):
    """Test valid conversions from network enum to BitcoinNetwork."""
    result = get_bitcoin_network_from_enum(network_enum)
    assert result == expected_network


def test_get_bitcoin_network_from_enum_invalid():
    """Test that invalid network raises CommonException."""
    with pytest.raises(CommonException, match='Invalid network'):
        get_bitcoin_network_from_enum('invalid_network')


@pytest.mark.parametrize(
    'network_str', ['mainnet', 'testnet', 'regtest'],
)
def test_get_bitcoin_config(network_str, mocker):
    """Test get_bitcoin_config returns correct config for each network."""
    # Create network instance
    if network_str == 'mainnet':
        network = BitcoinNetwork.MAINNET
    elif network_str == 'testnet':
        network = BitcoinNetwork.TESTNET
    else:
        network = BitcoinNetwork.REGTEST

    # Mock SettingRepository.get_config_value
    mocker.patch(
        'src.utils.helpers.SettingRepository.get_config_value',
        side_effect=[MOCK_INDEXER_URL, MOCK_PROXY_ENDPOINT],
    )

    config = get_bitcoin_config(network, MOCK_PASSWORD)

    assert isinstance(config, ConfigModel)
    assert config.indexer_url == MOCK_INDEXER_URL
    assert config.proxy_endpoint == MOCK_PROXY_ENDPOINT
    assert config.password == MOCK_PASSWORD
    assert config.network == network


def test_validate_xpub_valid():
    """validate_xpub should return True when BIP32.from_xpub does not raise."""
    with patch('src.utils.helpers.BIP32.from_xpub', return_value=object()):
        assert validate_xpub('xpub6CUGRUonZSQ4TWtTMmzXdrXDtypWKiKp') is True


def test_validate_xpub_invalid():
    """validate_xpub should return False when BIP32.from_xpub raises."""
    with patch('src.utils.helpers.BIP32.from_xpub', side_effect=Exception('bad')):
        assert validate_xpub('invalid') is False


@patch('src.utils.helpers.SettingRepository.get_rgb_lib_version', return_value='1.2.3')
def test_write_rgb_lib_version_file_success(_mock_get_version, mocker):
    """write_rgb_lib_version_file writes version and returns (path, name)."""
    mocker.patch('src.utils.helpers.app_paths.backup_folder_path', '/tmp')
    m = mock_open()
    mocker.patch('builtins.open', m)

    path, name = write_rgb_lib_version_file('wallet')

    assert name == 'wallet.version'
    assert path.endswith('/tmp/wallet.version')
    m.assert_called_once()
    handle = m()
    handle.write.assert_called_once_with('1.2.3')


def test_write_rgb_lib_version_file_oserror(mocker):
    """write_rgb_lib_version_file should wrap OSError in RuntimeError."""
    mocker.patch('src.utils.helpers.app_paths.backup_folder_path', '/tmp')
    mocker.patch('builtins.open', side_effect=OSError('disk full'))

    with pytest.raises(RuntimeError) as exc:
        write_rgb_lib_version_file('wallet')
    assert 'Failed to write version file' in str(exc.value)


def test_read_rgb_lib_version_file_success(mocker):
    """read_rgb_lib_version_file returns file content."""
    mocker.patch('src.utils.helpers.app_paths.restore_folder_path', '/tmp')
    m = mock_open(read_data='2.0.1')
    mocker.patch('builtins.open', m)

    val = read_rgb_lib_version_file('wallet.version')
    assert val == '2.0.1'


def test_read_rgb_lib_version_file_not_found(mocker):
    """read_rgb_lib_version_file returns 'unknown' if file missing."""
    mocker.patch('src.utils.helpers.app_paths.restore_folder_path', '/tmp')
    mocker.patch('builtins.open', side_effect=FileNotFoundError)

    val = read_rgb_lib_version_file('wallet.version')
    assert val == 'unknown'


def test_read_rgb_lib_version_file_oserror(mocker):
    """read_rgb_lib_version_file wraps OSError in RuntimeError."""
    mocker.patch('src.utils.helpers.app_paths.restore_folder_path', '/tmp')
    mocker.patch('builtins.open', side_effect=OSError('perm'))

    with pytest.raises(RuntimeError) as exc:
        read_rgb_lib_version_file('wallet.version')
    assert 'Failed to read version file' in str(exc.value)


def test_get_build_info_json_decode_error(mocker):
    """get_build_info returns None and logs on JSONDecodeError when frozen."""
    # simulate frozen app
    with patch('src.utils.helpers.sys') as mock_sys:
        mock_sys.frozen = True
        # make open return bad json and json.load raise JSONDecodeError
        m = mock_open(read_data='{bad json')
        mocker.patch('builtins.open', m)
        with patch('src.utils.helpers.logger') as mock_logger:
            # patch json.load to raise JSONDecodeError explicitly
            with patch('json.load', side_effect=json.JSONDecodeError('msg', 'doc', 0)):
                assert get_build_info() is None
                mock_logger.error.assert_called_once()


@patch('src.utils.helpers.SettingRepository')
def test_hash_mnemonic_multisig(mock_setting_repo):
    """Test hash_mnemonic for hardware/watch-only wallets."""
    # Return enums directly
    mock_setting_repo.get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET
    mock_setting_repo.get_wallet_access_type.return_value = WalletAccessType.WATCH_ONLY

    with patch('src.utils.helpers.validate_xpub', return_value=True) as mock_validate:
        xpub = 'tpubD6NzVbtR7TQ39BH8i8H7S86t65s46s789a...'
        hash_mnemonic(xpub)
        mock_validate.assert_called_once_with(xpub)


@patch('src.utils.helpers.SettingRepository')
def test_build_keys_from_data_singlesig(mock_setting_repo):
    """Test build_keys_from_data for singlesig wallet."""
    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.STANDARD_TYPE_WALLET

    with patch('src.utils.helpers.SinglesigKeys') as mock_keys:
        build_keys_from_data('v_xpub', 'c_xpub', 'fp', 'mnemonic', 1)
        mock_keys.assert_called_once()


@patch('src.utils.helpers.SettingRepository')
def test_build_keys_from_data_multisig(mock_setting_repo):
    """Test build_keys_from_data for multisig wallet."""
    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_setting_repo.get_multisig_config.return_value = (2, 3)

    cosigners = [
        {
            'account_xpub_vanilla': 'v2', 'account_xpub_colored': 'c2',
            'master_fingerprint': 'fp2',
        },
        {
            'account_xpub_vanilla': 'v3', 'account_xpub_colored': 'c3',
            'master_fingerprint': 'fp3',
        },
    ]
    mock_setting_repo.get_cosigners.return_value = cosigners

    keys = build_keys_from_data('v1', 'c1', 'fp1')
    assert isinstance(keys, MultisigKeys)
    assert len(keys.cosigners) == 3


def test_set_widgets_visible():
    """Test set_widgets_visible including exception paths."""
    w1 = MagicMock()
    w2 = MagicMock()
    w2.setVisible.side_effect = Exception('err')

    set_widgets_visible([w1, w2, None], True)
    w1.setVisible.assert_called_with(True)
    w2.show.assert_called_once()

    w3 = MagicMock()
    w3.setVisible.side_effect = Exception('err')
    set_widgets_visible([w3], False)
    w3.hide.assert_called_once()


def test_connect_multisig_pending_signal():
    """Test connect_multisig_pending_signal success and failure."""
    vm = MagicMock()
    cb = MagicMock()

    connect_multisig_pending_signal(vm, cb)
    vm.header_frame_view_model.multisig_pending_state_changed.connect.assert_called_once_with(
        cb,
    )
    cb.assert_called_once_with(vm.header_frame_view_model.is_multisig_pending)

    # Failure path
    connect_multisig_pending_signal(None, cb)  # Should not raise


def test_register_multisig_button():
    """Test register_multisig_button with various states."""

    btn = MagicMock(spec=QPushButton)
    vm = MagicMock()
    # Explicitly set to False to start in normal state
    vm.header_frame_view_model.is_multisig_pending = False
    handler = MagicMock()

    # Track property values to simulate Qt behavior
    property_values = {}

    def mock_set_property(key, value):
        property_values[key] = value

    def mock_get_property(key):
        return property_values.get(key)

    btn.setProperty.side_effect = mock_set_property
    btn.property.side_effect = mock_get_property

    register_multisig_button(vm, btn, handler)
    btn.clicked.connect.assert_called_with(handler)

    # Simulate signal update
    callback = vm.header_frame_view_model.multisig_pending_state_changed.connect.call_args[
        0
    ][0]

    # Switch to pending
    callback(True)
    btn.clicked.disconnect.assert_called_with()
    btn.setProperty.assert_called_with('pending', 'true')

    # Switch back
    callback(False)
    btn.setProperty.assert_called_with('pending', 'false')


@patch('src.utils.helpers.SettingRepository')
def test_get_bitcoin_config_invalid_network(mock_setting_repo):
    """Test get_bitcoin_config with an unknown network."""
    # Signet is not handled in the if/elif chain
    config = get_bitcoin_config(BitcoinNetwork.SIGNET, 'pass')
    assert isinstance(config, ConfigModel)
    assert config.indexer_url == ''
    assert config.proxy_endpoint == ''


@patch('src.utils.helpers.SettingRepository')
def test_build_keys_from_data_multisig_errors(mock_setting_repo):
    """Test build_keys_from_data multisig error paths."""
    mock_setting_repo.get_wallet_signature_type.return_value = WalletSignatureType.MULTI_SIG_WALLET

    # Case: Multisig config not set
    mock_setting_repo.get_multisig_config.return_value = (None, None)
    with pytest.raises(CommonException, match='Multisig configuration not set.'):
        build_keys_from_data('v', 'c', 'fp')

    # Case: Mismatched cosigners count
    mock_setting_repo.get_multisig_config.return_value = (2, 3)
    mock_setting_repo.get_cosigners.return_value = []  # Expected 2
    with pytest.raises(CommonException, match='Expected 2 cosigners, found 0.'):
        build_keys_from_data('v', 'c', 'fp')


def test_set_widgets_visible_extreme_failure():
    """Test set_widgets_visible when even show/hide fails."""
    w = MagicMock()
    w.setVisible.side_effect = Exception('err1')
    w.show.side_effect = Exception('err2')
    # Should not raise exception
    set_widgets_visible([w], True)


def test_register_multisig_button_not_pushbutton():
    """Test register_multisig_button with a non-QPushButton."""
    register_multisig_button(
        MagicMock(), MagicMock(),
        MagicMock(),
    )  # Should return early


@patch('src.utils.helpers.ToastManager')
def test_register_multisig_button_pending_handler(mock_toast):
    """Test the default pending handler in register_multisig_button."""
    btn = MagicMock(spec=QPushButton)
    vm = MagicMock()
    register_multisig_button(vm, btn, MagicMock())

    callback = vm.header_frame_view_model.multisig_pending_state_changed.connect.call_args[
        0
    ][0]
    callback(True)  # Set to pending

    # Trigger click
    handler = btn.clicked.connect.call_args[0][0]
    handler()
    mock_toast.info.assert_called_once()


def test_connect_multisig_pending_signal_exception():
    """Test connect_multisig_pending_signal when an exception occurs."""
    vm = MagicMock()
    vm.header_frame_view_model.multisig_pending_state_changed.connect.side_effect = Exception(
        'signal error',
    )
    with patch('src.utils.helpers.logger') as mock_logger:
        connect_multisig_pending_signal(vm, MagicMock())
        mock_logger.error.assert_called_once()


def test_register_multisig_button_redundant_handler():
    """Test register_multisig_button skips redundant connections."""
    btn = MagicMock(spec=QPushButton)
    vm = MagicMock()
    # Ensure is_multisig_pending is False to match normal_handler
    vm.header_frame_view_model.is_multisig_pending = False
    handler = MagicMock()

    # Track property values to simulate Qt behavior
    property_values = {}

    def mock_set_property(key, value):
        property_values[key] = value

    def mock_get_property(key):
        return property_values.get(key)

    btn.setProperty.side_effect = mock_set_property
    btn.property.side_effect = mock_get_property

    register_multisig_button(vm, btn, handler)
    # 1 from initial connect, 0 from state_update_callback (early return)
    assert btn.clicked.connect.call_count == 1


def test_register_multisig_button_disconnect_error():
    """Test register_multisig_button handles disconnect errors."""
    btn = MagicMock(spec=QPushButton)
    vm = MagicMock()
    handler = MagicMock()

    register_multisig_button(vm, btn, handler)
    btn.clicked.disconnect.side_effect = TypeError('not connected')

    callback = vm.header_frame_view_model.multisig_pending_state_changed.connect.call_args[
        0
    ][0]
    # Should not raise
    callback(True)
