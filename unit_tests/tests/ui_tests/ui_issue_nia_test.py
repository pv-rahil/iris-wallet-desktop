"""Unit test for Issue NIA UI."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from src.model.common_operation_model import IssueAssetDraftModel
from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_issue_nia import IssueNIAWidget
from unit_tests.tests.ui_tests.ui_helper_test.issue_asset_helper_test import assert_success_page_called


@pytest.fixture
def issue_nia_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_issue_nia_view_model(issue_nia_page_navigation: MagicMock):
    """Fixture to create a MainViewModel instance with mocked page navigation."""
    return MainViewModel(issue_nia_page_navigation)


@pytest.fixture
def issue_nia_widget(mock_issue_nia_view_model: MainViewModel):
    """Fixture to create a IssueNIAWidget instance."""
    return IssueNIAWidget(mock_issue_nia_view_model)


def test_asset_issued_success_and_draft_cleanup(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover draft cleanup, timer stop, and success page navigation with correct callback."""
    widget = issue_nia_widget
    widget.from_draft = True
    widget.draft_id = 7
    widget.render_timer.stop = MagicMock()

    svc = MagicMock()
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
    )
    widget._view_model.page_navigation.show_success_page = MagicMock()
    widget._view_model.page_navigation.fungibles_asset_page = MagicMock()

    asset_name = 'NIA-Asset'
    widget.asset_issued(asset_name)

    # Draft cleanup and success page
    svc.delete_draft_issue_asset.assert_called_once_with(7)
    widget.render_timer.stop.assert_called_once()
    widget._view_model.page_navigation.show_success_page.assert_called_once()

    params = widget._view_model.page_navigation.show_success_page.call_args[0][0]
    assert_success_page_called(widget, asset_name)
    assert params.callback == widget._view_model.page_navigation.fungibles_asset_page


def test_handle_nia_hw_dialog_update_shows_dialog(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover dialog update and show when not visible using get_instance()."""
    widget = issue_nia_widget
    # Mock isVisible so handle_nia_hw_dialog doesn't return early
    widget.isVisible = MagicMock(return_value=True)
    dlg = MagicMock()
    dlg.isVisible.return_value = False
    mocker.patch(
        'src.views.ui_issue_nia.HardwareWalletOperationDialog.get_instance', return_value=dlg,
    )

    widget.handle_nia_hw_dialog('msg', MagicMock())

    dlg.update_dialog.assert_called_once()
    dlg.show.assert_called_once()


def test_handle_nia_utxo_created_accepts_and_calls_issue(issue_nia_widget: IssueNIAWidget, mocker):
    """On status True: accept dialog if visible and call on_issue_nia_click."""
    widget = issue_nia_widget
    dlg = MagicMock()
    with patch.object(widget, 'on_issue_nia_click', new=MagicMock()) as mock_click:
        dlg.isVisible.return_value = True
        mocker.patch(
            'src.views.ui_issue_nia.HardwareWalletOperationDialog.get_instance', return_value=dlg,
        )
        # Gate by current purpose for accept path
        widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_nia'
        widget.handle_nia_utxo_created(True)

        dlg.accept.assert_called_once()
        mock_click.assert_called_once()


def test_handle_nia_issue_reuse_existing_psbt(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover existing PSBT branch -> show_nia_psbt_page called."""
    widget = issue_nia_widget
    svc = MagicMock()
    svc.list_psbt.return_value = [
        {'purpose': 'issue_asset_nia', 'psbt': 'psbt123'},
    ]
    with patch.object(widget, 'show_nia_psbt_page', new=MagicMock()) as mock_show:
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )

        widget.handle_nia_issue()
        mock_show.assert_called_once_with('psbt123')


