"""Unit test for FaucetsWidget UI."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,too-many-locals,protected-access
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.viewmodels.main_view_model import MainViewModel
from src.views.ui_faucets import FaucetsWidget


@pytest.fixture
def faucet_page_navigation():
    """Fixture to create a mocked page navigation object."""
    mock_navigation = MagicMock()
    return mock_navigation


@pytest.fixture
def mock_faucet_view_model(faucet_page_navigation):
    """Fixture to create a MainViewModel instance with a mocked FaucetsViewModel."""
    mock_view_model = MagicMock(spec=MainViewModel(faucet_page_navigation))
    mock_view_model.faucets_view_model = MagicMock()
    return mock_view_model


@pytest.fixture
def create_faucets_widget(qtbot, mock_faucet_view_model):
    """Fixture to create a FaucetsWidget instance."""
    widget = FaucetsWidget(mock_faucet_view_model)
    qtbot.addWidget(widget)
    return widget


def test_initial_ui_state(create_faucets_widget):
    """Test the initial state of UI elements in FaucetsWidget."""
    widget = create_faucets_widget
    assert widget.faucets_title_frame.title_name.text() == 'faucets'
    assert widget.get_faucets_title_label.text() == 'get_faucets'


def test_create_faucet_frames(create_faucets_widget):
    """Test the creation of faucet frames based on the faucet list."""
    widget = create_faucets_widget

    # Create a sample list of faucets
    faucets_list = [
        MagicMock(asset_name='Faucet1', asset_id='1'),
        MagicMock(asset_name='Faucet2', asset_id='2'),
    ]

    widget.create_faucet_frames(faucets_list)

    # Check if the correct number of faucet frames are created
    # Two faucets + 2 static widgets (title + spacer)
    assert widget.faucet_vertical_layout.count() == 6


def test_create_placeholder_faucet_frame(create_faucets_widget):
    """Test the creation of a placeholder frame when faucet list is None."""
    widget = create_faucets_widget

    # Simulate a scenario where faucet list is None
    widget.create_faucet_frames(None)

    # Count the number of widgets (excluding the spacer)
    widget_count = sum(
        1 for i in range(widget.faucet_vertical_layout.count())
        if widget.faucet_vertical_layout.itemAt(i).widget() is not None
    )

    # Check if a placeholder frame is created (1 placeholder frame + 2 static widgets)
    assert widget_count == 3  # Expecting 1 placeholder frame + 2 static widgets


def test_setup_ui_connection(mock_faucet_view_model, create_faucets_widget):
    """Test the setup of UI connections."""
    widget = create_faucets_widget

    # Simulate the faucet_list signal emitting
    faucets_list = [
        MagicMock(asset_name='Faucet1', asset_id='1'),
        MagicMock(asset_name='Faucet2', asset_id='2'),
    ]
    mock_faucet_view_model.faucets_view_model.faucet_list.emit(faucets_list)

    # Check if the correct number of widgets are in the layout
    assert widget.faucet_vertical_layout.count() == len(
        faucets_list,
    ) + 2  # Two faucets + static widgets


def test_start_loading_screen(create_faucets_widget):
    """Test the loading screen is displayed correctly."""
    widget = create_faucets_widget

    # Trigger loading screen display
    widget.start_faucets_loading_screen()

    # Check if the loading screen is shown
    assert not widget._loading_translucent_screen.isHidden()  # Checking if it's visible


def test_stop_loading_screen(create_faucets_widget):
    """Test the loading screen is stopped correctly."""
    widget = create_faucets_widget

    # Trigger stop of loading screen
    widget.stop_faucets_loading_screen()

    # Check if the loading screen is hidden
    assert widget._loading_translucent_screen.isHidden()


def test_faucet_request_button_click(create_faucets_widget, mock_faucet_view_model):
    """Test that the faucet request button triggers the correct function."""
    widget = create_faucets_widget
    faucets_list = [
        MagicMock(asset_name='Faucet1', asset_id='1'),
    ]
    widget.create_faucet_frames(faucets_list)

    # Mock the faucet request button click
    faucet_request_button = widget.faucet_request_button
    faucet_request_button.clicked.emit()

    # Check that the correct method is called when the button is clicked
    mock_faucet_view_model.faucets_view_model.request_faucet_asset.assert_called_once()


def test_faucet_request_button_visibility(create_faucets_widget):
    """Test that the faucet request button visibility is correct."""
    widget = create_faucets_widget

    # Simulate a faucet list with available faucets
    faucets_list = [
        MagicMock(asset_name='Faucet1', asset_id='1'),
    ]
    widget.create_faucet_frames(faucets_list)

    # Check if the faucet request button is visible
    assert not widget.faucet_request_button.isHidden()

    # Simulate a scenario where no faucets are available
    widget.create_faucet_frames(None)

    # Check if the request button is not visible
    assert not widget.faucet_request_button.isVisible()


def test_create_faucet_frame_with_no_faucet(create_faucets_widget):
    """Test that the faucet frame is created with no faucet data."""
    widget = create_faucets_widget

    # Create faucet frame with 'None' asset_name to trigger the fallback behavior
    widget.create_faucet_frame(
        asset_name=None, asset_id='NA', is_faucets_available=False,
    )

    # Check if the frame is created correctly (with 'Not yet available' text)
    assert widget.faucet_name_label.text() == 'Not yet available'


def test_retranslate_ui(create_faucets_widget):
    """Test if UI text is translated correctly."""
    widget = create_faucets_widget
    widget.retranslate_ui()

    # Check if the text of get_faucets_title_label is correctly translated
    assert widget.get_faucets_title_label.text() == 'get_faucets'


def test_handle_multiple_faucet_frames(create_faucets_widget):
    """Test if multiple faucet frames can be handled correctly."""
    widget = create_faucets_widget

    # Create a larger list of faucets
    faucets_list = [
        MagicMock(asset_name=f'Faucet{i}', asset_id=str(i)) for i in range(5)
    ]

    widget.create_faucet_frames(faucets_list)

    # Count the number of faucet widgets (ignoring non-widget items like spacers)
    widget_count = sum(
        1 for i in range(widget.faucet_vertical_layout.count())
        if widget.faucet_vertical_layout.itemAt(i).widget() is not None
    )

    # Check if the number of faucet frames corresponds to the number of faucets
    # 5 faucets + 2 static widgets
    assert widget_count == len(faucets_list) + 2


def test_create_faucet_frame_with_style(create_faucets_widget):
    """Test that the faucet frame has the correct styles applied."""
    widget = create_faucets_widget

    # Create a faucet frame with available faucet data
    widget.create_faucet_frame(
        asset_name='Faucet1', asset_id='1', is_faucets_available=True,
    )

    # Check if the faucet frame has the correct stylesheet applied
    assert 'faucet_frame' in widget.faucet_frame.objectName()


def test_loading_screen_during_request(create_faucets_widget):
    """Test that the loading screen appears during a faucet asset request."""
    widget = create_faucets_widget

    # Trigger loading when requesting a faucet asset
    widget.start_faucets_loading_screen()

    # Check if the loading screen is visible
    assert not widget._loading_translucent_screen.isHidden()
