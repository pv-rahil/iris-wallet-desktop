"""Unit test for view unspent list view model"""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from rgb_lib import RgbAllocation
from rgb_lib import Unspent
from rgb_lib import Utxo

from src.model.btc_model import UnspentsListResponseModel
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import CommonException
from src.viewmodels.view_unspent_view_model import UnspentListViewModel


@pytest.fixture
def mock_page_navigation():
    """Fixture for creating a mock page navigation object."""
    return MagicMock()


@pytest.fixture
def unspent_list_view_model(mock_page_navigation):
    """Fixture for creating an instance of UnspentListViewModel with a mock page navigation object."""
    return UnspentListViewModel(mock_page_navigation)


@pytest.fixture
def mock_list_unspents_response():
    """Fixture for creating a mock list_unspents api."""
    mocked_unspent_list_response = [
        Unspent(
            utxo=Utxo(
                outpoint='efed66f5309396ff43c8a09941c8103d9d5bbffd473ad9f13013ac89fb6b4671:0',
                btc_amount=1000,
                colorable=True,
                exists=False,  # Add default or actual value for exists if necessary
            ),
            rgb_allocations=[
                RgbAllocation(
                    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
                    amount=42,
                    settled=False,
                ),
            ],
        ),
    ]
    mock_response_model = UnspentsListResponseModel(
        unspents=mocked_unspent_list_response,
    )
    return mock_response_model


@patch('src.data.repository.btc_repository.BtcRepository.list_unspents')
@patch('src.utils.cache.Cache.get_cache_session')
@patch.object(UnspentListViewModel, 'run_in_thread')
def test_get_unspent_list_success(mock_run_in_thread, mock_cache, mock_list_unspents, unspent_list_view_model, mock_list_unspents_response):
    """Test get_unspent_list method when the API call succeeds."""
    # Create a mock function to connect to the signal
    list_loaded_mock = Mock()
    mock_loading_started = Mock()
    unspent_list_view_model.loading_started.connect(mock_loading_started)
    mock_loading_finished = Mock()
    unspent_list_view_model.loading_finished.connect(mock_loading_finished)
    unspent_list_view_model.list_loaded.connect(list_loaded_mock)

    mock_cache_session = Mock()
    mock_cache.return_value = mock_cache_session
    mock_list_unspents.return_value = mock_list_unspents_response

    # Patch run_in_thread so that it calls the success callback immediately
    def fake_run_in_thread(func, kwargs):
        kwargs['callback'](mock_list_unspents_response, True)

    mock_run_in_thread.side_effect = fake_run_in_thread

    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET):
        unspent_list_view_model.get_unspent_list(is_hard_refresh=True)

    # Assertions
    mock_cache.assert_called_once()
    mock_cache_session.invalidate_cache.assert_called_once()
    assert [
        (str(u.utxo.outpoint), u.utxo.btc_amount)
        for u in unspent_list_view_model.unspent_list
    ] == [
        (str(u.utxo.outpoint), u.utxo.btc_amount)
        for u in mock_list_unspents_response.unspents
    ]
    list_loaded_mock.assert_called_once_with(True)
    mock_loading_finished.assert_called_once_with(False)
    mock_loading_started.assert_called_once_with(True)