def test_handle_nia_issue_create_utxos_when_no_psbt(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover else branch -> create_utxos_begin called (also covers wallet_service None path separately)."""
    widget = issue_nia_widget
    svc = MagicMock()
    svc.list_psbt.return_value = []
    with patch.object(widget, 'show_nia_psbt_page', new=MagicMock()):
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )
    widget._view_model.utxo_creation_view_model.create_utxos_begin = MagicMock()

    widget.handle_nia_issue()
    # Implementation now passes a required count along with purpose; assert purpose only
    assert widget._view_model.utxo_creation_view_model.create_utxos_begin.called
    args, _ = widget._view_model.utxo_creation_view_model.create_utxos_begin.call_args
    assert args[0] == 'issue_asset_nia'


def test_handle_nia_issue_wallet_service_none(issue_nia_widget: IssueNIAWidget, mocker):
    """If wallet service is None, unsigned_psbts becomes [], so create_utxos_begin is called."""
    widget = issue_nia_widget
    with patch.object(widget, 'show_nia_psbt_page', new=MagicMock()):
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=None,
        )
    widget._view_model.utxo_creation_view_model.create_utxos_begin = MagicMock()

    widget.handle_nia_issue()
    assert widget._view_model.utxo_creation_view_model.create_utxos_begin.called
    args, _ = widget._view_model.utxo_creation_view_model.create_utxos_begin.call_args
    assert args[0] == 'issue_asset_nia'


def test_show_nia_psbt_page_navigates(issue_nia_widget: IssueNIAWidget):
    """Cover positive path of show_nia_psbt_page: disconnect unsigned_psbt and navigate."""
    widget = issue_nia_widget
    # Mock isVisible so show_nia_psbt_page doesn't return early
    widget.isVisible = MagicMock(return_value=True)
    widget._view_model.page_navigation.receive_asset_page = MagicMock()
    # Gate by current purpose
    widget._view_model.utxo_creation_view_model.current_purpose = 'issue_asset_nia'
    widget.show_nia_psbt_page('psbtXYZ')
    widget._view_model.page_navigation.receive_asset_page.assert_called_once()


def test_create_issue_asset_draft_calls_upsert(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover upsert call with int conversion."""
    widget = issue_nia_widget
    svc = MagicMock()
    with patch.object(widget, 'show_nia_psbt_page', new=MagicMock()):
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )

    widget.create_issue_asset_draft('TICK', 'Name', '25')
    svc.upsert_draft_issue_asset.assert_called_once_with(
        IssueAssetDraftModel(
            name='Name', ticker='TICK', issued_amount=25,
        ),
    )


def test_load_draft_data_populates_fields(issue_nia_widget: IssueNIAWidget, mocker):
    """Cover population of fields when draft exists and matches draft_id."""
    widget = issue_nia_widget
    widget.draft_id = 9
    svc = MagicMock()
    svc.list_draft_issue_assets.return_value = [{
        'id': 9, 'name': 'nm', 'ticker': 'tk', 'issued_amount': 3,
    }]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
    )

    widget.asset_name_input = MagicMock()
    widget.short_identifier_input = MagicMock()
    widget.amount_input = MagicMock()
    with patch.object(widget, 'handle_button_enabled', new=MagicMock()):
        widget._load_draft_data()

    widget.asset_name_input.setText.assert_called_once_with('nm')
    widget.short_identifier_input.setText.assert_called_once_with('tk')
    widget.amount_input.setText.assert_called_once_with('3')


def test_retranslate_ui(issue_nia_widget: IssueNIAWidget):
    """Test that the UI strings are correctly translated."""
    issue_nia_widget.retranslate_ui()

    assert issue_nia_widget.asset_ticker_label.text() == 'asset_ticker'
    assert issue_nia_widget.asset_name_label.text() == 'asset_name'


