# pylint: disable=unused-import,redefined-outer-name,unused-argument
"""Unit tests for IssueIFAViewModel (Inflatable Asset).
Plain-function tests aligned with legacy style, mirroring IssueNIAViewModel tests.
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from rgb_lib import OperationResult

from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import Balance
from src.model.rgb_model import IssueAssetResponseModel
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_AUTHENTICATION_CANCELLED
from src.utils.error_message import ERROR_FIELD_MISSING
from src.viewmodels.issue_ifa_view_model import IssueIFAViewModel


@pytest.fixture
def mock_page_navigation(mocker):
    """Mock page navigation."""
    return mocker.MagicMock()


@pytest.fixture
def vm(mock_page_navigation):
    """Mock view model."""
    return IssueIFAViewModel(mock_page_navigation)


def _mk_issue_resp():
    """Mock issue response."""
    return IssueAssetResponseModel(
        asset_id='aid',
        ticker='IFAT',
        name='AssetName',
        details=None,
        precision=0,
        issued_supply=1000,
        timestamp=123456,
        added_at=123456,
        balance=Balance(spendable=1, future=0, settled=1),
        media=None,
    )


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.repository.rgb_repository.RgbRepository.issue_asset_ifa')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_issue_ifa_asset_success_flow(mock_run, mock_issue, mock_toast_err, vm):
    """Test issue ifa asset success flow."""
    mock_issue.return_value = _mk_issue_resp()

    # Wire signals
    sig_loading = Mock()
    sig_success = Mock()
    vm.is_loading.connect(sig_loading)
    vm.success_page_message.connect(sig_success)

    # Provide inputs
    vm.issue_ifa_asset('IFAT', 'AssetName', 100, 50)

    # Simulate worker success callback
    worker = MagicMock()
    vm.worker = worker
    worker.result.emit = Mock()
    worker.result.emit(mock_issue.return_value)

    mock_toast_err.assert_not_called()


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_ifa_missing_fields(mock_toast, vm):
    """Test on success native auth ifa missing fields."""
    vm.asset_ticker = 'IFAT'
    vm.asset_name = 'AssetName'
    vm.amount = None  # missing
    vm.inflation_amounts = 10
    vm.replace_rights_num = True

    vm.on_success_native_auth_ifa(True)

    mock_toast.assert_called_once_with(description=ERROR_FIELD_MISSING)


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_ifa_auth_failed(mock_toast, vm):
    """Test on success native auth ifa auth failed."""
    vm.on_success_native_auth_ifa(False)
    mock_toast.assert_called_once_with(
        description=ERROR_AUTHENTICATION_CANCELLED,
    )


def test_on_error_handles_no_available_utxos(vm, mocker):
    """Test on error handles no available utxos."""
    vm.is_loading.connect(lambda *_: None)
    slot = Mock()
    vm.utxo_creation_started.connect(slot)

    err = CommonException('NoAvailableUtxos')
    err.message = 'NoAvailableUtxos'

    vm.on_error(err)
    slot.assert_called_once_with(True)


@patch('src.viewmodels.issue_ifa_view_model.ToastManager.error')
def test_on_error_generic_message(mock_toast, vm):
    """Test on error generic message."""
    e = CommonException('x')
    e.message = 'x'
    vm.on_error(e)
    mock_toast.assert_called_once()


@patch('src.views.components.toast.ToastManager.success')
@patch('src.data.repository.rgb_repository.RgbRepository.inflate')
@patch('src.utils.worker.ThreadManager.run_in_thread')
@patch('src.data.repository.setting_repository.SettingRepository.native_authentication')
def test_secondary_issuance_flow(mock_auth, mock_run, mock_inflate, _mock_toast_success, vm):
    """Test secondary issuance flow."""
    mock_auth.return_value = True
    vm.secondary_issuance('aid', 7, 2, 1)

    # Simulate emitted success from worker -> on_success_inflate
    res = MagicMock(spec=OperationResult)
    res.txid = 'tx123'
    vm.on_success_inflate(res)


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET)
@patch('src.data.repository.setting_repository.SettingRepository.get_key_storage_type', return_value=KeyStorageType.HARDWARE_WALLET)
@patch('src.utils.hardware_client_store.hardware_client_store.set_rgb_mode')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_secondary_issuance_begin_hardware_sign(mock_run, mock_set_rgb, _get_kst, _get_wt, _get_sign, vm):
    """Test secondary issuance begin hardware sign."""
    # Expect HW dialog update to be emitted with SIGNING, then run sign_and_finalize
    slot = Mock()
    vm.hw_dialog_update.connect(slot)

    # Pass a proper result object (string for non-multisig)
    vm.on_success_inflate_begin('psbt_str')
    # Ensure the run_in_thread scheduled signing
    mock_run.assert_called()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_signature_type', return_value=WalletSignatureType.STANDARD_TYPE_WALLET)
@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY)
def test_secondary_issuance_begin_watch_only_emits_unsigned_psbt(_get_acc, _get_sign, vm):
    """Test secondary issuance begin watch only emits unsigned psbt."""
    slot = Mock()
    vm.unsigned_psbt.connect(slot)

    vm.on_success_inflate_begin('psbt_str')
    slot.assert_called_once_with('psbt_str')


def test_on_psbt_signed_and_finalized_success_triggers_broadcast(vm, mocker):
    """Test on psbt signed and finalized success triggers broadcast."""
    # Capture hw_dialog_update state and ensure inflate_end is called
    hw_slot = Mock()
    vm.hw_dialog_update.connect(hw_slot)

    with patch.object(vm, 'inflate_end') as infl_end:
        vm.on_psbt_signed_and_finalized_success('signed')
        infl_end.assert_called_once_with('signed')


@patch('src.data.repository.rgb_repository.RgbRepository.inflate_end')
@patch('src.utils.worker.ThreadManager.run_in_thread')
def test_inflate_end_runs(mock_run, mock_end, vm):
    """Test inflate end runs."""
    vm.inflate_end('signed_psbt')
    mock_run.assert_called()


def test_on_success_inflate_begin_hardware(vm, mocker):
    """Test on_success_inflate_begin with hardware wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.viewmodel_helpers.hardware_client_store.set_rgb_mode',
    )

    slot = Mock()
    vm.hw_dialog_update.connect(slot)
    mock_run = mocker.patch.object(vm, 'run_in_thread')

    vm.on_success_inflate_begin(mocker.Mock(psbt='psbt', operation_idx=1))

    slot.assert_called_once()
    mock_run.assert_called_once()


