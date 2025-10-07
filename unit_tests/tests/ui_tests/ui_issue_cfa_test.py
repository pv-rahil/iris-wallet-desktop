"""Unit test for Issue CFA UI."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSize

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.toast import ToastManager
from src.views.ui_issue_cfa import IssueCFAWidget
from unit_tests.tests.ui_tests.ui_helper_test.issue_asset_helper_test import assert_success_page_called


@pytest.fixture
def issue_cfa_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_issue_cfa_view_model(issue_cfa_page_navigation: MagicMock):
    """Fixture to create a MainViewModel instance with mocked page navigation."""
    return MainViewModel(issue_cfa_page_navigation)


@pytest.fixture
def issue_cfa_widget(mock_issue_cfa_view_model: MainViewModel):
    """Fixture to create a IssueCFAWidget instance."""

    return IssueCFAWidget(mock_issue_cfa_view_model)


@pytest.fixture(autouse=True, scope='session')
def _disable_toast_ui():
    """Disable toast UI creation for the whole test session to avoid headless teardown errors."""

    def _noop(*_a, **_k):
        return None

    # Persist stubs for the session; do not restore to avoid late event-loop callbacks
    try:
        setattr(ToastManager, '_create_toast', _noop)
    except Exception:
        pass
    try:
        setattr(ToastManager, 'error', _noop)
    except Exception:
        pass


def test_retranslate_ui(issue_cfa_widget: IssueCFAWidget):
    """Test that the UI strings are correctly translated."""
    issue_cfa_widget.retranslate_ui()
    assert issue_cfa_widget.total_supply_label.text() == 'total_supply'
    assert issue_cfa_widget.asset_name_label.text() == 'asset_name'


def test_on_issue_cfa(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the on_issue_cfa method."""
    widget = issue_cfa_widget

    # Mock the view model method
    widget._view_model.issue_cfa_asset_view_model.issue_cfa_asset = MagicMock()

    # Set input values
    widget.asset_description_input.setText('Description')
    widget.name_of_the_asset_input.setText('Asset Name')
    widget.amount_input.setText('1000')

    # Simulate the button click
    widget.on_issue_cfa()

    # Verify that the view model method is called with the correct arguments
    widget._view_model.issue_cfa_asset_view_model.issue_cfa_asset.assert_called_once_with(
        'Description', 'Asset Name', '1000',
    )


