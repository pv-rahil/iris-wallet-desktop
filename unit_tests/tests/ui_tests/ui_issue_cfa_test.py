"""Unit test for Issue CFA UI."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QSize

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.viewmodels.main_view_model import MainViewModel
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