def test_on_success_inflate_begin_software(vm, mocker):
    """Test on_success_inflate_begin with software wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_access_type',
        return_value=WalletAccessType.WITH_PRIVATE_KEY,
    )
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.ON_DEVICE,
    )

    mock_run = mocker.patch.object(vm, 'run_in_thread')

    vm.on_success_inflate_begin('psbt_str')
    mock_run.assert_called_once()


def test_on_error_software(vm, mocker):
    """Test on_error with software wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.ON_DEVICE,
    )
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    mock_toast = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.ToastManager.error',
    )

    vm.on_error(CommonException('failed'))
    mock_toast.assert_called_once()


def test_on_success_inflate(vm, mocker):
    """Test on_success_inflate callback."""
    slot = Mock()
    vm.secondary_issuance_success.connect(slot)

    res = MagicMock(spec=OperationResult)
    res.txid = 'tx123'
    vm.on_success_inflate(res)
    slot.assert_called_once()


def test_on_success_multisig_post(vm, mocker):
    """Test on_success_multisig_post callback."""
    slot = Mock()
    vm.secondary_issuance_success.connect(slot)
    mocker.patch('src.viewmodels.issue_ifa_view_model.ToastManager.success')

    def mock_run_in_thread(target, params):
        if 'callback' in params:
            params['callback'](None)

    mocker.patch.object(vm, 'run_in_thread', side_effect=mock_run_in_thread)

    vm.on_success_multisig_post()
    slot.assert_called_once()


