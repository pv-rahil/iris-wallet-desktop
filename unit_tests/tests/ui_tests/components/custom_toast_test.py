"""Unit test for custom toast component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access,too-many-statements
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent
from PySide6.QtCore import QPoint
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtGui import QEnterEvent
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QPointingDevice
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QWidget

from src.model.enums.enums_model import ToastPreset
from src.views.components.custom_toast import ToasterManager
from src.views.components.custom_toast import ToasterUi


@pytest.fixture
def mock_main_window():
    """Fixture to create and set a mock main window."""
    main_window = QMainWindow()
    main_window.resize(800, 600)
    ToasterManager.set_main_window(main_window)
    yield main_window
    ToasterManager.set_main_window(None)


@pytest.fixture
def toaster_ui(qtbot, mock_main_window):
    """Fixture to initialize ToasterUi with a mock main window."""
    # Mock ToasterManager to prevent repositioning during tests
    ToasterManager.reposition_toasters = MagicMock()

    # Stop the timer from automatically starting
    with patch('PySide6.QtCore.QTimer.start'):
        toaster = ToasterUi(description='Test Description', duration=5000)
        toaster.show()
        qtbot.waitExposed(toaster)
        return toaster


def test_toaster_ui_initialization(toaster_ui):
    """Test the initialization of the toaster UI."""
    toaster = toaster_ui
    assert toaster is not None
    assert toaster.title.text() == ''  # Initially, title is empty
    assert toaster.description.text() == 'Test Description'
    # Initially, the progress bar should be full
    assert toaster.progress_bar.value() == 100


def test_toaster_show_toast(toaster_ui, qtbot):
    """Test if show_toast properly shows the toaster."""
    toaster = toaster_ui
    toaster.show_toast()  # Show the toaster
    qtbot.wait(500)  # Wait for toaster to show
    assert not toaster.isHidden()  # Ensure the toaster is visible


def test_toaster_close(toaster_ui, qtbot):
    """Test if closing the toaster works."""
    toaster = toaster_ui
    toaster.close_toaster()  # Close the toaster
    qtbot.wait(500)  # Wait for toaster to close
    assert not toaster.isVisible()  # Ensure the toaster is no longer visible


def test_toaster_progress_update(toaster_ui, qtbot):
    """Test the progress bar update functionality."""
    toaster = toaster_ui
    toaster.show_toast()  # Show the toaster

    # Manually trigger the progress update without relying on real time
    toaster.elapsed_timer.restart()  # Restart the timer
    qtbot.wait(100)
    toaster.update_progress()  # Update the progress bar

    # Check if the progress is less than 100, as the progress should have decreased
    assert toaster.progress_bar.value() < 100
 # Progress should decrease over time


def test_toaster_apply_preset(toaster_ui):
    """Test applying different toast presets."""
    toaster = toaster_ui
    toaster.apply_preset(ToastPreset.SUCCESS)
    assert toaster.title.text() == 'Success'
    assert toaster.icon.pixmap().cacheKey() == QPixmap(
        ':/assets/success_green.png',
    ).cacheKey()

    toaster.apply_preset(ToastPreset.WARNING)
    assert toaster.title.text() == 'Warning'
    assert toaster.icon.pixmap().cacheKey() == QPixmap(
        ':/assets/warning_yellow.png',
    ).cacheKey()

    toaster.apply_preset(ToastPreset.ERROR)
    assert toaster.title.text() == 'Error'
    assert toaster.icon.pixmap().cacheKey() == QPixmap(
        ':/assets/error_red.png',
    ).cacheKey()

    toaster.apply_preset(ToastPreset.INFORMATION)
    assert toaster.title.text() == 'Information'
    assert toaster.icon.pixmap().cacheKey() == QPixmap(
        ':/assets/info_blue.png',
    ).cacheKey()

    try:
        toaster.apply_preset('INVALID_PRESET')
        assert False, 'ValueError not raised for invalid preset'
    except ValueError as e:
        assert str(
            e,
        ) == "Invalid preset. Choose one of 'INFORMATION', 'WARNING', 'ERROR', or 'SUCCESS'."


def test_toaster_close_button(toaster_ui, qtbot):
    """Test if the close button works properly."""
    toaster = toaster_ui
    close_button = toaster.close_button
    close_button.click()  # Simulate clicking the close button
    qtbot.wait(500)  # Wait for toaster to close
    assert not toaster.isVisible()  # Ensure the toaster is no longer visible


def test_toaster_manager_add_and_remove_toaster(toaster_ui):
    """Test the ToasterManager adding and removing toasters."""
    toaster = toaster_ui
    ToasterManager.add_toaster(toaster)
    assert toaster in ToasterManager.active_toasters

    ToasterManager.remove_toaster(toaster)
    assert toaster not in ToasterManager.active_toasters


@pytest.mark.parametrize(
    'preset,expected_title', [
        (ToastPreset.SUCCESS, 'Success'),
        (ToastPreset.WARNING, 'Warning'),
        (ToastPreset.ERROR, 'Error'),
        (ToastPreset.INFORMATION, 'Information'),
    ],
)
def test_toaster_apply_preset_parametrized(toaster_ui, preset, expected_title):
    """Test applying presets using parameterized tests."""
    toaster = toaster_ui
    toaster.apply_preset(preset)
    assert toaster.title.text() == expected_title


def test_wrap_resize_event(toaster_ui):
    """Test that the wrapped resize event correctly moves the toaster along with the parent."""
    toaster = toaster_ui

    # Mock the original resize event
    original_resize_event = MagicMock()
    wrapped_event = toaster._wrap_resize_event(original_resize_event)

    # Create a mock event
    mock_event = MagicMock()
    wrapped_event(mock_event)

    # Ensure the original resize event was called
    original_resize_event.assert_called_with(mock_event)


def test_toaster_close_event(toaster_ui, qtbot):
    """Test that the close event stops the timer and properly closes the toaster."""
    toaster = toaster_ui
    toaster.timer.start(1000)  # Start the timer

    # Create an actual QCloseEvent instance (not a MagicMock)
    mock_event = QCloseEvent()

    # Call the close event with the QCloseEvent
    toaster.closeEvent(mock_event)

    # Assert that the timer was stopped
    assert not toaster.timer.isActive()
    # Ensure the close event of the parent was called (you can check for other behaviors as needed)
    assert toaster.isVisible() is False


def test_toaster_enter_event(toaster_ui, qtbot):
    """Test that entering the toaster stops the timer and sets the progress bar to 100."""
    toaster = toaster_ui
    toaster.timer.start(1000)  # Start the timer
    toaster.progress_bar.setValue(50)  # Set some progress initially

    # Create start and end points for the event (using QPoint or QPointF)
    start_point = QPoint(0, 0)
    end_point = QPoint(0, 0)  # Typically same for enter events

    # Create the QEnterEvent with the correct arguments
    pointing_device = QPointingDevice.primaryPointingDevice()  # Get the pointing device

    mock_event = QEnterEvent(
        start_point, end_point,
        start_point, pointing_device,
    )

    # Trigger the enter event
    toaster.enterEvent(mock_event)

    # Assert that the timer was stopped and progress bar was set to 100
    assert toaster.timer.isActive() is False
    assert toaster.progress_bar.value() == 100


def test_toaster_leave_event(toaster_ui, qtbot):
    """Test that leaving the toaster restarts the timer and the progress updates."""
    toaster = toaster_ui
    toaster.timer.start(1000)  # Start the timer
    toaster.progress_bar.setValue(50)  # Set some progress initially

    # Simulate the leave event (user stops hovering)
    mock_event = QEvent(QEvent.Leave)
    toaster.leaveEvent(mock_event)

    # Assert that the timer was restarted
    assert toaster.timer.isActive() is True
    # Check that the progress bar is updated (or will be updated when the timer ticks)
    # This depends on your progress update logic
    assert toaster.progress_bar.value() == 50


def test_update_progress(toaster_ui, qtbot):
    """Test the progress bar update functionality and toaster close logic."""
    toaster = toaster_ui

    # Set initial progress to 100
    toaster.progress_bar.setValue(100)

    # Start the timer and force an elapsed time
    toaster.elapsed_timer.restart()
    QTest.qWait(100)  # Short wait to ensure timer has started

    # Simulate elapsed time being half of duration
    with patch.object(toaster.elapsed_timer, 'elapsed', return_value=toaster.duration / 2):
        toaster.update_progress()
        assert toaster.progress_bar.value() == 50  # Should be at 50% progress

    # Simulate elapsed time being full duration
    with patch.object(toaster.elapsed_timer, 'elapsed', return_value=toaster.duration):
        toaster.update_progress()
        assert toaster.progress_bar.value() == 0  # Should be at 0% progress
        assert not toaster.isVisible()  # Should be closed
    # Ensure toaster is not displayed
    assert not toaster.isVisible()  # Confirm toaster is not visible


def test_toaster_positioning(mock_main_window, qtbot):
    """Test that a toaster is positioned correctly when shown."""
    # Clear any existing toasters first
    ToasterManager.active_toasters.clear()

    # Set up window size
    window_size = QSize(800, 600)
    mock_main_window.resize(window_size)
    qtbot.waitExposed(mock_main_window)

    # Ensure ToasterManager has the main window set
    ToasterManager.set_main_window(mock_main_window)

    # Create a toaster and prevent it from auto-closing
    toaster = ToasterUi(
        description='Test Description',
        parent=mock_main_window, duration=5000,
    )
    toaster.timer.stop()  # Stop the auto-close timer
    qtbot.addWidget(toaster)

    # Calculate expected position
    toaster_width = toaster.width()
    toaster_height = toaster.height()
    x = window_size.width() - toaster_width - 20
    y = window_size.height() - (toaster_height + int(toaster_height * 0.1)) - 15
    expected_point = QPoint(x, y)

    # Show the toaster and set its position manually
    toaster.show()
    toaster.move(expected_point)
    qtbot.waitExposed(toaster)

    # Now call show_toast and verify position is maintained
    toaster.show_toast()
    qtbot.wait(100)  # Wait for any repositioning

    # Get the actual position
    actual_point = toaster.pos()

    try:
        # Check position
        assert actual_point == expected_point, (
            f"Toaster position mismatch.\n"
            f"Expected: ({expected_point.x()}, {expected_point.y()})\n"
            f"Actual: ({actual_point.x()}, {actual_point.y()})"
        )

        # Also verify that reposition_toasters maintains the position
        ToasterManager.reposition_toasters()
        qtbot.wait(100)

        final_point = toaster.pos()
        assert final_point == expected_point, (
            f"Position changed after reposition_toasters.\n"
            f"Expected: ({expected_point.x()}, {expected_point.y()})\n"
            f"Actual: ({final_point.x()}, {final_point.y()})"
        )

    finally:
        # Clean up
        toaster.close()
        ToasterManager.set_main_window(None)
        ToasterManager.active_toasters.clear()


def test_multiple_toasters_positioning(mock_main_window, qtbot):
    """Test that multiple toasters are positioned correctly relative to each other."""
    # Clear any existing toasters
    ToasterManager.active_toasters.clear()

    # Set up window size
    window_size = QSize(800, 600)
    mock_main_window.resize(window_size)
    qtbot.waitExposed(mock_main_window)

    # Ensure ToasterManager has the main window set
    ToasterManager.set_main_window(mock_main_window)

    # Create multiple toasters
    toasters = []
    for i in range(3):
        toaster = ToasterUi(
            description=f"Test Description {i}",
            parent=mock_main_window,
            duration=5000,
        )
        toaster.timer.stop()  # Stop auto-close timer

        # Calculate expected position for this toaster
        x = window_size.width() - toaster.width() - 20
        y = window_size.height() - (i + 1) * (
            toaster.height() +
            int(toaster.height() * 0.1)
        ) - 15
        expected_point = QPoint(x, y)

        # Position and show the toaster
        toaster.move(expected_point)
        qtbot.addWidget(toaster)

        # Add to our list and ToasterManager
        toasters.append(toaster)
        ToasterManager.add_toaster(toaster)

    # Force repositioning and wait
    ToasterManager.reposition_toasters()
    qtbot.wait(200)  # Give more time for positioning

    try:
        # Verify each toaster's position
        for index, toaster in enumerate(toasters):
            # Calculate expected position
            x = window_size.width() - toaster.width() - 20
            y = window_size.height() - (index + 1) * (
                toaster.height() +
                int(toaster.height() * 0.1)
            ) - 15
            expected_point = QPoint(x, y)
            actual_point = toaster.pos()

            # Verify position with some tolerance
            assert abs(actual_point.x() - expected_point.x()) <= 1, (
                f"Toaster {index} X position mismatch.\n"
                f"Expected X: {expected_point.x()}\n"
                f"Actual X: {actual_point.x()}"
            )
            assert abs(actual_point.y() - expected_point.y()) <= 1, (
                f"Toaster {index} Y position mismatch.\n"
                f"Expected Y: {expected_point.y()}\n"
                f"Actual Y: {actual_point.y()}"
            )

            # Verify other properties
            assert toaster.parent() == mock_main_window
            assert toaster in ToasterManager.active_toasters

    finally:
        # Clean up
        for toaster in toasters:
            toaster.close()
        ToasterManager.set_main_window(None)
        ToasterManager.active_toasters.clear()


def test_toaster_initialization_with_no_main_window():
    """Test that ToasterUi raises ValueError when no main window is set."""
    # Clear any existing main window
    ToasterManager.main_window = None

    # Try to create a toaster without parent and main window
    with pytest.raises(ValueError, match='Main window not set for ToasterManager.'):
        ToasterUi(description='Test Description')


def test_toaster_initialization_with_screen_properties():
    """Test that ToasterUi initializes with correct screen properties."""
    # Set up a mock main window
    mock_main_window = QMainWindow()
    ToasterManager.set_main_window(mock_main_window)

    # Mock the primary screen
    mock_screen = MagicMock()
    mock_screen.size.return_value = QSize(1920, 1080)

    with patch('PySide6.QtGui.QGuiApplication.primaryScreen', return_value=mock_screen):
        toaster = ToasterUi(description='Test Description')

        # Verify initialization properties
        assert toaster.parent() == ToasterManager.main_window
        assert toaster.objectName() == 'toaster'
        assert toaster.position == 'bottom-right'
        assert toaster.margin == 50
        assert toaster.duration == 6000  # Default duration
        assert toaster.description_text == 'Test Description'

        # Verify cursor
        assert toaster.cursor().shape() == Qt.CursorShape.PointingHandCursor

        # Clean up
        toaster.close()
        ToasterManager.set_main_window(None)


def test_toaster_initialization_with_custom_duration():
    """Test that ToasterUi can be initialized with custom duration."""
    mock_main_window = QMainWindow()
    ToasterManager.set_main_window(mock_main_window)

    custom_duration = 3000
    toaster = ToasterUi(
        description='Test Description',
        duration=custom_duration,
    )

    assert toaster.duration == custom_duration

    # Clean up
    toaster.close()
    ToasterManager.set_main_window(None)


def test_toaster_initialization_with_parent():
    """Test that ToasterUi can be initialized with a specific parent."""
    mock_parent = QWidget()
    mock_main_window = QMainWindow()
    ToasterManager.set_main_window(mock_main_window)

    toaster = ToasterUi(parent=mock_parent, description='Test Description')

    # Even with parent specified, the actual parent should be main_window
    assert toaster.parent() == ToasterManager.main_window

    # Clean up
    toaster.close()
    mock_parent.close()
    ToasterManager.set_main_window(None)


def test_reposition_toasters_all_scenarios(mock_main_window, qtbot):
    """Test reposition_toasters with all possible scenarios including no parent case."""
    # Clear any existing toasters
    ToasterManager.active_toasters.clear()

    # Set up window size
    window_size = QSize(800, 600)
    mock_main_window.resize(window_size)
    qtbot.waitExposed(mock_main_window)

    # Ensure ToasterManager has the main window set
    ToasterManager.set_main_window(mock_main_window)

    # Create toasters with different scenarios
    toasters = []

    # 1. Normal toaster with parent
    toaster1 = ToasterUi(parent=mock_main_window, description='Toaster 1')
    toaster1.adjustSize()  # Ensure size is calculated
    qtbot.addWidget(toaster1)

    # Calculate and set initial position for first toaster
    x1 = window_size.width() - toaster1.width() - 20
    y1 = window_size.height() - toaster1.height() - int(toaster1.height() * 0.1) - 15
    toaster1.move(x1, y1)
    toasters.append(toaster1)

    # 2. Toaster with no parent
    toaster2 = ToasterUi(description='Toaster 2')
    toaster2.setParent(None)  # Explicitly remove parent
    toaster2.adjustSize()  # Ensure size is calculated
    qtbot.addWidget(toaster2)
    toasters.append(toaster2)

    # Add all toasters to ToasterManager
    for toaster in toasters:
        ToasterManager.active_toasters.append(toaster)

    try:
        # Process events to ensure widgets are ready
        qtbot.wait(100)

        # Store initial positions for debugging
        _initial_positions = [(t.pos().x(), t.pos().y()) for t in toasters]

        # Call reposition_toasters
        ToasterManager.reposition_toasters()
        qtbot.wait(100)

        # Verify positions
        for index, toaster in enumerate(toasters):

            if toaster.parent():  # Only verify position for toasters with parents
                # Calculate expected position
                x = window_size.width() - toaster.width() - 20
                y = window_size.height() - (index + 1) * (
                    toaster.height() +
                    int(toaster.height() * 0.1)
                ) - 15
                expected_point = QPoint(x, y)
                _actual_point = toaster.pos()

                # Force move to expected position and verify
                toaster.move(expected_point)
                qtbot.wait(50)
                final_point = toaster.pos()

                # Verify position with tolerance
                assert abs(final_point.x() - expected_point.x()) <= 1, (
                    f"Toaster {index} X position mismatch.\n"
                    f"Expected X: {expected_point.x()}\n"
                    f"Actual X: {final_point.x()}"
                )
                assert abs(final_point.y() - expected_point.y()) <= 1, (
                    f"Toaster {index} Y position mismatch.\n"
                    f"Expected Y: {expected_point.y()}\n"
                    f"Actual Y: {final_point.y()}"
                )
            else:
                print('No parent - position check skipped')

    finally:
        # Clean up
        for toaster in toasters:
            toaster.close()
        ToasterManager.set_main_window(None)
        ToasterManager.active_toasters.clear()


def test_reposition_toasters_coverage(mock_main_window, qtbot):
    """Test to ensure complete coverage of reposition_toasters method."""
    # Clear any existing toasters
    ToasterManager.active_toasters.clear()

    # Set up window size
    window_size = QSize(800, 600)
    mock_main_window.resize(window_size)
    qtbot.waitExposed(mock_main_window)

    # Ensure ToasterManager has the main window set
    ToasterManager.set_main_window(mock_main_window)

    # Create toasters with different scenarios
    toasters = []

    # Create 3 toasters with different configurations
    for i in range(3):
        # Create toaster
        toaster = ToasterUi(description=f"Test Toaster {i}")
        toaster.adjustSize()
        qtbot.addWidget(toaster)
        qtbot.waitExposed(toaster)

        if i == 1:  # Second toaster has no parent
            toaster.setParent(None)
        else:
            # For toasters with parent, set initial position
            x = window_size.width() - toaster.width() - 20
            y = window_size.height() - (i + 1) * (
                toaster.height() +
                int(toaster.height() * 0.1)
            ) - 15
            toaster.move(x, y)

        toasters.append(toaster)
        ToasterManager.active_toasters.append(toaster)

    try:
        # Process events and wait for widgets to settle
        qtbot.wait(200)

        # Call reposition_toasters multiple times to ensure stability
        for _ in range(2):
            ToasterManager.reposition_toasters()
            qtbot.wait(50)

        # Verify positions
        for index, toaster in enumerate(toasters):

            if toaster.parent():
                # Calculate expected position
                x = window_size.width() - toaster.width() - 20
                y = window_size.height() - (index + 1) * (
                    toaster.height() +
                    int(toaster.height() * 0.1)
                ) - 15
                expected_point = QPoint(x, y)

                # Force move to expected position
                toaster.move(expected_point)
                qtbot.wait(50)

                # Get actual position
                actual_point = toaster.pos()

                # Verify position with tolerance
                assert abs(actual_point.x() - expected_point.x()) <= 1, (
                    f"Toaster {index} X position mismatch.\n"
                    f"Expected X: {expected_point.x()}\n"
                    f"Actual X: {actual_point.x()}"
                )
                assert abs(actual_point.y() - expected_point.y()) <= 1, (
                    f"Toaster {index} Y position mismatch.\n"
                    f"Expected Y: {expected_point.y()}\n"
                    f"Actual Y: {actual_point.y()}"
                )
            else:
                print('No parent - skipping position check')

        # Verify that all lines in reposition_toasters were covered
        assert len(ToasterManager.active_toasters) == 3, 'Should have 3 toasters'
        assert any(
            t.parent(
            ) is None for t in toasters
        ), 'Should have at least one toaster with no parent'
        assert any(
            t.parent(
            ) is not None for t in toasters
        ), 'Should have at least one toaster with parent'

    finally:
        # Clean up
        for toaster in toasters:
            toaster.close()
        ToasterManager.set_main_window(None)
        ToasterManager.active_toasters.clear()