@patch('src.views.components.toast.ToastManager.error')
@patch('src.data.service.wallet_data_service.WalletDataService.get_session')
def test_get_unspent_list_offline_wallet_success(mock_get_session, mock_toast, unspent_list_view_model, mock_list_unspents_response):
    """When wallet type is OFFLINE, it should fetch via WalletDataService and emit success."""
    # Force offline branch
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.OFFLINE_TYPE_WALLET):
        # Provide a session with list_unspents
        session = Mock()
        session.list_unspents.return_value = mock_list_unspents_response
        mock_get_session.return_value = session

        list_loaded = Mock()
        loading_started = Mock()
        loading_finished = Mock()
        unspent_list_view_model.list_loaded.connect(list_loaded)
        unspent_list_view_model.loading_started.connect(loading_started)
        unspent_list_view_model.loading_finished.connect(loading_finished)

        unspent_list_view_model.get_unspent_list(is_hard_refresh=False)

        loading_started.assert_called_once_with(True)
        # should set list and finish loading
        assert [
            (str(u.utxo.outpoint), u.utxo.btc_amount)
            for u in unspent_list_view_model.unspent_list
        ] == [
            (str(u.utxo.outpoint), u.utxo.btc_amount)
            for u in mock_list_unspents_response.unspents
        ]
        list_loaded.assert_called_once_with(True)
        loading_finished.assert_called_once_with(False)
        mock_toast.assert_not_called()


@patch('src.views.components.toast.ToastManager.error')
@patch.object(UnspentListViewModel, 'run_in_thread')
@patch('src.data.repository.btc_repository.BtcRepository.list_unspents')
@patch('src.utils.cache.Cache.get_cache_session')
def test_get_unspent_list_online_error_path_emits_error(mock_cache, mock_list_unspents, mock_run_in_thread, mock_toast, unspent_list_view_model):
    """Simulate error callback to cover error() path."""
    mock_cache.return_value = Mock()

    def fake_run(func, kwargs):
        kwargs['error_callback'](CommonException('boom'))

    mock_run_in_thread.side_effect = fake_run
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET):
        unspent_list_view_model.get_unspent_list(is_hard_refresh=True)

    mock_toast.assert_called_once()
    finished = Mock()
    unspent_list_view_model.loading_finished.connect(finished)
    unspent_list_view_model.loading_finished.emit(True)
    finished.assert_called_with(True)


@patch('src.views.components.toast.ToastManager.error')
def test_get_unspent_list_exception_handling(mock_toast, unspent_list_view_model):
    """Force an exception in try block and ensure except path is covered."""
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', side_effect=Exception('bad')):
        finished = Mock()
        unspent_list_view_model.loading_finished.connect(finished)
        unspent_list_view_model.get_unspent_list(is_hard_refresh=False)
        finished.assert_called_once_with(True)
        assert mock_toast.called


@patch.object(UnspentListViewModel, 'run_in_thread')
@patch('src.data.repository.btc_repository.BtcRepository.list_unspents')
@patch('src.utils.cache.Cache.get_cache_session')
def test_get_unspent_list_no_hard_refresh_no_cache_call(mock_cache, mock_list_unspents, mock_run_in_thread, unspent_list_view_model, mock_list_unspents_response):
    """When is_hard_refresh is False, it should not invalidate cache and still run thread for online wallet."""
    mock_cache.return_value = Mock()

    def fake_run(func, kwargs):
        kwargs['callback'](mock_list_unspents_response, True)

    mock_run_in_thread.side_effect = fake_run
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET):
        unspent_list_view_model.get_unspent_list(is_hard_refresh=False)

    # Cache.get_cache_session should not be called at all when not hard refresh
    mock_cache.assert_not_called()
    assert unspent_list_view_model.unspent_list


@patch.object(UnspentListViewModel, 'run_in_thread')
@patch('src.data.repository.btc_repository.BtcRepository.list_unspents')
@patch('src.utils.cache.Cache.get_cache_session')
def test_get_unspent_list_filters_none_unspents(mock_cache, mock_list_unspents, mock_run_in_thread, unspent_list_view_model):
    """Ensure None entries in response.unspents are filtered out in success handler."""
    mock_cache.return_value = Mock()
    resp = UnspentsListResponseModel(unspents=[None])

    def fake_run(func, kwargs):
        kwargs['callback'](resp, True)

    mock_run_in_thread.side_effect = fake_run
    with patch('src.data.repository.setting_repository.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET):
        unspent_list_view_model.get_unspent_list(is_hard_refresh=True)

    assert unspent_list_view_model.unspent_list == []
