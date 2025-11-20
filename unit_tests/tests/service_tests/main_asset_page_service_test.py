"""Unit tests for main asset page service"""
# pylint: disable=redefined-outer-name,unused-argument,too-many-arguments,unused-import
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from rgb_lib import AssetSchema
from rgb_lib import RgbLibError

from src.data.service.main_asset_page_service import MainAssetPageDataService
from src.model.common_operation_model import MainPageDataResponseModel
from src.model.enums.enums_model import WalletType
from src.model.rgb_model import FilterAssetRequestModel
from src.model.setting_model import IsHideExhaustedAssetEnabled
from unit_tests.repository_fixture.btc_repository_mock import mock_get_btc_balance
from unit_tests.repository_fixture.rgb_repository_mock import mock_get_asset
from unit_tests.repository_fixture.rgb_repository_mock import mock_list_transfers
from unit_tests.repository_fixture.rgb_repository_mock import mock_refresh_transfer
from unit_tests.repository_fixture.setting_repository_mocked import mock_get_wallet_type
from unit_tests.repository_fixture.setting_repository_mocked import mock_is_exhausted_asset_enabled
from unit_tests.service_test_resources.mocked_fun_return_values.main_asset_service import (
    GetAssetResponseModel as MockGetAssetResponseModel,
)
from unit_tests.service_test_resources.mocked_fun_return_values.main_asset_service import (
    mock_balance_response_data,
)
from unit_tests.service_test_resources.mocked_fun_return_values.main_asset_service import mock_get_asset_response_model
from unit_tests.service_test_resources.mocked_fun_return_values.main_asset_service import mock_get_asset_response_model_when_exhausted_asset
from unit_tests.service_test_resources.service_fixture.main_asset_page_helper_mock import mock_get_asset_name
from unit_tests.service_test_resources.service_fixture.main_asset_page_helper_mock import (
    mock_get_offline_asset_ticker,
)


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_get_assets(
    mock_get_wallet_type,
    mock_get_btc_balance,
    mock_get_asset,
    mock_get_offline_asset_ticker,
    mock_get_asset_name,
    mock_refresh_transfer,
    mock_is_exhausted_asset_enabled,
):
    """Test case  for main asset page service when wallet type embedded"""

    # Taking mocked object to check if the method is called once
    # Passing data for the return value of the mocked function
    get_btc_balance = mock_get_btc_balance(mock_balance_response_data)
    refresh_asset = mock_refresh_transfer({})
    get_asset = mock_get_asset(mock_get_asset_response_model)
    asset_name = mock_get_asset_name('rBitcoin')
    asset_ticker = mock_get_offline_asset_ticker('rBTC')
    is_exhausted_asset_enabled = mock_is_exhausted_asset_enabled(
        IsHideExhaustedAssetEnabled(is_enabled=False),
    )
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    # Execute the function under test
    result = MainAssetPageDataService.get_assets()

    # Assert results
    assert result.nia == mock_get_asset_response_model.nia
    assert result.cfa == mock_get_asset_response_model.cfa
    assert result.uda == mock_get_asset_response_model.uda
    assert result.ifa == mock_get_asset_response_model.ifa
    assert result.vanilla.ticker == 'rBTC'
    assert result.vanilla.name == 'rBitcoin'
    assert result.vanilla.balance.settled == mock_balance_response_data.vanilla.settled
    assert (
        result.vanilla.balance.spendable == mock_balance_response_data.vanilla.spendable
    )
    assert result.vanilla.balance.future == mock_balance_response_data.vanilla.future
    assert isinstance(result.vanilla.balance.settled, int)
    assert isinstance(result.vanilla.balance.spendable, int)
    assert isinstance(result.vanilla.balance.future, int)
    assert isinstance(result, MainPageDataResponseModel)

    # checking the method is called once
    get_asset.assert_called_once_with(
        FilterAssetRequestModel(
            filter_asset_schemas=[
                AssetSchema.NIA,
                AssetSchema.CFA,
                AssetSchema.UDA,
                AssetSchema.IFA,
            ],
        ),
    )
    refresh_asset.assert_called_once()
    asset_name.assert_called_once()
    asset_ticker.assert_called_once()
    get_btc_balance.assert_called_once()
    is_exhausted_asset_enabled.assert_called_once()


