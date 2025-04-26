"""Unit test for loading screen component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent
from PySide6.QtCore import QRect
from PySide6.QtCore import QThread
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtGui import QPaintEvent
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QWidget

from src.model.enums.enums_model import LoaderDisplayModel
from src.utils.custom_exception import CommonException
from src.views.components.loading_screen import LoadingTranslucentScreen


@pytest.fixture
def loading_screen_widget(qtbot):
    """Create and return a LoadingTranslucentScreen instance with a parent widget."""
    parent_widget = QWidget()
    loading_screen = LoadingTranslucentScreen(
        parent_widget,
        description_text='Loading...',
        dot_animation=True,
        loader_type=LoaderDisplayModel.TOP_OF_SCREEN,
    )
    qtbot.addWidget(loading_screen)
    return loading_screen, parent_widget


def test_initialize_ui(loading_screen_widget, qtbot):
    """Test initialization of UI components."""
    loading_screen, _parent_widget = loading_screen_widget

    # Mock QMovie and assign it to the loading screen's movie label
    with patch('PySide6.QtGui.QMovie'):
        mock_movie = MagicMock()
        loading_screen._LoadingTranslucentScreen__loading_mv = mock_movie

        # Verify UI components setup correctly
        assert not loading_screen.isVisible()  # Initially hidden
        # Layout should be QGridLayout
        assert isinstance(loading_screen.layout(), QGridLayout)
        # Movie label should be a QLabel
        assert isinstance(
            loading_screen._LoadingTranslucentScreen__movie_lbl, QLabel,
        )
        # Movie should be a MagicMock
        assert isinstance(
            loading_screen._LoadingTranslucentScreen__loading_mv, MagicMock,
        )


def test_start_loading(loading_screen_widget, qtbot):
    """Test start loading animation."""
    loading_screen, _parent_widget = loading_screen_widget

    # Mock the QMovie's start method to prevent actual animation
    mock_movie = MagicMock()
    loading_screen._LoadingTranslucentScreen__loading_mv = mock_movie

    loading_screen.start()
    mock_movie.start.assert_called_once()  # Check that start was called


def test_stop_loading(loading_screen_widget, qtbot):
    """Test stop loading animation."""
    loading_screen, _parent_widget = loading_screen_widget

    # Mock the QMovie's stop method
    mock_movie = MagicMock()
    loading_screen._LoadingTranslucentScreen__loading_mv = mock_movie

    loading_screen.stop()
    mock_movie.stop.assert_called_once()  # Check that stop was called


def test_invalid_description_label_direction(loading_screen_widget, qtbot):
    """Test exception raised for invalid description label direction."""
    loading_screen, _parent_widget = loading_screen_widget

    with pytest.raises(CommonException):
        loading_screen.set_description_label_direction('InvalidDirection')


def test_paint_event_full_screen_loader(loading_screen_widget, qtbot):
    """Test paint event handling for full screen loader."""
    loading_screen, _parent_widget = loading_screen_widget
    loading_screen.loader_type = LoaderDisplayModel.FULL_SCREEN.value

    # Create a QPaintEvent instance for the test
    # Provide a valid QRect for the paint event
    paint_event = QPaintEvent(QRect(0, 0, 100, 100))

    # Call the paintEvent method with the real QPaintEvent
    loading_screen.paintEvent(paint_event)

    # Check if the background color of the widget is set correctly
    palette = loading_screen.palette()
    background_color = palette.color(QPalette.Window)
    expected_color = QColor(3, 11, 37, 100)  # Expected color from the code
    assert background_color == expected_color


def test_event_filter_resize(loading_screen_widget, qtbot):
    """Test event filter handling of resize events."""
    loading_screen, parent_widget = loading_screen_widget

    parent_widget.resize(800, 600)
    loading_screen.eventFilter(parent_widget, QEvent(QEvent.Resize))

    # Check that loading screen resizes to match parent
    assert loading_screen.size() == parent_widget.size()


def test_dot_animation_timer(loading_screen_widget, qtbot):
    """Test initialization and setup of dot animation timer."""
    loading_screen, _parent_widget = loading_screen_widget

    # Set dot_animation_flag to True since timer is only initialized when flag is True
    loading_screen._LoadingTranslucentScreen__dot_animation_flag = True
    loading_screen.loader_type = LoaderDisplayModel.FULL_SCREEN.value

    # Create mock timer before patching QTimer
    mock_timer = MagicMock(spec=QTimer)

    with patch('src.views.components.loading_screen.QTimer', return_value=mock_timer) as mock_timer_class:
        # Call initialize_timer directly since that's what we're testing
        loading_screen._LoadingTranslucentScreen__initialize_timer()

        # Verify QTimer was instantiated with loading_screen as parent
        mock_timer_class.assert_called_once_with(loading_screen)

        # Verify timer connections were made
        mock_timer.timeout.connect.assert_called_once_with(
            loading_screen._LoadingTranslucentScreen__update_dot_animation,
        )
        mock_timer.singleShot.assert_called_once_with(
            0, loading_screen._LoadingTranslucentScreen__update_dot_animation,
        )
        mock_timer.start.assert_called_once_with(500)


def test_update_dot_animation(loading_screen_widget, qtbot):
    """Test dot animation text updates."""
    loading_screen, _parent_widget = loading_screen_widget

    # Set up the loading screen for full screen mode
    loading_screen.loader_type = LoaderDisplayModel.FULL_SCREEN.value

    mock_label = MagicMock()
    loading_screen._LoadingTranslucentScreen__description_lbl = mock_label
    loading_screen._LoadingTranslucentScreen__description_lbl_original_text = 'Loading'

    # Test progression of dots
    test_cases = [
        ('Loading', 'Loading.'),
        ('Loading.', 'Loading..'),
        ('Loading..', 'Loading...'),
        ('Loading...', 'Loading.'),
    ]

    for input_text, expected_text in test_cases:
        mock_label.text.return_value = input_text
        loading_screen._LoadingTranslucentScreen__update_dot_animation()
        mock_label.setText.assert_called_with(expected_text)
        mock_label.reset_mock()

    # Test when not in full screen mode
    loading_screen.loader_type = 'OTHER'
    mock_label.reset_mock()
    loading_screen._LoadingTranslucentScreen__update_dot_animation()
    mock_label.setText.assert_not_called()


def test_set_parent_thread(loading_screen_widget, qtbot):
    """Test setting parent thread."""
    loading_screen, _parent_widget = loading_screen_widget
    mock_thread = MagicMock(spec=QThread)

    # Set the parent thread
    loading_screen.set_parent_thread(mock_thread)

    # Verify that the thread was correctly set
    assert loading_screen._LoadingTranslucentScreen__thread == mock_thread


def test_make_parent_disabled_during_loading_non_full_screen(loading_screen_widget, qtbot):
    """Test parent widget remains enabled for non-full screen loader."""
    loading_screen, parent_widget = loading_screen_widget
    parent_widget.setEnabled = MagicMock()

    # Set a non-full screen loader type
    loading_screen.loader_type = 'SOME_OTHER_TYPE'

    # Call the method with loading=True
    loading_screen.make_parent_disabled_during_loading(loading=True)

    # Assert that setEnabled was not called since the loader type is not FULL_SCREEN
    # Parent should not be disabled for other loader types
    parent_widget.setEnabled.assert_not_called()


def test_make_parent_disabled_during_loading_full_screen(loading_screen_widget, qtbot):
    """Test parent widget is disabled for full screen loader."""
    loading_screen, parent_widget = loading_screen_widget
    # Mock setEnabled method of the parent widget
    parent_widget.setEnabled = MagicMock()

    # Mock the __thread attribute and its isRunning() method
    mock_thread = MagicMock()
    mock_thread.isRunning.return_value = True  # Set the thread to be "running"
    # Set the thread to the mock thread
    loading_screen._LoadingTranslucentScreen__thread = mock_thread

    # Set loader_type to FULL_SCREEN
    loading_screen.loader_type = LoaderDisplayModel.FULL_SCREEN

    # Call the method with loading=True
    loading_screen.make_parent_disabled_during_loading(loading=True)

    # Assert that setEnabled is called with False to disable the parent
    parent_widget.setEnabled.assert_called_once_with(
        False,
    )  # Parent should be disabled
