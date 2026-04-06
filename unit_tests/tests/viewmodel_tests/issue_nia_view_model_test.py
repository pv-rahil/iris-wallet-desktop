"""Unit test for issue NIA view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import Balance
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.viewmodels.issue_nia_view_model import IssueNIAViewModel

expected_issue_asset_nia_response_model = IssueAssetResponseModel(
    asset_id='asset_id',
    ticker='ticker',
    name='name',
    details='details',
    precision=2,
    issued_supply=1000,
    timestamp=123556789,
    added_at=123456789,
    balance=Balance(
            spendable=10, future=10, settled=12,
    ),
    media=None,
)


@pytest.fixture
def mock_page_navigation(mocker):
    """Fixture to create a mock page navigation object."""
    return mocker.MagicMock()


@pytest.fixture
def issue_nia_view_model(mock_page_navigation):
    """Fixture to create an instance of the IssueNIAViewModel class."""
    return IssueNIAViewModel(mock_page_navigation)


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.repository.rgb_repository.RgbRepository.issue_asset_nia')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_on_issue_click_success(
    mock_run_in_thread, mock_issue_asset_nia, mock_toast_error,
    issue_nia_view_model, mock_page_navigation,
):
    """Test for successful issuing of NIA asset."""
    # Mock the asset issuance response
    mock_issue_asset_nia.return_value = IssueAssetResponseModel(
        asset_id='asset_id',
        ticker='ticker',
        name='name',
        details='details',
        precision=2,
        issued_supply=4000,
        timestamp=123456789,
        added_at=123456789,
        balance=Balance(
            spendable=10, future=10, settled=12,
        ),
        media=None,
    )

    # Mock signals
    mock_issue_button_clicked = Mock()
    issue_nia_view_model.issue_button_clicked.connect(
        mock_issue_button_clicked,
    )

    # Mock worker
    mock_worker = MagicMock()
    issue_nia_view_model.worker = mock_worker
    mock_worker.result.emit = Mock()

    # Perform the action
    issue_nia_view_model.on_issue_click(
        'short_identifier', 'asset_name', '100',
    )

    # Simulate the successful callback from the worker
    mock_worker.result.emit(mock_issue_asset_nia.return_value)

    # Assertions
    mock_issue_button_clicked.assert_called_once()
    mock_toast_error.assert_not_called()


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.repository.rgb_repository.RgbRepository.issue_asset_nia')
@patch('src.data.repository.setting_repository.SettingRepository.native_authentication')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_on_success_native_auth(
    mock_run_in_thread, mock_native_authentication, mock_issue_asset_nia,
    mock_toast_error, issue_nia_view_model, mock_page_navigation,
):
    """Test for successful native authentication and asset issuance."""
    # Mock native authentication and asset issuance
    mock_native_authentication.return_value = True
    mock_issue_asset_nia.return_value = expected_issue_asset_nia_response_model

    # Connect signals to mocks
    mock_issue_button_clicked = MagicMock()
    issue_nia_view_model.issue_button_clicked.connect(
        mock_issue_button_clicked,
    )
    mock_is_issued = MagicMock()
    issue_nia_view_model.is_issued.connect(mock_is_issued)

    # Set test data
    issue_nia_view_model.token_amount = '100'
    issue_nia_view_model.asset_name = 'asset_name'
    issue_nia_view_model.short_identifier = 'short_identifier'

    # Simulate success callback for native authentication
    issue_nia_view_model.on_success_native_auth_nia(success=True)

    # Simulate worker behavior
    mock_worker = MagicMock()
    issue_nia_view_model.worker = mock_worker

    mock_worker.result.emit(mock_issue_asset_nia.return_value)
    mock_toast_error.assert_not_called()


def test_on_success_native_auth_generic_exception(
    issue_nia_view_model,
):
    """Test for handling generic Exception in on_success_native_auth."""
    # Setup
    with patch('src.views.components.toast.ToastManager.error') as mock_show_toast:

        # Trigger the exception
        issue_nia_view_model.on_success_native_auth_nia(success=False)

        # Verify the call to show_toast
        mock_show_toast.assert_called_once_with(
            description=ERROR_AUTHENTICATION_CANCELLED,
        )


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_nia_missing_value(mock_toast_manager, issue_nia_view_model):
    """Test on_success_native_auth_nia when fields are missing - should call _proceed_with_issue_nia which handles missing fields"""

    # Set all required attributes to None to trigger missing fields in _proceed_with_issue_nia
    issue_nia_view_model.token_amount = None
    issue_nia_view_model.asset_name = 'Test Asset'
    issue_nia_view_model.short_identifier = 'TEST'

    # on_success_native_auth_nia with success=True will call _proceed_with_issue_nia
    # which will raise CommonException for missing fields
    issue_nia_view_model.on_success_native_auth_nia(True)

    mock_toast_manager.assert_called_once_with(
        description='Few fields missing',
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_nia_exception(mock_toast_manager, issue_nia_view_model):
    """Test on_success_native_auth_nia when an unexpected exception occurs during _proceed_with_issue_nia"""
    issue_nia_view_model.issue_button_clicked = MagicMock()

    # Set required attributes
    issue_nia_view_model.token_amount = '100'
    issue_nia_view_model.asset_name = 'Test Asset'
    issue_nia_view_model.short_identifier = 'TEST'

    # Mock run_in_thread to raise an exception inside _proceed_with_issue_nia
    def mock_run_in_thread(*args, **kwargs):
        raise RuntimeError('Test exception')

    # Patch run_in_thread method
    with patch.object(issue_nia_view_model, 'run_in_thread', side_effect=mock_run_in_thread):
        issue_nia_view_model.on_success_native_auth_nia(True)

    mock_toast_manager.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    issue_nia_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error_native_auth_nia_common_exception(mock_toast_manager, issue_nia_view_model):
    """Test on_error_native_auth_nia with CommonException"""
    issue_nia_view_model.issue_button_clicked = MagicMock()
    test_message = 'Test error message'
    test_error = CommonException(message=test_message)

    issue_nia_view_model.on_error_native_auth_nia(test_error)

    mock_toast_manager.assert_called_once_with(description=test_message)
    issue_nia_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error_native_auth_nia_generic_exception(mock_toast_manager, issue_nia_view_model):
    """Test on_error_native_auth_nia with generic Exception"""
    issue_nia_view_model.issue_button_clicked = MagicMock()
    test_error = Exception('Test error')

    issue_nia_view_model.on_error_native_auth_nia(test_error)

    mock_toast_manager.assert_called_once_with(
        description=ERROR_SOMETHING_WENT_WRONG,
    )
    issue_nia_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


@patch('src.views.components.toast.ToastManager.error')
def test_on_error(mock_toast_manager, issue_nia_view_model):
    """Test on_error method for NIA issue page"""
    # Setup
    issue_nia_view_model.issue_button_clicked = MagicMock()
    test_message = 'Test error message'
    test_error = MagicMock()
    test_error.message = test_message

    # Execute
    issue_nia_view_model.on_error(test_error)

    # Assert
    mock_toast_manager.assert_called_once_with(description=test_message)
    issue_nia_view_model.issue_button_clicked.emit.assert_called_once_with(
        False,
    )


def test_on_success(mocker, issue_nia_view_model):
    """Test that on_success shows toast and emits correct signals."""
    # Arrange
    response = expected_issue_asset_nia_response_model

    # Create signal-connected mocks
    mock_issue_button_clicked = Mock()
    mock_is_issued = Mock()
    issue_nia_view_model.issue_button_clicked.connect(
        mock_issue_button_clicked,
    )
    issue_nia_view_model.is_issued.connect(mock_is_issued)

    # Patch ToastManager
    mock_toast_success = mocker.patch(
        'src.viewmodels.issue_nia_view_model.ToastManager.success',
    )

    # Act
    issue_nia_view_model.on_success(response)

    # Assert
    mock_toast_success.assert_called_once_with(
        description=f'Asset issued with asset id: {response.asset_id}',
    )
    mock_issue_button_clicked.assert_called_once_with(False)
    mock_is_issued.assert_called_once_with('name')


def test_on_close_click(mocker, issue_nia_view_model):
    """Test that on_close_click triggers navigation to fungibles_asset_page."""
    mock_nav = mocker.patch.object(
        issue_nia_view_model._page_navigation, 'fungibles_asset_page',
    )

    issue_nia_view_model.on_close_click()

    mock_nav.assert_called_once()


@patch('src.views.components.toast.ToastManager.error')
def test_on_error_no_available_utxos_triggers_utxo_creation_started(mock_toast_error, issue_nia_view_model):
    """on_error should emit utxo_creation_started(True) and return without toast for NoAvailableUtxos."""
    # Connect signals
    utxo_slot = Mock()
    issue_nia_view_model.utxo_creation_started.connect(utxo_slot)
    btn_slot = Mock()
    issue_nia_view_model.issue_button_clicked.connect(btn_slot)

    err = CommonException('NoAvailableUtxos')
    err.message = 'NoAvailableUtxos'

    issue_nia_view_model.on_error(err)

    btn_slot.assert_called_once_with(False)
    utxo_slot.assert_called_once_with(True)
    mock_toast_error.assert_not_called()


@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_type')
def test_on_issue_click_multisig_on_device_requires_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, issue_nia_view_model,
):
    """Test that multisig on-device wallet requires native auth."""
    mock_get_signature.return_value = WalletSignatureType.MULTI_SIG_WALLET
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(issue_nia_view_model, 'run_in_thread') as mock_run:
        issue_nia_view_model.on_issue_click('TEST', 'Test Asset', '100')

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_type')
def test_on_issue_click_standard_wallet_no_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, issue_nia_view_model,
):
    """Test that standard online on-device wallet DOES require native auth."""
    mock_get_signature.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_key_storage.return_value = KeyStorageType.ON_DEVICE
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(issue_nia_view_model, 'run_in_thread') as mock_run:
        issue_nia_view_model.on_issue_click('TEST', 'Test Asset', '100')

        # Verify native auth was passed to run_in_thread (standard online on-device DOES require auth)
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_signature_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_key_storage_type')
@patch('src.viewmodels.issue_nia_view_model.SettingRepository.get_wallet_type')
def test_on_issue_click_hardware_wallet_no_native_auth(
    mock_get_wallet_type, mock_get_key_storage, mock_get_signature, issue_nia_view_model,
):
    """Test that hardware wallet does not require native auth."""
    mock_get_signature.return_value = WalletSignatureType.STANDARD_TYPE_WALLET
    mock_get_key_storage.return_value = KeyStorageType.HARDWARE_WALLET
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET

    with patch.object(issue_nia_view_model, 'run_in_thread') as mock_run:
        issue_nia_view_model.on_issue_click('TEST', 'Test Asset', '100')

        # Verify issue_asset_nia was passed to run_in_thread (no native auth for hardware wallet)
        call_args = mock_run.call_args[0]
        expected_method = RgbRepository.issue_asset_nia
        assert call_args[0] is expected_method