@patch('src.data.service.main_asset_page_service.RgbRepository.get_assets')
def test_get_all_assets_flattens_and_handles_none(mock_get_assets):
    """get_all_assets should flatten lists and handle None gracefully."""
    from src.model.rgb_model import GetAssetResponseModel
    # Build a response with mixed lists and None
    response = MagicMock(spec=GetAssetResponseModel)
    a1 = MagicMock(asset_id='n1')
    a2 = MagicMock(asset_id='c1')
    a3 = MagicMock(asset_id='u1')
    a4 = MagicMock(asset_id='i1')
    response.nia = [a1]
    response.cfa = None
    response.uda = [a3]
    response.ifa = [a4]
    mock_get_assets.return_value = response

    svc = MainAssetPageDataService()
    all_assets = svc.get_all_assets()

    assert [a.asset_id for a in all_assets] == ['n1', 'u1', 'i1']
    assert mock_get_assets.called


@patch('src.data.service.main_asset_page_service.RgbRepository.list_transfers')
def test_find_asset_for_failed_transfer_matches_and_skips_on_exception(mock_list_transfers):
    """find_asset_for_failed_transfer should return asset_id when idx matches and skip assets raising exceptions."""
    # Prepare assets; first will raise, second will match
    a_bad = MagicMock(asset_id='bad')
    a_ok = MagicMock(asset_id='ok')
    assets = [a_bad, a_ok]

    # First call raises, second returns transfers with a matching idx
    def side_effect(arg):
        if arg.asset_id == 'bad':
            raise RuntimeError('boom')
        t = MagicMock()
        t.idx = '42'
        return [t]

    mock_list_transfers.side_effect = side_effect

    svc = MainAssetPageDataService()
    found = svc.find_asset_for_failed_transfer('42', assets)

    assert found == 'ok'
    # Ensure list_transfers attempted for both assets
    assert mock_list_transfers.call_count == 2