def test_on_upload_asset_file(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the on_upload_asset_file method."""
    widget = issue_cfa_widget

    # Mock the view model method
    widget._view_model.issue_cfa_asset_view_model.open_file_dialog = MagicMock()

    # Simulate the button click
    widget.on_upload_asset_file()

    # Verify that the file dialog is opened
    widget._view_model.issue_cfa_asset_view_model.open_file_dialog.assert_called_once()


def test_on_close(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the on_close method."""
    widget = issue_cfa_widget

    # Mock the page navigation method
    widget._view_model.page_navigation.collectibles_asset_page = MagicMock()

    # Simulate the button click
    widget.on_close()

    # Verify that the page navigation method is called
    widget._view_model.page_navigation.collectibles_asset_page.assert_called_once()


def test_handle_button_enabled(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the handle_button_enabled method."""
    widget = issue_cfa_widget

    # Mock the inputs and button
    widget.amount_input = MagicMock()
    widget.asset_description_input = MagicMock()
    widget.name_of_the_asset_input = MagicMock()
    widget.issue_cfa_button = MagicMock()

    # Case when all fields are filled
    widget.amount_input.text.return_value = '1000'
    widget.asset_description_input.text.return_value = 'Description'
    widget.name_of_the_asset_input.text.return_value = 'Asset Name'

    widget.handle_button_enabled()
    widget.issue_cfa_button.setDisabled.assert_called_once_with(False)

    # Case when one of the fields is empty
    widget.name_of_the_asset_input.text.return_value = ''

    widget.handle_button_enabled()
    assert widget.issue_cfa_button.isEnabled()


def test_update_loading_state(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the update_loading_state method."""
    widget = issue_cfa_widget

    # Mock the button's loading methods
    widget.issue_cfa_button.start_loading = MagicMock()
    widget.issue_cfa_button.stop_loading = MagicMock()

    # Test loading state true
    widget.update_loading_state(True)
    widget.issue_cfa_button.start_loading.assert_called_once()
    widget.issue_cfa_button.stop_loading.assert_not_called()

    # Test loading state false
    widget.update_loading_state(False)
    # still called once from previous
    widget.issue_cfa_button.start_loading.assert_called_once()
    widget.issue_cfa_button.stop_loading.assert_called_once()


def test_show_asset_issued(issue_cfa_widget: IssueCFAWidget, qtbot):
    """Test the show_asset_issued method."""
    widget = issue_cfa_widget

    # Mock the success page method
    widget._view_model.page_navigation.show_success_page = MagicMock()
    widget._view_model.page_navigation.collectibles_asset_page = MagicMock()

    # Simulate asset issuance
    asset_name = 'Asset Name'
    widget.show_asset_issued(asset_name)

    # Verify that the success page is shown with correct parameters
    widget._view_model.page_navigation.show_success_page.assert_called_once()

    params = widget._view_model.page_navigation.show_success_page.call_args[0][0]
    assert_success_page_called(widget, asset_name)
    assert params.callback == widget._view_model.page_navigation.collectibles_asset_page


def test_show_asset_issued_deletes_draft_when_from_draft(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover draft cleanup and render timer stop and success navigation."""
    widget = issue_cfa_widget
    widget.from_draft = True
    widget.draft_id = 42
    with patch.object(widget.render_timer, 'stop', new=MagicMock()) as mock_stop:
        svc = MagicMock()
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )
        widget._view_model.page_navigation.show_success_page = MagicMock()

        widget.show_asset_issued('A')

        svc.delete_draft_issue_asset.assert_called_once_with(42)
        mock_stop.assert_called_once()
        widget._view_model.page_navigation.show_success_page.assert_called_once()


def test_handle_cfa_hw_dialog_update_shows_dialog(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover dialog creation, update, and show when message/type present."""
    widget = issue_cfa_widget
    dlg = MagicMock()
    dlg.isVisible.return_value = False
    mocker.patch(
        'src.views.ui_issue_cfa.HardwareWalletOperationDialog.get_instance', return_value=dlg,
    )

    widget.handle_cfa_hw_dialog_update('msg', MagicMock())

    dlg.update_dialog.assert_called_once()
    dlg.show.assert_called_once()


def test_handle_cfa_utxo_created_accepts_and_calls_issue(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover utxo created path: disconnect, accept visible dialog, then on_issue_cfa."""
    widget = issue_cfa_widget
    dlg = MagicMock()
    dlg.isVisible.return_value = True
    with patch.object(widget, 'on_issue_cfa', new=MagicMock()):
        mocker.patch(
            'src.views.ui_issue_cfa.HardwareWalletOperationDialog.get_instance', return_value=dlg,
        )

        widget.handle_cfa_utxo_created(True)

    dlg.accept.assert_called_once()


def test_handle_cfa_issue_reuse_existing_psbt(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover existing PSBT branch -> show_cfa_psbt_page called."""
    widget = issue_cfa_widget
    svc = MagicMock()
    svc.list_psbt.return_value = [{'purpose': 'issue_asset', 'psbt': 'abc'}]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
    )
    with patch.object(widget, 'show_cfa_psbt_page', new=MagicMock()) as mock_show:
        widget.handle_cfa_issue()
        mock_show.assert_called_once_with('abc')


def test_handle_cfa_issue_create_utxos_when_no_psbt(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover else branch -> create_utxos_begin called."""
    widget = issue_cfa_widget
    svc = MagicMock()
    svc.list_psbt.return_value = []
    with patch.object(widget._view_model.utxo_creation_view_model, 'create_utxos_begin', new=MagicMock()):
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )

        widget.handle_cfa_issue()
        widget._view_model.utxo_creation_view_model.create_utxos_begin.assert_called_once_with(
            'issue_asset',
        )


def test_create_issue_cfa_draft_success_and_exception(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover upsert call (with int conversion) and exception swallow path."""
    widget = issue_cfa_widget
    svc = MagicMock()
    with patch.object(widget._view_model.utxo_creation_view_model, 'create_utxos_begin', new=MagicMock()):
        mocker.patch(
            'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
        )

    widget.create_issue_cfa_draft('N', 'TICK', '10', '/tmp/x')
    svc.upsert_draft_issue_asset.assert_called_once_with(
        name='N', ticker='TICK', issued_amount=10, file_path='/tmp/x',
    )

    # exception path
    svc.upsert_draft_issue_asset.side_effect = Exception('boom')
    widget.create_issue_cfa_draft('N', 'TICK', '0', None)


def test_load_cfa_draft_data_paths(issue_cfa_widget: IssueCFAWidget, mocker):
    """Cover wallet_service None, no draft, and full draft with file path branch."""
    widget = issue_cfa_widget

    # wallet_service is None branch
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=None,
    )
    widget._load_cfa_draft_data()  # should early return without error

    # no draft branch
    widget.draft_id = 5
    svc = MagicMock()
    svc.list_draft_issue_assets.return_value = [{'id': 1}]
    mocker.patch(
        'src.data.service.wallet_data_service.WalletDataService.get_session', return_value=svc,
    )
    widget._load_cfa_draft_data()  # early return

    # full draft with file path and existing file
    widget.name_of_the_asset_input = MagicMock()
    widget.asset_description_input = MagicMock()
    widget.amount_input = MagicMock()
    widget.file_path = MagicMock()
    with patch.object(widget, 'handle_button_enabled', new=MagicMock()) as mock_button:
        with patch.object(widget, 'show_file_preview', new=MagicMock()) as mock_preview:
            widget._view_model.issue_cfa_asset_view_model.uploaded_file_path = None
            fp = '/tmp/file.png'
            svc.list_draft_issue_assets.return_value = [{
                'id': 5, 'name': 'nm', 'ticker': 'tk', 'issued_amount': 3, 'file_path': fp,
            }]
            mocker.patch(
                'src.views.ui_issue_cfa.os.path.exists',
                return_value=True,
            )
            widget._load_cfa_draft_data()
            widget.name_of_the_asset_input.setText.assert_called_once_with(
                'nm',
            )
            widget.asset_description_input.setText.assert_called_once_with(
                'tk',
            )
            widget.amount_input.setText.assert_called_once_with('3')
            assert widget._view_model.issue_cfa_asset_view_model.uploaded_file_path == fp
            mock_preview.assert_called_once_with(fp)
            mock_button.assert_called_once()


def test_show_cfa_psbt_page_navigates(issue_cfa_widget: IssueCFAWidget):
    """Cover positive path of show_cfa_psbt_page."""
    widget = issue_cfa_widget
    widget._view_model.page_navigation.receive_asset_page = MagicMock()
    widget.show_cfa_psbt_page('abc')
    widget._view_model.page_navigation.receive_asset_page.assert_called_once()


def test_show_file_preview(issue_cfa_widget: IssueCFAWidget, mocker):
    """Test the show_file_preview method."""
    widget = issue_cfa_widget

    # Mock os.path.getsize
    mock_getsize = mocker.patch('os.path.getsize')

    # Mock QCoreApplication.translate
    mock_translate = mocker.patch('PySide6.QtCore.QCoreApplication.translate')
    mock_translate.return_value = 'Mocked translation {}'

    # Mock resize_image
    mock_resize_image = mocker.patch('src.views.ui_issue_cfa.resize_image')
    mock_resize_image.return_value = 'resized_image_path'

    # Mock QPixmap
    _mock_pixmap = mocker.patch('PySide6.QtGui.QPixmap')

    # Mock button and card methods
    widget.issue_cfa_button.setDisabled = MagicMock()
    widget.issue_cfa_card.setMaximumSize = MagicMock()
    widget.file_path.setText = MagicMock()
    widget.file_path.setPixmap = MagicMock()
    widget.upload_file.setText = MagicMock()

    # Test case 1: File size exceeds maximum
    mock_getsize.return_value = 6 * 1024 * 1024  # 6MB
    file_path = '/path/to/large_image.jpg'

    widget.show_file_preview(file_path)

    # Verify behavior for large file
    mock_translate.assert_called_with(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'image_validation', None,
    )
    widget.file_path.setText.assert_called_with('Mocked translation 5')
    widget.issue_cfa_button.setDisabled.assert_called_with(True)
    widget.issue_cfa_card.setMaximumSize.assert_called_with(QSize(499, 608))

    # Test case 2: File size within limit
    mock_getsize.return_value = 2 * 1024 * 1024  # 2MB
    file_path = '/path/to/valid_image.jpg'

    # Reset mocks
    widget.file_path.setText.reset_mock()
    widget.issue_cfa_button.setDisabled.reset_mock()
    widget.issue_cfa_card.setMaximumSize.reset_mock()
    mock_translate.reset_mock()

    widget.show_file_preview(file_path)

    # Verify behavior for valid file
    widget.file_path.setText.assert_called_with(file_path)
    widget.issue_cfa_card.setMaximumSize.assert_called_with(QSize(499, 808))
    mock_resize_image.assert_called_with(file_path, 242, 242)
    widget.file_path.setPixmap.assert_called_once()
    mock_translate.assert_called_with(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'change_uploaded_file', 'CHANGE UPLOADED FILE',
    )
    widget.upload_file.setText.assert_called_with('Mocked translation {}')
    widget.issue_cfa_button.setDisabled.assert_called_with(False)
