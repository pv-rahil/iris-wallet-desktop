# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for the PageNavigation class."""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.rgb_model import RgbAssetPageLoadModel
from src.model.success_model import SuccessPageModel
from src.model.transaction_detail_page_model import TransactionDetailPageModel
from src.utils.page_navigation import PageNavigation
from src.utils.page_navigation_events import PageNavigationEventManager
from src.views.main_window import MainWindow


@pytest.fixture
def mock_ui():
    """Mock the MainWindow UI."""
    mock_ui = MagicMock(spec=MainWindow)
    mock_ui.sidebar = MagicMock()
    mock_ui.stacked_widget = MagicMock()
    mock_ui.view_model = MagicMock()
    return mock_ui


@pytest.fixture
def mock_event_manager():
    """Mock the PageNavigationEventManager."""
    event_manager = MagicMock(spec=PageNavigationEventManager)
    event_manager.get_instance.return_value = event_manager
    return event_manager


@pytest.fixture
def page_navigation(mock_ui, mock_event_manager):
    """Create an instance of PageNavigation with mocked dependencies."""
    navigation = PageNavigation(mock_ui)
    # Mock all page widgets
    for page_name in navigation.pages:
        navigation.pages[page_name] = MagicMock(return_value=MagicMock())
    return navigation


def test_splash_screen_page(page_navigation):
    """Test splash_screen_page navigation."""
    page_navigation.splash_screen_page()

    assert page_navigation.current_stack['name'] == 'SplashScreenWidget'


def test_welcome_page(page_navigation):
    """Test welcome_page navigation."""
    page_navigation.welcome_page()

    assert page_navigation.current_stack['name'] == 'Welcome'


def test_term_and_condition_page(page_navigation):
    """Test term_and_condition_page navigation."""
    page_navigation.term_and_condition_page()

    assert page_navigation.current_stack['name'] == 'TermCondition'


def test_fungibles_asset_page(page_navigation):
    """Test fungibles_asset_page navigation."""
    page_navigation.fungibles_asset_page()

    assert page_navigation.current_stack['name'] == 'FungibleAssetWidget'


def test_collectibles_asset_page(page_navigation):
    """Test collectibles_asset_page navigation."""
    page_navigation.collectibles_asset_page()

    assert page_navigation.current_stack['name'] == 'CollectiblesAssetWidget'


def test_set_wallet_password_page(page_navigation):
    """Test set_wallet_password_page navigation."""
    page_navigation.set_wallet_password_page()

    assert page_navigation.current_stack['name'] == 'SetWalletPassword'


def test_enter_wallet_password_page(page_navigation):
    """Test enter_wallet_password_page navigation."""
    page_navigation.enter_wallet_password_page()

    assert page_navigation.current_stack['name'] == 'EnterWalletPassword'


def test_issue_nia_asset_page(page_navigation):
    """Test issue_nia_asset_page navigation."""
    page_navigation.issue_nia_asset_page()

    assert page_navigation.current_stack['name'] == 'IssueNIA'


def test_bitcoin_page(page_navigation):
    """Test bitcoin_page navigation."""
    page_navigation.bitcoin_page()

    assert page_navigation.current_stack['name'] == 'Bitcoin'


def test_issue_cfa_asset_page(page_navigation):
    """Test issue_cfa_asset_page navigation."""
    page_navigation.issue_cfa_asset_page()

    assert page_navigation.current_stack['name'] == 'IssueCFA'


def test_send_cfa_page(page_navigation):
    """Test send_cfa_page navigation."""
    page_navigation.send_cfa_page()

    assert page_navigation.current_stack['name'] == 'SendCFA'


def test_receive_cfa_page(page_navigation):
    """Test receive_cfa_page navigation."""
    params = MagicMock()
    page_navigation.receive_cfa_page(params)

    assert page_navigation.current_stack['name'] == 'ReceiveCFA'


def test_cfa_detail_page(page_navigation):
    """Test cfa_detail_page navigation."""
    params = MagicMock(spec=RgbAssetPageLoadModel)
    page_navigation.cfa_detail_page(params)

    assert page_navigation.current_stack['name'] == 'CFADetail'


def test_send_bitcoin_page(page_navigation):
    """Test send_bitcoin_page navigation."""
    page_navigation.send_bitcoin_page()

    assert page_navigation.current_stack['name'] == 'SendBitcoin'