@patch('src.utils.page_navigation_events.PageNavigationEventManager.get_instance')
@patch('src.data.service.main_asset_page_service.MainAssetPageDataService.find_asset_for_failed_transfer')
@patch('src.data.service.main_asset_page_service.MainAssetPageDataService.get_all_assets')
def test_refresh_transfer_failures_emit_dialog(
    mock_get_all_assets,
    mock_find_asset,
    mock_get_mgr,
):
    """handle_refresh_failures should emit dialog items when failures exist (new separated method design)."""
    # Arrange: one failure with id '1'
    failure_entry = MagicMock()
    failure_entry.failure = RgbLibError.Internal(details='test')
    failures = {'1': failure_entry}

    # Mock assets and mapping
    mock_get_all_assets.return_value = [MagicMock(asset_id='asset-1')]
    mock_find_asset.return_value = 'asset-1'

    # Capture emitted items
    signal = MagicMock()
    mgr = MagicMock()
    mgr.refresh_transfer_result_dialog_signal = signal
    mock_get_mgr.return_value = mgr

    # Act: call the separated method directly
    MainAssetPageDataService().handle_refresh_failures(failures)

    # Assert: dialog emitted with non-empty items list
    assert signal.emit.called
    items = signal.emit.call_args[0][0]
    assert isinstance(items, list) and len(items) == 1
    mock_get_all_assets.assert_called_once()
    mock_find_asset.assert_called_once()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_offline_with_session(
    mock_get_session,
    mock_get_wallet_type,
    mock_get_btc_balance,
    mock_get_asset,
    mock_get_offline_asset_ticker,
    mock_get_asset_name,
    mock_refresh_transfer,
    mock_is_exhausted_asset_enabled,
):
    """Offline wallet: session present -> use session.get_btc_balance, no refresh_transfer, no BtcRepository call."""
    # Arrange
    mock_get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    get_asset = mock_get_asset(mock_get_asset_response_model)
    mock_is_exhausted_asset_enabled(
        IsHideExhaustedAssetEnabled(is_enabled=False),
    )
    mock_get_asset_name('rBitcoin')
    mock_get_offline_asset_ticker('rBTC')
    # Session object with get_btc_balance
    session = MagicMock()
    session.get_btc_balance.return_value = mock_balance_response_data
    mock_get_session.return_value = session
    # Ensure repo balance is NOT used and refresh is NOT called
    get_btc_balance = mock_get_btc_balance(None)
    refresh_asset = mock_refresh_transfer(None)

    # Act
    result = MainAssetPageDataService.get_assets()

    # Assert
    assert result.vanilla.balance.settled == mock_balance_response_data.vanilla.settled
    session.get_btc_balance.assert_called_once()
    refresh_asset.assert_not_called()
    get_btc_balance.assert_not_called()
    get_asset.assert_called_once()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_offline_without_session(
    mock_get_session,
    mock_get_wallet_type,
    mock_get_btc_balance,
    mock_get_asset,
    mock_get_offline_asset_ticker,
    mock_get_asset_name,
    mock_refresh_transfer,
    mock_is_exhausted_asset_enabled,
):
    """Offline wallet: no session -> falls back to BtcRepository.get_btc_balance, no refresh_transfer."""
    mock_get_wallet_type.return_value = WalletType.OFFLINE_TYPE_WALLET
    mock_get_session.return_value = None
    get_asset = mock_get_asset(mock_get_asset_response_model)
    mock_is_exhausted_asset_enabled(
        IsHideExhaustedAssetEnabled(is_enabled=False),
    )
    mock_get_asset_name('rBitcoin')
    mock_get_offline_asset_ticker('rBTC')
    get_btc_balance = mock_get_btc_balance(mock_balance_response_data)
    refresh_asset = mock_refresh_transfer(None)

    result = MainAssetPageDataService.get_assets()

    assert result.vanilla.balance.settled == mock_balance_response_data.vanilla.settled
    get_btc_balance.assert_called_once()
    refresh_asset.assert_not_called()
    get_asset.assert_called_once()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_none_asset_lists_return_path(
    mock_get_wallet_type,
    mock_get_btc_balance,
    mock_get_asset,
    mock_get_offline_asset_ticker,
    mock_get_asset_name,
    mock_refresh_transfer,
    mock_is_exhausted_asset_enabled,
):
    """When assets lists are None, ensure they are returned as empty lists (or [] paths)."""
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    # Return None lists to hit 'or []' code path
    get_asset = mock_get_asset(
        MockGetAssetResponseModel(nia=None, cfa=None, uda=None),
    )
    mock_is_exhausted_asset_enabled(
        IsHideExhaustedAssetEnabled(is_enabled=False),
    )
    mock_get_asset_name('rBitcoin')
    mock_get_offline_asset_ticker('rBTC')
    mock_get_btc_balance(mock_balance_response_data)
    mock_refresh_transfer({})

    result = MainAssetPageDataService.get_assets()
    assert not result.nia
    assert not result.cfa
    assert not result.uda
    assert not result.ifa
    get_asset.assert_called_once()


@patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type')
def test_when_asset_exhausted(
    mock_get_wallet_type,
    mock_get_btc_balance,
    mock_get_asset,
    mock_get_offline_asset_ticker,
    mock_get_asset_name,
    mock_refresh_transfer,
    mock_is_exhausted_asset_enabled,
):
    """Test case  for main asset page service when asset_exhausted"""
    get_btc_balance = mock_get_btc_balance(mock_balance_response_data)
    refresh_asset = mock_refresh_transfer({})
    asset_name = mock_get_asset_name('rBitcoin')
    asset_ticker = mock_get_offline_asset_ticker('rBTC')
    get_asset = mock_get_asset(
        mock_get_asset_response_model_when_exhausted_asset,
    )
    is_exhausted_asset_enabled = mock_is_exhausted_asset_enabled(
        IsHideExhaustedAssetEnabled(is_enabled=True),
    )
    mock_get_wallet_type.return_value = WalletType.ONLINE_TYPE_WALLET
    result = MainAssetPageDataService.get_assets()
    assert len(result.cfa) == 1
    assert len(result.uda) == 1
    assert len(result.nia) == 1
    assert len(result.ifa) == 1
    get_asset.assert_called_once_with(
        FilterAssetRequestModel(
            filter_asset_schemas=[
                AssetSchema.NIA,
                AssetSchema.CFA,
                AssetSchema.UDA,
                AssetSchema.IFA,
            ],
        ),
    )
    refresh_asset.assert_called_once()
    asset_name.assert_called_once()
    asset_ticker.assert_called_once()
    get_btc_balance.assert_called_once()
    is_exhausted_asset_enabled.assert_called_once()