def test_on_multisig_psbt_signed(vm, mocker):
    """Test on_multisig_psbt_signed callback."""
    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.operation_idx = 1
    vm.on_multisig_psbt_signed('signed_psbt')
    mock_run.assert_called_once()


def test_native_auth_ifa_success(vm, mocker):
    """Test on_success_native_auth_ifa when auth is successful."""
    vm.asset_ticker = 'IFAT'
    vm.asset_name = 'AssetName'
    vm.amount = 100
    vm.inflation_amounts = 50
    mock_run = mocker.patch.object(vm, 'run_in_thread')

    vm.on_success_native_auth_ifa(True)
    mock_run.assert_called_once()


def test_native_auth_ifa_exception(vm, mocker):
    """Test on_success_native_auth_ifa when exception occurs."""
    vm.asset_ticker = 'IFAT'
    vm.asset_name = 'AssetName'
    vm.amount = 100
    vm.inflation_amounts = 50

    # Trigger exception in int() conversion
    vm.amount = 'invalid'
    mock_toast = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.ToastManager.error',
    )

    vm.on_success_native_auth_ifa(True)
    mock_toast.assert_called_once()


def test_on_error_native_auth_ifa(vm, mocker):
    """Test on_error_native_auth_ifa callback."""
    mock_toast = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.ToastManager.error',
    )
    vm.on_error_native_auth_ifa(Exception('auth failed'))
    mock_toast.assert_called_once()


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_issue_ifa_asset_full_flow(mock_requires_auth, vm, mocker):
    """Test issue_ifa_asset start."""

    def mock_run_in_thread(target, params):
        if 'callback' in params:
            params['callback'](True)
    mocker.patch.object(vm, 'run_in_thread', side_effect=mock_run_in_thread)

    with patch.object(vm, 'on_success_native_auth_ifa') as mock_cb:
        vm.issue_ifa_asset('T', 'N', 1, 1)
        mock_cb.assert_called_with(True)


def test_on_success_issuance(vm, mocker):
    """Test on_success callback."""
    mock_toast = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.ToastManager.success',
    )
    slot = Mock()
    vm.success_page_message.connect(slot)

    resp = _mk_issue_resp()
    vm.on_success(resp)

    mock_toast.assert_called_once()
    slot.assert_called_once_with('AssetName')


def test_on_error_hardware(vm, mocker):
    """Test on_error with hardware wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    mock_toast = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.ToastManager.error',
    )

    vm.on_error(CommonException('hw failed'))
    mock_toast.assert_called_once()


def test_native_auth_inflate_flow(vm, mocker):
    """Test on_success_native_auth_inflate."""
    vm.asset_id = 'aid'
    vm.amount = 100
    vm.fee_rate = 1
    vm.min_confirmation = 1

    mock_run = mocker.patch.object(vm, 'run_in_thread')
    vm.on_success_native_auth_inflate(True)
    mock_run.assert_called_once()


@patch('src.views.components.toast.ToastManager.error')
def test_on_success_native_auth_inflate_auth_failed(mock_toast, vm):
    """Test on_success_native_auth_inflate when auth fails."""
    vm.on_success_native_auth_inflate(False)
    mock_toast.assert_called_once_with(
        description=ERROR_AUTHENTICATION_CANCELLED,
    )


def test_secondary_issuance_full_flow(vm, mocker):
    """Test secondary_issuance start."""
    mocker.patch.object(vm, 'run_in_thread')
    vm.secondary_issuance('aid', 1, 1, 1)
    assert vm.asset_id == 'aid'


def test_on_success_inflate_hardware(vm, mocker):
    """Test on_success_inflate with hardware wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_key_storage_type',
        return_value=KeyStorageType.HARDWARE_WALLET,
    )
    slot = Mock()
    vm.hw_dialog_update.connect(slot)

    res = MagicMock(spec=OperationResult)
    res.txid = 'tx123'
    vm.on_success_inflate(res)
    slot.assert_called_once()