def test_receive_bitcoin_page(page_navigation):
    """Test receive_bitcoin_page navigation."""
    page_navigation.receive_bitcoin_page()

    assert page_navigation.current_stack['name'] == 'ReceiveBitcoin'


def test_view_unspent_list_page(page_navigation):
    """Test view_unspent_list_page navigation."""
    page_navigation.view_unspent_list_page()

    assert page_navigation.current_stack['name'] == 'ViewUnspentList'


def test_cfa_transaction_detail_page(page_navigation):
    """Test cfa_transaction_detail_page navigation."""
    params = MagicMock(spec=TransactionDetailPageModel)
    page_navigation.cfa_transaction_detail_page(params)

    assert page_navigation.current_stack['name'] == 'CFATransactionDetail'


def test_bitcoin_transaction_detail_page(page_navigation):
    """Test bitcoin_transaction_detail_page navigation."""
    params = MagicMock(spec=TransactionDetailPageModel)
    page_navigation.bitcoin_transaction_detail_page(params)

    assert page_navigation.current_stack['name'] == 'BitcoinTransactionDetail'


def test_backup_page(page_navigation):
    """Test backup_page navigation."""
    page_navigation.backup_page()

    assert page_navigation.current_stack['name'] == 'Backup'


def test_settings_page(page_navigation):
    """Test settings_page navigation."""
    page_navigation.settings_page()

    assert page_navigation.current_stack['name'] == 'Settings'


def test_show_success_page(page_navigation):
    """Test show_success_page navigation."""
    params = MagicMock(spec=SuccessPageModel)
    page_navigation.show_success_page(params)

    assert page_navigation.current_stack['name'] == 'SuccessWidget'


def test_about_page(page_navigation):
    """Test about_page navigation."""
    page_navigation.about_page()

    assert page_navigation.current_stack['name'] == 'AboutWidget'


def test_faucets_page(page_navigation):
    """Test faucets_page navigation."""
    page_navigation.faucets_page()

    assert page_navigation.current_stack['name'] == 'FaucetsWidget'


def test_help_page(page_navigation):
    """Test help_page navigation."""
    page_navigation.help_page()

    assert page_navigation.current_stack['name'] == 'HelpWidget'


def test_sidebar(page_navigation, mock_ui):
    """Test sidebar method."""
    result = page_navigation.sidebar()
    assert result == mock_ui.sidebar


def test_error_report_dialog_box(page_navigation):
    """Test error_report_dialog_box method."""
    with patch('src.utils.page_navigation.ErrorReportDialog') as mock_dialog:
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance

        # Call the method we're testing
        page_navigation.error_report_dialog_box()

        # Verify the dialog was created
        mock_dialog.assert_called_once()

        # Verify the dialog was shown
        mock_dialog_instance.exec.assert_called_once()


def test_selection_page(page_navigation):
    """selection_page should set current stack name and not show sidebar."""
    page_navigation.selection_page()
    assert page_navigation.current_stack['name'] == 'SelectionPage'


def test_hardware_wallet_connect_page_with_flag(page_navigation, mock_ui, monkeypatch):
    """hardware_wallet_connect_page should pass is_multisig flag to widget factory."""
    factory = MagicMock(return_value=MagicMock())
    page_navigation.pages['HardwareWalletConnectPage'] = factory
    # Avoid UI side-effects
    monkeypatch.setattr(page_navigation, 'navigate_and_toggle', MagicMock())

    page_navigation.hardware_wallet_connect_page(is_multisig=True)

    assert page_navigation.current_stack['name'] == 'HardwareWalletConnectPage'
    factory.assert_called_once()
    args, _ = factory.call_args
    # (view_model, is_multisig)
    assert args[0] is mock_ui.view_model
    assert args[1] is True


def test_broadcast_transaction_page_flags(page_navigation, mock_ui, monkeypatch):
    """broadcast_transaction_page should pass from_sidebar flag to widget constructor."""
    factory = MagicMock(return_value=MagicMock())
    page_navigation.pages['BroadcastTransactionWidget'] = factory
    monkeypatch.setattr(page_navigation, 'navigate_and_toggle', MagicMock())

    page_navigation.broadcast_transaction_page()
    page_navigation.broadcast_transaction_page(from_sidebar=True)

    # Two calls: default False, then True
    assert factory.call_count == 2
    first_args, _ = factory.call_args_list[0]
    second_args, _ = factory.call_args_list[1]
    assert first_args[0] is mock_ui.view_model and first_args[1] is False
    assert second_args[0] is mock_ui.view_model and second_args[1] is True