def test_on_issue_nia_click(issue_nia_widget: IssueNIAWidget, qtbot):
    """Test the on_issue_nia_click method."""
    widget = issue_nia_widget

    # Mock the input fields
    widget.short_identifier_input = MagicMock()
    widget.short_identifier_input.text.return_value = 'TTK'

    widget.asset_name_input = MagicMock()
    widget.asset_name_input.text.return_value = 'NIA'

    widget.amount_input = MagicMock()
    widget.amount_input.text.return_value = '100'

    # Avoid creating draft during click in this unit test
    widget.from_draft = True
    # Mock the view model method
    widget._view_model.issue_nia_asset_view_model.on_issue_click = MagicMock()

    # Simulate the click event
    widget.on_issue_nia_click()

    # Verify that the view model method was called with the correct arguments
    widget._view_model.issue_nia_asset_view_model.on_issue_click.assert_called_once_with(
        'TTK', 'NIA', '100',
    )


def test_handle_button_enabled(issue_nia_widget: IssueNIAWidget, qtbot):
    """Test the handle_button_enabled method."""
    widget = issue_nia_widget

    # Mock the input fields
    widget.short_identifier_input = MagicMock()
    widget.amount_input = MagicMock()
    widget.asset_name_input = MagicMock()
    widget.issue_nia_btn = MagicMock()

    # Case when all fields are filled
    widget.short_identifier_input.text.return_value = 'TTK'
    widget.amount_input.text.return_value = '100'
    widget.asset_name_input.text.return_value = 'NIA'

    widget.handle_button_enabled()
    widget.issue_nia_btn.setDisabled.assert_called_once_with(False)

    # Case when one of the fields is empty
    widget.short_identifier_input.text.return_value = ''

    widget.handle_button_enabled()
    widget.issue_nia_btn.setDisabled.assert_called_with(True)


def test_asset_issued(issue_nia_widget: IssueNIAWidget, qtbot):
    """Test the asset_issued method."""
    widget = issue_nia_widget

    # Mock the view model's navigation
    widget._view_model.page_navigation.show_success_page = MagicMock()
    widget._view_model.page_navigation.fungibles_asset_page = MagicMock()

    # Simulate asset issuance
    asset_name = 'NIA'
    widget.asset_issued(asset_name)

    # Verify that the success page is shown with correct parameters
    widget._view_model.page_navigation.show_success_page.assert_called_once()

    params = widget._view_model.page_navigation.show_success_page.call_args[0][0]
    assert_success_page_called(widget, asset_name)
    assert params.callback == widget._view_model.page_navigation.fungibles_asset_page


def test_update_loading_state_true(issue_nia_widget: IssueNIAWidget):
    """Test the update_loading_state method when is_loading is True."""

    issue_nia_widget.render_timer = MagicMock()
    issue_nia_widget.issue_nia_btn = MagicMock()
    issue_nia_widget.nia_close_btn = MagicMock()

    # Call the method with is_loading=True
    issue_nia_widget.update_loading_state(True)

    # Assert that the render_timer starts
    issue_nia_widget.render_timer.start.assert_called_once()

    # Assert that the issue_nia_btn starts loading
    issue_nia_widget.issue_nia_btn.start_loading.assert_called_once()

    # Assert that the nia_close_btn is disabled
    issue_nia_widget.nia_close_btn.setDisabled.assert_called_once_with(
        True,
    )


def test_update_loading_state_false(issue_nia_widget: IssueNIAWidget):
    """Test the update_loading_state method when is_loading is False."""

    issue_nia_widget.render_timer = MagicMock()
    issue_nia_widget.issue_nia_btn = MagicMock()
    issue_nia_widget.nia_close_btn = MagicMock()

    # Call the method with is_loading=False
    issue_nia_widget.update_loading_state(False)

    # Assert that the render_timer stops
    issue_nia_widget.render_timer.stop.assert_called_once()

    # Assert that the issue_nia_btn stops loading
    issue_nia_widget.issue_nia_btn.stop_loading.assert_called_once()

    # Assert that the nia_close_btn is enabled
    issue_nia_widget.nia_close_btn.setDisabled.assert_called_once_with(
        False,
    )
