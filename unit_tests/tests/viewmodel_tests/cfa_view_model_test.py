"""Unit test for CFA view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument,too-many-statements,protected-access,too-few-public-methods
from __future__ import annotations

from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from rgb_lib import AssetSchema
from rgb_lib import Assignment
from rgb_lib import TransferStatus

from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import Balance
from src.model.rgb_model import FailTransferResponseModel
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.rgb_model import SendAssetResponseModel
from src.model.rgb_model import TransferAsset
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_FAIL_TRANSFER
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_ASSET_SENT
from src.utils.info_message import INFO_FAIL_TRANSFER_SUCCESSFULLY
from src.utils.info_message import INFO_REFRESH_SUCCESSFULLY
from src.utils.page_navigation import PageNavigation
from src.viewmodels.cfa_view_model import CFAViewModel


@pytest.fixture
def setup_navigation():
    """Fixture to set up and tear down PAGE_NAVIGATION."""
    mock_page_navigation = MagicMock(spec=PageNavigation)
    yield mock_page_navigation
    # Clean up after tests


@pytest.fixture
def cfa_view_model(setup_navigation):
    """Fixture to create an instance of the CFAViewModel class."""
    return CFAViewModel(setup_navigation)


@pytest.fixture
def mock_asset_details_response():
    """Fixture to mock asset details response."""
    return ListTransferAssetWithBalanceResponseModel(
        transfers=[
            TransferAsset(
                idx=11,
                created_at=1718280342,
                updated_at=1718280342,
                created_at_date='2024-06-13',
                created_at_time='17:35:42',
                update_at_date='2024-06-13',
                updated_at_time='17:35:42',
                status=TransferStatus.SETTLED,
                assignments=[
                    Assignment.FUNGIBLE(
                        amount=69,
                    ),
                ],
                amount_status='+69',
                kind='Issuance',
                transfer_Status=TransferStatusEnumModel.INTERNAL,
                receive_utxo=None,
                txid=None,
                expiration=None,
                recipient_id=None,
                change_utxo=None,
                transport_endpoints=[],
            ),
        ],
        asset_balance=Balance(
            settled=69,
            future=69,
            spendable=69,
        ),
    )


@patch('src.data.service.asset_detail_page_services.AssetDetailPageService.get_asset_transactions')
def test_get_cfa_asset_detail_success(mock_get_asset_transactions, cfa_view_model, mock_asset_details_response):
    """Test for successfully retrieving CFA asset detail."""
    mock_txn_list_loaded_signal = Mock()
    mock_is_loading_signal = Mock()
    cfa_view_model.txn_list_loaded.connect(mock_txn_list_loaded_signal)
    cfa_view_model.is_loading.connect(mock_is_loading_signal)

    mock_get_asset_transactions.return_value = mock_asset_details_response

    asset_id = 'test_asset_id'
    asset_name = 'test_asset_name'
    image_path = 'test_image_path'
    asset_type = 'test_asset_type'

    cfa_view_model.get_cfa_asset_detail(
        asset_id, asset_name, image_path, asset_type,
    )
    cfa_view_model.worker.result.emit(mock_asset_details_response)

    mock_txn_list_loaded_signal.assert_called_once_with(
        asset_id, asset_name, image_path, asset_type,
    )
    mock_is_loading_signal.assert_called_with(False)
    assert cfa_view_model.asset_id == asset_id
    assert cfa_view_model.asset_name == asset_name
    assert cfa_view_model.image_path == image_path
    assert cfa_view_model.asset_type == asset_type


@patch('src.utils.worker.ThreadManager.run_in_thread', autospec=True)
def test_on_send_click(mock_run_in_thread, cfa_view_model):
    """Test the on_send_click method of CFAViewModel without executing the actual method."""
    # Setup test parameters
    assignment = Assignment.FUNGIBLE(amount=100)
    blinded_utxo = 'test_blinded_utxo'
    transport_endpoints = ['test_endpoint']
    fee_rate = 1.0
    min_confirmation = 1

    # Ensure asset_id is set before calling the method
    cfa_view_model.asset_id = 'test_asset_id'

    # Mock the worker object
    mock_worker = MagicMock()
    cfa_view_model.worker = mock_worker

    # Call the method
    # Method signature: (blinded_utxo, transport_endpoints, fee_rate, min_confirmation, assignment)
    cfa_view_model.on_send_click(
        blinded_utxo, transport_endpoints, fee_rate, min_confirmation, assignment,
    )

    # Verify the state changes
    assert cfa_view_model.assignment.amount == assignment.amount
    assert cfa_view_model.blinded_utxo == blinded_utxo
    assert cfa_view_model.transport_endpoints == transport_endpoints
    assert cfa_view_model.fee_rate == fee_rate
    assert cfa_view_model.min_confirmation == min_confirmation


@patch('src.viewmodels.cfa_view_model.requires_native_authentication', return_value=True)
def test_on_send_click_multisig_on_device_requires_native_auth(
    mock_requires_auth, cfa_view_model,
):
    """Test that multisig on-device wallet requires native auth for send asset."""
    assignment = Assignment.FUNGIBLE(amount=100)
    cfa_view_model.asset_id = 'test_asset_id'

    with patch.object(cfa_view_model, 'run_in_thread') as mock_run:
        cfa_view_model.on_send_click('blind', ['te'], 2, 3, assignment)

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.cfa_view_model.requires_native_authentication', return_value=True)
def test_on_send_click_standard_wallet_no_native_auth(
    mock_requires_auth, cfa_view_model,
):
    """Test that standard online on-device wallet DOES require native auth."""
    assignment = Assignment.FUNGIBLE(amount=100)
    cfa_view_model.asset_id = 'test_asset_id'

    with patch.object(cfa_view_model, 'run_in_thread') as mock_run:
        cfa_view_model.on_send_click('blind', ['te'], 2, 3, assignment)

        # Verify native auth was passed to run_in_thread (standard online on-device DOES require auth)
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.cfa_view_model.requires_native_authentication', return_value=False)
def test_on_send_click_hardware_wallet_no_native_auth(
    mock_requires_auth, cfa_view_model,
):
    """Test that hardware wallet does not require native auth for send asset."""
    assignment = Assignment.FUNGIBLE(amount=100)
    cfa_view_model.asset_id = 'test_asset_id'

    with patch.object(cfa_view_model, 'run_in_thread') as mock_run:
        cfa_view_model.on_send_click('blind', ['te'], 2, 3, assignment)

        # Verify send_asset was passed to run_in_thread (no native auth for hardware wallet)
        call_args = mock_run.call_args[0]
        expected_method = RgbRepository.send_asset
        assert call_args[0] is expected_method


@patch('src.data.repository.rgb_repository.RgbRepository.fail_transfer')
@patch('src.views.components.toast.ToastManager.success')
@patch('src.views.components.toast.ToastManager.error')
def test_on_fail_transfer(mock_toast_error, mock_toast_success, mock_fail_transfer, cfa_view_model):
    """Test for handling fail transfer operation."""
    # Mock necessary attributes and methods
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.get_cfa_asset_detail = MagicMock()

    # Mock the repository method return value
    mock_fail_transfer.return_value = FailTransferResponseModel(
        transfers_changed=True,
    )

    # Mock run_in_thread to directly invoke the success callback
    def mock_run_in_thread(func, args):
        # Simulate the success callback being called
        args['callback'](mock_fail_transfer.return_value)

    cfa_view_model.run_in_thread = MagicMock(side_effect=mock_run_in_thread)

    # Set up the asset ID
    cfa_view_model.asset_id = 'test_asset_id'

    # Call the method
    batch_transfer_idx = 1
    cfa_view_model.on_fail_transfer(batch_transfer_idx)

    # Verify the behavior
    cfa_view_model.is_loading.emit.assert_called_with(
        True,
    )  # Loading state is set
    mock_toast_success.assert_called_once_with(
        description=INFO_FAIL_TRANSFER_SUCCESSFULLY,
    )  # Success toast is shown
    cfa_view_model.get_cfa_asset_detail.assert_called_once_with(
        cfa_view_model.asset_id, cfa_view_model.asset_name, None, cfa_view_model.asset_type,
    )

    # Test when transfers_changed=False
    mock_fail_transfer.return_value.transfers_changed = False

    def mock_run_in_thread_fail(func, args):
        # Simulate the error callback being called
        args['callback'](mock_fail_transfer.return_value)

    cfa_view_model.run_in_thread = MagicMock(
        side_effect=mock_run_in_thread_fail,
    )

    cfa_view_model.on_fail_transfer(batch_transfer_idx)

    cfa_view_model.is_loading.emit.assert_called_with(
        False,
    )  # Loading state is unset
    mock_toast_error.assert_called_once_with(
        description=ERROR_FAIL_TRANSFER,
    )  # Error toast is shown

    # Test for handling error while failing a transfer
    mock_exception = CommonException('Error sending asset')
    mock_fail_transfer.side_effect = mock_exception
    cfa_view_model.run_in_thread = MagicMock(
        side_effect=lambda func, args: args['error_callback'](mock_exception),
    )

    cfa_view_model.on_fail_transfer(batch_transfer_idx)

    cfa_view_model.is_loading.emit.assert_called_with(
        False,
    )  # Loading state is unset
    mock_toast_error.assert_called_with(
        description='Something went wrong: Error sending asset',
    )

    # Test for handling generic exception while failing a transfer
    mock_fail_transfer.side_effect = Exception('Generic error')
    cfa_view_model.run_in_thread = MagicMock(
        side_effect=lambda func, args: func(),
    )

    cfa_view_model.on_fail_transfer(batch_transfer_idx)

    cfa_view_model.is_loading.emit.assert_called_with(
        False,
    )  # Loading state is unset
    mock_toast_error.assert_called_with(
        description='Something went wrong: Generic error',
    )

# Test on_refresh_click functionality


@patch('src.viewmodels.cfa_view_model.Cache')
@patch('src.viewmodels.cfa_view_model.ToastManager')
@patch('src.viewmodels.cfa_view_model.RgbRepository')
def test_on_refresh_click(mock_rgb_repository, mock_toast_manager, mock_cache, cfa_view_model):
    """Test the on_refresh_click method behavior."""
    # Set up mocks
    mock_cache_session = MagicMock()
    mock_cache.get_cache_session.return_value = mock_cache_session
    mock_toast_success = mock_toast_manager.success
    mock_toast_error = mock_toast_manager.error

    # Set up the view model
    cfa_view_model.refresh = MagicMock()
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    cfa_view_model.get_cfa_asset_detail = MagicMock()
    cfa_view_model.asset_id = 'test_asset_id'
    cfa_view_model.asset_name = 'test_asset'
    cfa_view_model.asset_type = 'CFA'

    # Test successful refresh: pass empty dict to mimic no failures
    def mock_run_in_thread(func, args):
        args['callback']({})

    cfa_view_model.run_in_thread = MagicMock(side_effect=mock_run_in_thread)

    # Call the method
    cfa_view_model.on_refresh_click()

    # Verify behavior for successful case
    mock_cache_session.invalidate_cache.assert_called_once()
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(
        True,
    )
    cfa_view_model.is_loading.emit.assert_has_calls(
        [call(True), call(False)],
    )
    calls = cfa_view_model.refresh.emit.call_args_list
    assert len(calls) >= 1 and calls[0] == call(True)
    mock_toast_success.assert_called_once_with(
        description=INFO_REFRESH_SUCCESSFULLY,
    )
    cfa_view_model.get_cfa_asset_detail.assert_called_once_with(
        cfa_view_model.asset_id,
        cfa_view_model.asset_name,
        None,
        cfa_view_model.asset_type,
    )

    # Test refresh with failures (lines 227-235)
    class DummyFailure:
        """Dummy class to simulate failure."""

        def __init__(self):
            self.failure = MagicMock()

    mock_refresh_data = {'transfer_idx_1': DummyFailure()}

    def mock_run_in_thread_with_failures(func, args):
        args['callback'](mock_refresh_data)

    cfa_view_model.run_in_thread = MagicMock(
        side_effect=mock_run_in_thread_with_failures,
    )

    with patch('src.viewmodels.cfa_view_model.PageNavigationEventManager') as mock_page_nav_ev:
        with patch('src.viewmodels.cfa_view_model.RefreshFailureItem'):
            cfa_view_model.on_refresh_click()
            mock_page_nav_ev.get_instance(
            ).refresh_transfer_result_dialog_signal.emit.assert_called_once()

    # Test error case with CommonException
    mock_exception = CommonException('Refresh error')
    cfa_view_model.run_in_thread = MagicMock(
        side_effect=lambda func, args: args['error_callback'](mock_exception),
    )

    # Reset mocks
    cfa_view_model.refresh.reset_mock()
    cfa_view_model.is_loading.reset_mock()
    mock_toast_error.reset_mock()
    mock_cache_session.invalidate_cache.reset_mock()

    # Call the method
    cfa_view_model.on_refresh_click()

    # Verify behavior for error case
    # Ensure the first refresh emit indicates failure
    calls = cfa_view_model.refresh.emit.call_args_list
    assert len(calls) >= 1 and calls[0] == call(False)
    cfa_view_model.is_loading.emit.assert_has_calls(
        [call(True), call(False)],
    )
    mock_toast_error.assert_called_once_with(
        description=f'{ERROR_SOMETHING_WENT_WRONG}: {mock_exception}',
    )

    # Test generic exception case
    generic_exception = Exception('Generic error')
    cfa_view_model.run_in_thread = MagicMock(side_effect=generic_exception)

    # Reset mocks
    cfa_view_model.refresh.reset_mock()
    cfa_view_model.is_loading.reset_mock()
    mock_toast_error.reset_mock()
    mock_cache_session.invalidate_cache.reset_mock()

    # Call the method
    cfa_view_model.on_refresh_click()

    # Verify behavior for generic exception case
    assert cfa_view_model.refresh.emit.call_args_list == [call(False)]
    cfa_view_model.is_loading.emit.assert_has_calls(
        [call(True), call(False)],
    )
    mock_toast_error.assert_called_once_with(
        description=f'{ERROR_SOMETHING_WENT_WRONG}: Generic error',
    )

    # Test when cache is None
    mock_cache.get_cache_session.return_value = None
    cfa_view_model.run_in_thread = MagicMock(side_effect=mock_run_in_thread)

    # Reset mocks
    cfa_view_model.refresh.reset_mock()
    cfa_view_model.is_loading.reset_mock()
    mock_toast_success.reset_mock()
    mock_cache_session.invalidate_cache.reset_mock()

    # Call the method
    cfa_view_model.on_refresh_click()

    # Verify behavior when cache is None
    # Should not be called when cache is None
    mock_cache_session.invalidate_cache.assert_not_called()
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_with(True)
    cfa_view_model.is_loading.emit.assert_has_calls(
        [call(True), call(False)],
    )
    calls = cfa_view_model.refresh.emit.call_args_list
    assert len(calls) >= 1 and calls[0] == call(True)
    mock_toast_success.assert_called_once_with(
        description=INFO_REFRESH_SUCCESSFULLY,
    )


def test_on_success_send_rgb_asset(cfa_view_model, mocker):
    """Test on_success_send_rgb_asset behavior"""
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.on_error = MagicMock()  # Mock on_error as MagicMock
    # Mock toast_error
    mock_toast_error = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.error',
    )

    # Test successful case
    cfa_view_model.asset_id = 'test_asset_id'
    cfa_view_model.assignment = Assignment.FUNGIBLE(amount=100)
    cfa_view_model.blinded_utxo = 'test_blinded_utxo'
    cfa_view_model.transport_endpoints = ['endpoint1', 'endpoint2']
    cfa_view_model.fee_rate = 1.0
    cfa_view_model.min_confirmation = 1
    cfa_view_model.run_in_thread = MagicMock()

    # Call method with success=True
    cfa_view_model.on_success_send_rgb_asset(True)

    # Verify behavior for success case
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(
        True,
    )
    cfa_view_model.is_loading.emit.assert_called_once_with(True)
    cfa_view_model.run_in_thread.assert_called_once()

    # Verify run_in_thread arguments
    call_args = cfa_view_model.run_in_thread.call_args[0][1]
    assert call_args['args'][0].asset_id == cfa_view_model.asset_id
    assert call_args['args'][0].assignment.amount == cfa_view_model.assignment.amount
    assert call_args['args'][0].recipient_id == cfa_view_model.blinded_utxo
    assert call_args['args'][0].transport_endpoints == cfa_view_model.transport_endpoints
    assert call_args['args'][0].fee_rate == cfa_view_model.fee_rate
    assert call_args['args'][0].min_confirmations == cfa_view_model.min_confirmation
    assert call_args['callback'] == cfa_view_model.on_success_cfa
    assert call_args['error_callback'] == cfa_view_model.on_error

    # Test exception case
    mock_exception = Exception('Test error')
    cfa_view_model.run_in_thread = MagicMock(side_effect=mock_exception)

    # Reset mocks
    cfa_view_model.send_cfa_button_clicked.reset_mock()
    cfa_view_model.is_loading.reset_mock()
    cfa_view_model.on_error.reset_mock()
    mock_toast_error.reset_mock()

    # Call method with success=True (will raise exception)
    cfa_view_model.on_success_send_rgb_asset(True)

    # Verify behavior for exception case
    cfa_view_model.send_cfa_button_clicked.emit.assert_has_calls([
        call(True),
    ])
    cfa_view_model.is_loading.emit.assert_has_calls([call(True)])
    cfa_view_model.on_error.assert_called_once()
    assert isinstance(
        cfa_view_model.on_error.call_args[0][0], CommonException,
    )
    assert str(mock_exception) in str(
        cfa_view_model.on_error.call_args[0][0],
    )

    # Test authentication cancelled case
    # Reset mocks
    cfa_view_model.send_cfa_button_clicked.reset_mock()
    cfa_view_model.is_loading.reset_mock()
    mock_toast_error.reset_mock()

    # Call method with success=False
    cfa_view_model.on_success_send_rgb_asset(False)

    # Verify behavior for cancelled case - signals emit False
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(False)
    cfa_view_model.is_loading.emit.assert_called_once_with(False)
    mock_toast_error.assert_called_once_with(
        description=ERROR_AUTHENTICATION_CANCELLED,
    )


def test_on_error(cfa_view_model, mocker):
    """Test the on_error method of CFAViewModel."""
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    # Create test error
    mock_error = CommonException('Test error message')

    # Mock to ensure non-HW, non-multisig path (which calls ToastManager.error)
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.ON_DEVICE,
    )
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    mock_toast_error = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.error',
    )

    # Reset mocks
    cfa_view_model.is_loading.reset_mock()
    cfa_view_model.send_cfa_button_clicked.reset_mock()
    mock_toast_error.reset_mock()

    # Call on_error method
    cfa_view_model.on_error(mock_error)

    # Verify behavior
    cfa_view_model.is_loading.emit.assert_called_once_with(False)
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(
        False,
    )
    mock_toast_error.assert_called_once_with(description=mock_error.message)


def test_on_success_cfa(cfa_view_model, mocker):
    """Test the on_success_cfa method of CFAViewModel."""
    # Setup mocks
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    cfa_view_model._page_navigation = MagicMock()

    # Mock for non-multisig path
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    mock_toast_success = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.success',
    )

    # Create test tx_id
    mock_tx_id = SendAssetResponseModel(txid='test_txid_123')

    # Test CFA asset type
    cfa_view_model.asset_type = AssetSchema.CFA
    cfa_view_model.on_success_cfa(mock_tx_id)

    # Verify behavior for CFA
    cfa_view_model.is_loading.emit.assert_called_once_with(False)
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(
        False,
    )
    mock_toast_success.assert_called_once_with(
        description=INFO_ASSET_SENT.format(mock_tx_id.txid),
    )
    cfa_view_model._page_navigation.collectibles_asset_page.assert_called_once()

    # Reset mocks
    cfa_view_model.is_loading.reset_mock()
    cfa_view_model.send_cfa_button_clicked.reset_mock()
    cfa_view_model._page_navigation.reset_mock()
    mock_toast_success.reset_mock()

    # Test NIA asset type
    cfa_view_model.asset_type = AssetSchema.NIA
    cfa_view_model.on_success_cfa(mock_tx_id)

    cfa_view_model.is_loading.emit.assert_called_once_with(False)
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(
        False,
    )
    mock_toast_success.assert_called_once_with(
        description=INFO_ASSET_SENT.format(mock_tx_id.txid),
    )
    cfa_view_model._page_navigation.fungibles_asset_page.assert_called_once()

    # Test IFA asset type (lines 140-141)
    cfa_view_model.is_loading.reset_mock()
    cfa_view_model.send_cfa_button_clicked.reset_mock()
    cfa_view_model._page_navigation.reset_mock()
    cfa_view_model.asset_type = AssetSchema.IFA
    cfa_view_model.on_success_cfa(mock_tx_id)
    cfa_view_model._page_navigation.inflatable_asset_page.assert_called_once()


def test_on_success_cfa_hw_multisig(cfa_view_model, mocker):
    """Test HW and Multisig specific branches (lines 123, 130)."""
    cfa_view_model.is_loading = MagicMock()
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    cfa_view_model._page_navigation = MagicMock()
    mock_toast_success = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.success',
    )
    mock_tx_id = SendAssetResponseModel(txid='test_txid_123')

    emitted = []
    cfa_view_model.hw_dialog_update.connect(
        lambda msg, st: emitted.append((msg, st)),
    )

    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )

    cfa_view_model.on_success_cfa(mock_tx_id)

    assert (None, PsbtStatus.SUCCESS) in emitted
    mock_toast_success.assert_called_once_with(
        description='Operation posted to multisig bridge.',
    )


@patch('src.viewmodels.cfa_view_model.ToastManager.error')
@patch('src.viewmodels.cfa_view_model.AssetDetailPageService.get_asset_transactions')
def test_get_cfa_asset_detail_error_and_exception(mock_get_tx, mock_toast_error, cfa_view_model):
    """Cover error and exception paths in get_cfa_asset_detail."""
    # Patch run_in_thread to call error_callback directly
    def run_calls_error(func, kwargs):
        kwargs['error_callback'](CommonException('boom'))

    cfa_view_model.run_in_thread = MagicMock(side_effect=run_calls_error)
    txn_loaded = Mock()
    is_loading = Mock()
    cfa_view_model.txn_list_loaded.connect(txn_loaded)
    cfa_view_model.is_loading.connect(is_loading)

    cfa_view_model.get_cfa_asset_detail('aid', 'aname', 'img', AssetSchema.CFA)
    txn_loaded.assert_called_once_with('aid', 'aname', 'img', AssetSchema.CFA)
    is_loading.assert_called_with(False)
    mock_toast_error.assert_called()

    # Now make run_in_thread raise to exercise except branch
    cfa_view_model.run_in_thread = MagicMock(side_effect=Exception('crash'))
    mock_toast_error.reset_mock()
    txn_loaded = Mock()
    cfa_view_model.txn_list_loaded.connect(txn_loaded)
    cfa_view_model.get_cfa_asset_detail(
        'aid2', 'aname2', 'img2', AssetSchema.NIA,
    )
    mock_toast_error.assert_called()


def test_on_error_native_auth(cfa_view_model, mocker):
    """Cover on_error_native_auth for CommonException and generic Exception."""
    toast_err = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.error',
    )
    # CommonException -> use error.message
    cfa_view_model.on_error_native_auth(CommonException('nope'))
    toast_err.assert_called_with(description='nope')
    # Generic -> SOMETHING_WENT_WRONG
    toast_err.reset_mock()
    cfa_view_model.on_error_native_auth(Exception('x'))
    toast_err.assert_called_with(description=ERROR_SOMETHING_WENT_WRONG)


@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
@patch('src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
def test_on_psbt_created_hardware_wallet(mock_get_sig, mock_get_kst, mock_get_wt, cfa_view_model):
    """When HW + online wallet, emit signing status and run sign_and_finalize."""
    emitted = []
    cfa_view_model.hw_dialog_update.connect(
        lambda msg, st: emitted.append((msg, st)),
    )
    cfa_view_model.send_cfa_button_clicked = MagicMock()
    cfa_view_model.run_in_thread = MagicMock()
    # Create mock result object with psbt attribute
    mock_result = MagicMock()
    mock_result.psbt = 'psbt'
    cfa_view_model.on_psbt_created(mock_result)
    # hw dialog shows signing
    assert any(msg for (msg, st) in emitted if st == PsbtStatus.SIGNING)
    # run_in_thread called targeting CommonOperationRepository.sign_and_finalize_psbt
    args = cfa_view_model.run_in_thread.call_args[0][1]
    assert args['args'] == ['psbt']
    assert args['callback'] == cfa_view_model.on_psbt_signed_and_finalized_success
    assert args['error_callback'] == cfa_view_model.on_error


@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY)
@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
def test_on_psbt_created_watch_only(mock_get_sig, mock_get_acc, cfa_view_model):
    """WATCH_ONLY should emit unsigned_psbt signal."""
    got = []
    cfa_view_model.unsigned_psbt.connect(got.append)
    # Create mock result object with psbt attribute
    mock_result = MagicMock()
    mock_result.psbt = 'raw_psbt'
    cfa_view_model.on_psbt_created(mock_result)
    assert got == ['raw_psbt']


@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
@patch('src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
@patch('src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
def test_on_psbt_created_sets_rgb_mode(mock_get_sig, mock_get_kst, mock_get_wt, cfa_view_model, mocker):
    """Ensure RGB mode is enabled before invoking sign_and_finalize_psbt in HW flow."""
    set_rgb = mocker.patch(
        'src.viewmodels.cfa_view_model.hardware_client_store.set_rgb_mode',
    )
    cfa_view_model.run_in_thread = MagicMock()
    # Create mock result object with psbt attribute
    mock_result = MagicMock()
    mock_result.psbt = 'psbtX'
    cfa_view_model.on_psbt_created(mock_result)
    set_rgb.assert_called_once_with(True)


def test_on_psbt_signed_and_finalized_calls_send_end_and_broadcasts(cfa_view_model):
    """Ensure broadcasting status and send_end call."""
    emitted = []
    cfa_view_model.hw_dialog_update.connect(lambda msg, st: emitted.append(st))
    cfa_view_model.send_end = MagicMock()
    cfa_view_model.on_psbt_signed_and_finalized_success('final_psbt')
    assert PsbtStatus.BROADCASTING in emitted
    cfa_view_model.send_end.assert_called_once_with('final_psbt')


def test_send_begin_sets_request_and_runs(cfa_view_model):
    """send_begin calls RgbRepository.send_begin with correct request and callbacks."""
    cfa_view_model.asset_id = 'aid'
    cfa_view_model.run_in_thread = MagicMock()
    cfa_view_model.send_cfa_button_clicked = Mock()
    cfa_view_model.send_begin(
        'blind', ['te'], 2, 3, Assignment.FUNGIBLE(amount=1),
    )
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(True)
    params = cfa_view_model.run_in_thread.call_args[0][1]
    req = params['args'][0]
    assert req.asset_id == 'aid'
    assert req.assignment.amount == 1
    assert req.recipient_id == 'blind'
    assert req.transport_endpoints == ['te']
    assert req.fee_rate == 2
    assert req.min_confirmations == 3
    assert params['callback'] == cfa_view_model.on_psbt_created
    assert params['error_callback'] == cfa_view_model.on_error


def test_send_end_runs_with_request(cfa_view_model):
    """send_end calls RgbRepository.send_end with broadcast request and callbacks."""
    cfa_view_model.run_in_thread = MagicMock()
    cfa_view_model.send_cfa_button_clicked = Mock()
    cfa_view_model.send_end('signed', skip_sync=True)
    cfa_view_model.send_cfa_button_clicked.emit.assert_called_once_with(True)
    params = cfa_view_model.run_in_thread.call_args[0][1]
    req = params['args'][0]
    assert req.skip_sync is True
    assert params['callback'] == cfa_view_model.on_success_cfa
    assert params['error_callback'] == cfa_view_model.on_error


def test_send_begin_multisig(cfa_view_model, mocker):
    """Cover multisig branch in send_begin (line 316)."""
    cfa_view_model.asset_id = 'test_asset'
    cfa_view_model.run_in_thread = MagicMock()
    cfa_view_model.send_cfa_button_clicked = Mock()
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )

    cfa_view_model.send_begin(
        'blind', ['te'], 2, 3, Assignment.FUNGIBLE(amount=1),
    )

    params = cfa_view_model.run_in_thread.call_args[0][1]
    assert params['args'][0].recipient_id == 'blind'
    assert 'send_init' in str(
        cfa_view_model.run_in_thread.call_args[0][0],
    ) or cfa_view_model.run_in_thread.call_args[0][0].__name__ == 'send_init'


def test_on_psbt_created_multisig(cfa_view_model, mocker):
    """Cover HW+Multisig branch in on_psbt_created and common sign branch (lines 340, 360-365, 368)."""
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.cfa_view_model.SettingRepository.get_wallet_type',
        return_value=WalletType.ONLINE_TYPE_WALLET,
    )

    hw_emit = mocker.Mock()
    cfa_view_model.hw_dialog_update.connect(hw_emit)
    cfa_view_model.run_in_thread = MagicMock()

    mock_res = mocker.Mock(psbt='psbt1', operation_idx=2)
    with patch('src.viewmodels.cfa_view_model.hardware_client_store.set_rgb_mode') as mock_hw_rgb:
        cfa_view_model.on_psbt_created(mock_res)

        mock_hw_rgb.assert_called_once_with(True)
        assert cfa_view_model.operation_idx == 2
        hw_emit.assert_called_once()
        cfa_view_model.run_in_thread.assert_called_once()
        assert 'sign_psbt' in str(
            cfa_view_model.run_in_thread.call_args[0][0],
        ) or cfa_view_model.run_in_thread.call_args[0][0].__name__ == 'sign_psbt'


def test_on_multisig_psbt_signed(cfa_view_model, mocker):
    """Cover on_multisig_psbt_signed logic (lines 388-391)."""
    cfa_view_model.operation_idx = 1
    # Mock post_signed_psbt_to_bridge where it's imported in cfa_view_model
    mock_post = mocker.patch(
        'src.viewmodels.cfa_view_model.post_signed_psbt_to_bridge',
    )

    cfa_view_model.on_multisig_psbt_signed('signed_psbt')

    # Verify post_signed_psbt_to_bridge was called
    mock_post.assert_called_once_with(cfa_view_model, 'signed_psbt', 1)


def test_on_multisig_post_success(cfa_view_model, mocker):
    """Cover on_success_multisig_post logic (line 403)."""
    mock_success = mocker.patch.object(cfa_view_model, 'on_success_cfa')
    cfa_view_model.on_success_multisig_post(None)
    mock_success.assert_called_once()
    # on_success_cfa is called without arguments from on_success_multisig_post


@patch('src.viewmodels.cfa_view_model.hardware_client_store.stop_client')
def test_cancel_operation_emits_and_stops(mock_stop, cfa_view_model):
    """Cancel should close dialog and stop HW client."""
    clicked = Mock()
    cfa_view_model.send_cfa_button_clicked.connect(clicked)
    cfa_view_model.cancel_operation()
    clicked.assert_called_once_with(False)
    mock_stop.assert_called_once()


@patch('src.viewmodels.cfa_view_model.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
def test_on_error_hardware_branch(mock_kst, cfa_view_model, mocker):
    """Cover hardware branch of on_error emitting hw error status."""
    emitted = []
    cfa_view_model.hw_dialog_update.connect(lambda msg, st: emitted.append(st))
    mock_toast_error = mocker.patch(
        'src.viewmodels.cfa_view_model.ToastManager.error',
    )
    cfa_view_model.on_error(CommonException('e'))
    assert PsbtStatus.ERROR in emitted
    mock_toast_error.assert_not_called()