def test_receive_asset_page_sets_params(page_navigation, mock_ui, monkeypatch):
    """receive_asset_page should construct page with provided ReceiveAssetModel params."""
    factory = MagicMock(return_value=MagicMock())
    page_navigation.pages['ReceiveAssetWidget'] = factory
    monkeypatch.setattr(page_navigation, 'navigate_and_toggle', MagicMock())
    params = MagicMock()

    page_navigation.receive_asset_page(params)

    factory.assert_called_once()
    args, _ = factory.call_args
    assert args[0] is mock_ui.view_model and args[1] is params
    assert page_navigation.current_stack['name'] == 'ReceiveAssetWidget'


def test_refresh_transfer_result_dialog_shows_dialog(page_navigation, mocker):
    """Dialog should be constructed with current widget and show() called."""
    parent_widget = MagicMock()
    page_navigation._ui.stacked_widget.currentWidget.return_value = parent_widget
    dlg = MagicMock()
    mocker.patch(
        'src.utils.page_navigation.RefreshTransferDialog',
        return_value=dlg,
    )

    payload = {'k': 'v'}
    page_navigation.refresh_transfer_result_dialog(payload)

    mocker.spy(page_navigation._ui.stacked_widget, 'currentWidget')
    assert dlg.show.called


def test_issue_ifa_page_uses_factory(page_navigation, mock_ui, monkeypatch):
    """issue_ifa_page should use pages factory and pass draft context."""
    factory = MagicMock(return_value=MagicMock())
    page_navigation.pages['IssueIFA'] = factory
    monkeypatch.setattr(page_navigation, 'navigate_and_toggle', MagicMock())

    page_navigation.issue_ifa_page(draft_id=7, from_draft=True)

    factory.assert_called_once()
    args, _ = factory.call_args
    assert args[0] is mock_ui.view_model and args[1] == 7 and args[2] is True
    assert page_navigation.current_stack['name'] == 'IssueIFA'


def test_issue_ifa_secondary_page_calls_widget(page_navigation, mock_ui, mocker):
    """issue_ifa_secondary_page constructs IssueIFAWidget directly with params."""
    widget = MagicMock()
    mocker.patch(
        'src.utils.page_navigation.IssueIFAWidget',
        return_value=widget,
    )
    params = MagicMock(spec=RgbAssetPageLoadModel)

    page_navigation.issue_ifa_secondary_page(
        params, draft_id=9, from_draft=True,
    )

    from src.utils.page_navigation import IssueIFAWidget as _W
    _W.assert_called_once()
    args, _ = _W.call_args
    assert args[0] is mock_ui.view_model and args[1] == 9 and args[2] is True and args[3] is params
    assert page_navigation.current_stack['name'] == 'IssueIFA'


def test_multisig_setup_page_calls_widget(page_navigation, mock_ui, mocker):
    """multisig_setup_page should construct MultisigSetupPage and set current stack."""
    widget = MagicMock()
    mocker.patch(
        'src.utils.page_navigation.MultisigSetupPage',
        return_value=widget,
    )

    page_navigation.multisig_setup_page()

    from src.utils.page_navigation import MultisigSetupPage as _M
    _M.assert_called_once()
    args, _ = _M.call_args
    assert args[0] is mock_ui.view_model
    assert page_navigation.current_stack['name'] == 'MultisigSetupPage'


def test_toggle_sidebar_show_hide(page_navigation, mock_ui):
    """toggle_sidebar should call show/hide on UI sidebar."""
    page_navigation.toggle_sidebar(True)
    mock_ui.sidebar.show.assert_called_once()
    page_navigation.toggle_sidebar(False)
    mock_ui.sidebar.hide.assert_called_once()


def test_show_current_page_adds_and_sets(page_navigation, mock_ui):
    """show_current_page should add and set current widget when not present."""
    widget = MagicMock()
    page_navigation.current_stack = {'name': 'X', 'widget': widget}
    # children() returns list (empty to force add)
    mock_ui.stacked_widget.children = MagicMock(return_value=[])

    page_navigation.show_current_page()

    mock_ui.stacked_widget.addWidget.assert_called_once_with(widget)
    mock_ui.stacked_widget.setCurrentWidget.assert_called_once_with(widget)