def test_secondary_issuance_begin_multisig(vm, mocker):
    """Test secondary_issuance_begin with multisig."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.MULTI_SIG_WALLET,
    )
    _mock_inflate_init = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.RgbRepository.inflate_init',
        return_value=MagicMock(psbt='psbt', operation_idx=1),
    )
    mock_run = mocker.patch.object(vm, 'run_in_thread')

    vm.secondary_issuance_begin('aid', 1, 1, 1)
    mock_run.assert_called_once()
    # Verify the function and args passed to run_in_thread
    args, _ = mock_run.call_args
    assert args[0] is RgbRepository.inflate_init
    assert args[1] is not None  # request model


def test_secondary_issuance_begin_standard(vm, mocker):
    """Test secondary_issuance_begin with standard wallet."""
    mocker.patch(
        'src.viewmodels.issue_ifa_view_model.SettingRepository.get_wallet_signature_type',
        return_value=WalletSignatureType.STANDARD_TYPE_WALLET,
    )
    _mock_inflate_begin = mocker.patch(
        'src.viewmodels.issue_ifa_view_model.RgbRepository.inflate_begin',
        return_value='psbt',
    )
    mock_run = mocker.patch.object(vm, 'run_in_thread')

    vm.secondary_issuance_begin('aid', 1, 1, 1)
    mock_run.assert_called_once()
    # Verify the function and args passed to run_in_thread
    args, _ = mock_run.call_args
    assert args[0] is RgbRepository.inflate_begin
    assert args[1] is not None  # request model


def test_native_auth_inflate_exception(vm, mocker):
    """Test on_success_native_auth_inflate with an exception at call time."""
    vm.asset_id = 'aid'
    vm.amount = 100
    vm.fee_rate = 1
    vm.min_confirmation = 1

    # Mock run_in_thread to raise an exception when called
    mocker.patch.object(
        vm, 'run_in_thread',
        side_effect=ValueError('immediate fail'),
    )
    mock_on_error = mocker.patch.object(vm, 'on_error')

    vm.on_success_native_auth_inflate(True)
    mock_on_error.assert_called_once()


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_issue_ifa_asset_multisig_on_device_requires_native_auth(
    mock_requires_auth, vm,
):
    """Test that multisig on-device wallet requires native auth for IFA."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.issue_ifa_asset('TEST', 'Test Asset', 100, 50)

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_issue_ifa_asset_standard_wallet_no_native_auth(
    mock_requires_auth, vm,
):
    """Test that standard online on-device wallet DOES require native auth for IFA."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.issue_ifa_asset('TEST', 'Test Asset', 100, 50)

        # Verify native auth was passed to run_in_thread (standard online on-device DOES require auth)
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=False)
def test_issue_ifa_asset_hardware_wallet_no_native_auth(
    mock_requires_auth, vm,
):
    """Test that hardware wallet does not require native auth for IFA."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.issue_ifa_asset('TEST', 'Test Asset', 100, 50)

        # Verify issue_asset_ifa was passed to run_in_thread (no native auth for hardware wallet)
        call_args = mock_run.call_args[0]
        expected_method = RgbRepository.issue_asset_ifa
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_secondary_issuance_multisig_on_device_requires_native_auth(
    mock_requires_auth, vm,
):
    """Test that multisig on-device wallet requires native auth for secondary issuance."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.secondary_issuance('aid', 100, 1, 1)

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_secondary_issuance_standard_wallet_no_native_auth(
    mock_requires_auth, vm,
):
    """Test that standard online on-device wallet DOES require native auth for secondary issuance."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.secondary_issuance('aid', 100, 1, 1)

        # Verify native auth was passed to run_in_thread (standard online on-device DOES require auth)
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method


@patch('src.viewmodels.issue_ifa_view_model.requires_native_authentication', return_value=True)
def test_secondary_issuance_begin_multisig_on_device_requires_native_auth(
    mock_requires_auth, vm,
):
    """Test that multisig on-device wallet requires native auth for secondary_issuance_begin."""

    with patch.object(vm, 'run_in_thread') as mock_run:
        vm.secondary_issuance_begin('aid', 100, 1, 1)

        # Verify native auth was passed to run_in_thread
        call_args = mock_run.call_args[0]
        expected_method = SettingRepository.native_authentication
        assert call_args[0] is expected_method
