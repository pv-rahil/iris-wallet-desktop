# pylint: disable=redefined-outer-name,unused-argument,protected-access
"""UI tests for InflatableAssetWidget."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rgb_lib import AssetSchema

from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletType
from src.views.ui_inflatable_asset import InflatableAssetWidget


@pytest.fixture
def vm_mock():
    """Mock for MainAssetViewModel."""
    vm = MagicMock()
    # Signals used in setup_ui_connection and show_assets
    mavm = MagicMock()
    mavm.asset_loaded = MagicMock()
    mavm.asset_loaded.connect = lambda *_a, **_k: None
    mavm.loading_started = MagicMock()
    mavm.loading_started.connect = lambda *_a, **_k: None
    mavm.loading_finished = MagicMock()
    mavm.loading_finished.connect = lambda *_a, **_k: None
    mavm.message = MagicMock()
    mavm.message.connect = lambda *_a, **_k: None
    vm.main_asset_view_model = mavm
    vm.page_navigation = MagicMock()
    return vm


@pytest.fixture
def widget(qt_app, vm_mock):
    """Provide a widget instance configured for inflatable asset view."""
    # Provide a privileges object with permissive defaults
    priv = MagicMock(can_send_transactions=True, can_receive_asset=True)
    cfg = MagicMock(privileges=priv)
    with patch('src.views.ui_inflatable_asset.load_stylesheet', return_value=''), \
            patch('src.views.ui_inflatable_asset.get_current_wallet_mode_config', return_value=cfg), \
            patch('src.views.ui_inflatable_asset.SettingRepository.get_wallet_access_type', return_value=WalletAccessType.WATCH_ONLY), \
            patch('src.views.ui_inflatable_asset.SettingRepository.get_wallet_type', return_value=WalletType.ONLINE_TYPE_WALLET), \
            patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        # Provide empty drafts by default
        get_sess.return_value = MagicMock(list_draft_issue_assets=lambda: [])
        w = InflatableAssetWidget(vm_mock)
        yield w
        w.close()


def test_refresh_asset_calls_get_assets(widget: InflatableAssetWidget, vm_mock):
    """Test that refresh_asset calls get_assets with rgb_asset_hard_refresh=True."""
    vm_mock.main_asset_view_model.get_assets.reset_mock()
    widget.refresh_inflatables_asset()
    vm_mock.main_asset_view_model.get_assets.assert_called_once_with(
        rgb_asset_hard_refresh=True,
    )


def test_show_assets_populates_headers_and_cards(widget: InflatableAssetWidget, vm_mock):
    """Test that show_assets populates headers and cards."""
    # Provide assets
    asset = MagicMock()
    asset.asset_id = 'aid'
    asset.name = 'Name'
    asset.ticker = 'TCK'
    asset.balance.future = 1
    vm_mock.main_asset_view_model.assets.nia = [asset]

    with patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_draft_issue_assets=lambda: [])
        widget.show_inflatables_assets()
        # Ensure header labels have been set
        assert widget.inflatables_name_header.text()
        assert widget.inflatables_address_header.text()
        assert widget.inflatables_amount_header.text()
        assert widget.inflatables_symbol_header.text()


def test_draft_asset_click_navigates_to_issue(widget: InflatableAssetWidget, vm_mock):
    """Test that clicking on a draft asset navigates to the issue page."""
    vm_mock.main_asset_view_model.assets.nia = []
    with patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(
            list_draft_issue_assets=lambda: [
                {'id': 1, 'name': 'Draft', 'ticker': 'DRF'},
            ],
        )
        widget.show_inflatables_assets()
        # A draft card should exist and clicking triggers navigation to issue_ifa_page
        vm_mock.page_navigation.issue_ifa_page.assert_not_called()
        # Simulate click; the connected lambda ignores args and uses captured draft_id
        widget.inflatable_frame.clicked.emit('', '', None, None)
        assert vm_mock.page_navigation.issue_ifa_page.called


def test_normal_asset_click_navigates_detail(widget: InflatableAssetWidget, vm_mock):
    """Test that clicking on a normal asset navigates to the CFA detail page."""
    # Supply a normal asset and ensure click goes to CFA detail page via page navigation
    asset = MagicMock()
    asset.asset_id = 'aid'
    asset.name = 'N'
    asset.ticker = 'T'
    asset.balance.future = 0
    vm_mock.main_asset_view_model.assets.nia = [asset]
    with patch('src.data.service.wallet_data_service.WalletDataService.get_session') as get_sess:
        get_sess.return_value = MagicMock(list_draft_issue_assets=lambda: [])
        widget.show_inflatables_assets()
        # Simulate click
        widget.inflatable_frame.clicked.emit(
            asset.asset_id, asset.name, None, AssetSchema.NIA,
        )
        assert vm_mock.page_navigation.cfa_detail_page.called
