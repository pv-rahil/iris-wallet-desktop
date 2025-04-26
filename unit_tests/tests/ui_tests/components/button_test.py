"""Unit test for button component."""
# Disable the redefined-outer-name warning as
# it's normal to pass mocked objects in test functions
# pylint: disable=redefined-outer-name,unused-argument,protected-access
from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import QRect
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtGui import QMovie
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPixmap

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.views.components.buttons import AssetTransferButton
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.buttons import SidebarButton


class MockQtSignal(QObject):
    """Mock class for Qt signals that inherits from QObject."""
    signal = Signal()  # Create an actual Qt signal

    def connect(self, callback):
        """Connect the signal to a callback."""
        self.signal.connect(callback)
        return True  # Return True to indicate successful connection

    def emit(self):
        """Emit the signal."""
        self.signal.emit()


@pytest.fixture
def secondary_button(qtbot):
    """Fixture to create and return a SecondaryButton instance."""
    button = SecondaryButton(
        'Test Secondary', ':/assets/icons/regtest-icon.png',
    )
    qtbot.addWidget(button)
    return button


@pytest.fixture
def primary_button(qtbot):
    """Fixture to create and return a PrimaryButton instance."""
    button = PrimaryButton('Test Primary', ':/assets/icons/regtest-icon.png')
    qtbot.addWidget(button)
    return button


@pytest.fixture
def sidebar_button(qtbot):
    """Fixture to create and return a SidebarButton instance."""
    button = SidebarButton(
        text='Test Sidebar', icon_path=':/assets/icons/regtest-icon.png', translation_key='test_key',
    )
    qtbot.addWidget(button)
    return button


@pytest.fixture
def asset_transfer_button(qtbot):
    """Fixture to create and return an AssetTransferButton instance."""
    button = AssetTransferButton(
        'Test Transfer', ':/assets/icons/regtest-icon.png',
    )
    qtbot.addWidget(button)
    return button


### Tests for SecondaryButton ###
def test_secondary_button_initialization(secondary_button):
    """Test initialization of SecondaryButton."""
    assert secondary_button.text() == 'Test Secondary'
    assert secondary_button.objectName() == 'secondary_button'
    assert secondary_button.size() == QSize(150, 50)
    assert secondary_button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_secondary_button_loading_state(secondary_button):
    """Test loading state of SecondaryButton."""
    secondary_button.start_loading()
    assert secondary_button.isEnabled() is False
    assert isinstance(secondary_button._movie, QMovie)
    assert secondary_button._movie.state() == QMovie.Running

    secondary_button.stop_loading()
    assert secondary_button.isEnabled() is True
    assert secondary_button.icon().isNull()


def test_secondary_button_movie_finished_connection(mocker):
    """Test that the movie finished signal is properly connected when loopCount is not -1."""
    # Create a mock movie
    mock_movie = mocker.MagicMock(spec=QMovie)
    mock_movie.loopCount.return_value = 1  # Finite loop count

    # Create mock signals with connect method
    mock_frame_changed = mocker.MagicMock()
    mock_frame_changed.connect = mocker.MagicMock(return_value=True)
    mock_finished = mocker.MagicMock()
    mock_finished.connect = mocker.MagicMock(return_value=True)

    # Set up the mock movie's signals
    type(mock_movie).frameChanged = mocker.PropertyMock(
        return_value=mock_frame_changed,
    )
    type(mock_movie).finished = mocker.PropertyMock(return_value=mock_finished)

    # Patch QMovie before creating the button
    mocker.patch(
        'src.views.components.buttons.QMovie',
        return_value=mock_movie,
    )

    # Create the button (which will use our mocked QMovie)
    button = SecondaryButton(
        'Test Secondary', ':/assets/icons/regtest-icon.png',
    )

    # Verify the signals were connected during initialization
    mock_frame_changed.connect.assert_called_once()
    mock_finished.connect.assert_called_once_with(button.start_loading)


def test_secondary_button_movie_infinite_loop(mocker):
    """Test that the movie finished signal is not connected when loopCount is -1."""
    # Create a mock movie
    mock_movie = mocker.MagicMock(spec=QMovie)
    mock_movie.loopCount.return_value = -1  # Infinite loop

    # Create mock signals with connect method
    mock_frame_changed = mocker.MagicMock()
    mock_frame_changed.connect = mocker.MagicMock(return_value=True)
    mock_finished = mocker.MagicMock()
    mock_finished.connect = mocker.MagicMock(return_value=True)

    # Set up the mock movie's signals
    type(mock_movie).frameChanged = mocker.PropertyMock(
        return_value=mock_frame_changed,
    )
    type(mock_movie).finished = mocker.PropertyMock(return_value=mock_finished)

    # Patch QMovie before creating the button
    mocker.patch(
        'src.views.components.buttons.QMovie',
        return_value=mock_movie,
    )

    # Create the button (which will use our mocked QMovie)
    _button = SecondaryButton(
        'Test Secondary', ':/assets/icons/regtest-icon.png',
    )

    # Verify only frameChanged was connected
    mock_frame_changed.connect.assert_called_once()
    mock_finished.connect.assert_not_called()


### Tests for PrimaryButton ###
def test_primary_button_initialization(primary_button):
    """Test initialization of PrimaryButton."""
    assert primary_button.text() == 'Test Primary'
    assert primary_button.objectName() == 'primary_button'
    assert primary_button.size() == QSize(150, 50)
    assert primary_button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_primary_button_loading_state(primary_button):
    """Test loading state of PrimaryButton."""
    primary_button.start_loading()
    assert primary_button.isEnabled() is False
    assert isinstance(primary_button._movie, QMovie)
    assert primary_button._movie.state() == QMovie.Running

    primary_button.stop_loading()
    assert primary_button.isEnabled() is True
    assert primary_button.icon().isNull()


def test_primary_button_movie_finished_connection(mocker):
    """Test that the movie finished signal is properly connected when loopCount is not -1."""
    # Create a mock movie
    mock_movie = mocker.MagicMock(spec=QMovie)
    mock_movie.loopCount.return_value = 1  # Finite loop count

    # Create mock signals with connect method
    mock_frame_changed = mocker.MagicMock()
    mock_frame_changed.connect = mocker.MagicMock(return_value=True)
    mock_finished = mocker.MagicMock()
    mock_finished.connect = mocker.MagicMock(return_value=True)

    # Set up the mock movie's signals
    type(mock_movie).frameChanged = mocker.PropertyMock(
        return_value=mock_frame_changed,
    )
    type(mock_movie).finished = mocker.PropertyMock(return_value=mock_finished)

    # Patch QMovie before creating the button
    mocker.patch(
        'src.views.components.buttons.QMovie',
        return_value=mock_movie,
    )

    # Create the button (which will use our mocked QMovie)
    button = PrimaryButton('Test Primary', ':/assets/icons/regtest-icon.png')

    # Verify the signals were connected
    mock_frame_changed.connect.assert_called_once()
    mock_finished.connect.assert_called_once_with(button.start_loading)


def test_primary_button_movie_infinite_loop(mocker):
    """Test that the movie finished signal is not connected when loopCount is -1."""
    # Create a mock movie
    mock_movie = mocker.MagicMock(spec=QMovie)
    mock_movie.loopCount.return_value = -1  # Infinite loop

    # Create mock signals with connect method
    mock_frame_changed = mocker.MagicMock()
    mock_frame_changed.connect = mocker.MagicMock(return_value=True)
    mock_finished = mocker.MagicMock()
    mock_finished.connect = mocker.MagicMock(return_value=True)

    # Set up the mock movie's signals
    type(mock_movie).frameChanged = mocker.PropertyMock(
        return_value=mock_frame_changed,
    )
    type(mock_movie).finished = mocker.PropertyMock(return_value=mock_finished)

    # Patch QMovie before creating the button
    mocker.patch(
        'src.views.components.buttons.QMovie',
        return_value=mock_movie,
    )

    # Create the button (which will use our mocked QMovie)
    _button = PrimaryButton('Test Primary', ':/assets/icons/regtest-icon.png')

    # Verify only frameChanged was connected
    mock_frame_changed.connect.assert_called_once()
    mock_finished.connect.assert_not_called()


### Tests for SidebarButton ###
def test_sidebar_button_initialization(sidebar_button):
    """Test initialization of SidebarButton."""
    expected_title = QCoreApplication.translate(
        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'test_key', None,
    )
    assert sidebar_button.text() == expected_title
    assert sidebar_button.objectName() == 'sidebar_button'
    assert sidebar_button.isCheckable() is True
    assert sidebar_button.autoExclusive() is True
    assert sidebar_button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_sidebar_button_translation_key(sidebar_button):
    """Test translation key handling for SidebarButton."""
    assert sidebar_button.get_translation_key() == 'test_key'


### Tests for AssetTransferButton ###
def test_asset_transfer_button_initialization(asset_transfer_button):
    """Test initialization of AssetTransferButton."""
    assert asset_transfer_button.text() == 'Test Transfer'
    assert asset_transfer_button.objectName() == 'transfer_button'
    assert asset_transfer_button.size() == QSize(157, 45)
    assert asset_transfer_button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_sidebar_button_paint_event(qtbot):
    """Test paintEvent for SidebarButton."""
    # Create a SidebarButton instance
    text = 'Test Button'
    icon_path = ':assets/about.png'  # Provide a valid icon path
    button = SidebarButton(
        text=text, icon_path=icon_path,
        translation_key='test_key',
    )
    qtbot.addWidget(button)

    # Render the button to a QPixmap
    pixmap = QPixmap(button.size())
    pixmap.fill(Qt.transparent)  # Clear pixmap to ensure rendering is isolated
    button.render(pixmap)

    # Verify the rendering using QPainter
    painter = QPainter(pixmap)
    painter.setFont(button.font())

    # Measure text bounding box
    metrics = QFontMetrics(button.font())
    expected_text_rect = button.rect().adjusted(36 + button.icon_spacing, 0, 0, 0)
    drawn_text_rect = metrics.boundingRect(
        expected_text_rect, Qt.AlignLeft | Qt.AlignVCenter, button.text(),
    )

    # Ensure the text fits within the expected rect
    assert expected_text_rect.contains(
        drawn_text_rect,
    ), 'Text rendering is outside the expected area'

    # If an icon is set, validate its area
    if not button.icon().isNull():
        icon_rect = QRect(16, (button.height() - 16) // 2, 16, 16)
        assert not pixmap.copy(icon_rect).toImage(
        ).isNull(), 'Icon rendering failed'

    painter.end()
