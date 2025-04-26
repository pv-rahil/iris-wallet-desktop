# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the LoadingTranslucentScreen classes,
which represents the loading screen.
"""
from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtGui import QMovie
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QWidget

import src.resources_rc
from src.model.enums.enums_model import LoaderDisplayModel
from src.utils.custom_exception import CommonException


class LoadingTranslucentScreen(QWidget):
    """
    A loading screen widget that can overlay its parent widget.

    Attributes:
        parent (QWidget): The parent widget.
        description_text (str): The text description to display.
        dot_animation (bool): Whether to enable dot animation.
        loader_type (LoaderDisplayModel): The type of loader.
    """

    def __init__(
        self,
        parent: QWidget,
        description_text: str = 'Waiting',
        dot_animation: bool = True,
        loader_type: LoaderDisplayModel = LoaderDisplayModel.TOP_OF_SCREEN,
    ):
        super().__init__(parent)
        self.loader_type = loader_type
        self.__parent = parent
        self.__dot_animation_flag = dot_animation
        self.__description_lbl_original_text = description_text
        self.__timer = None
        self.__thread = None
        self.__movie_lbl = None
        self.__loading_mv = None
        self.__description_lbl = QLabel()

        self.__setup_parent_event_handling()
        self.__initialize_ui(description_text)

    def __setup_parent_event_handling(self):
        """Setup event handling for the parent widget."""
        self.__parent.installEventFilter(self)
        self.__parent.resizeEvent = self.resizeEvent  # Override resize event

    def __initialize_ui(self, description_text: str):
        """Initialize UI components for the loading screen."""
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.__setup_loader_animation()
        self.__setup_description_label(description_text)
        self.__setup_layout()
        self.setMinimumSize(self.__parent.size())
        self.setVisible(False)
        self.__initialize_timer()

    def __setup_loader_animation(self):
        """Setup the loader animation."""
        self.__movie_lbl = QLabel(self.__parent)
        loader_path = (
            ':assets/images/clockwise_rotating_loader.gif'
            if self.loader_type == LoaderDisplayModel.TOP_OF_SCREEN
            else ':assets/images/button_loading.gif'
        )
        self.__loading_mv = QMovie(loader_path)
        self.__loading_mv.setScaledSize(QSize(45, 45))
        self.__movie_lbl.setMovie(self.__loading_mv)
        self.__movie_lbl.setStyleSheet('QLabel { background: transparent; }')
        self.__movie_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

    def __setup_description_label(self, description_text: str):
        """Setup the description label."""
        if description_text.strip():
            if self.loader_type == LoaderDisplayModel.FULL_SCREEN.value:
                self.__description_lbl.setText(description_text)
            self.__description_lbl.setVisible(False)
            self.__description_lbl.setAlignment(
                Qt.AlignVCenter | Qt.AlignCenter,
            )

    def __setup_layout(self):
        """Setup the layout for the loading screen."""
        layout = QGridLayout()
        if self.loader_type == LoaderDisplayModel.TOP_OF_SCREEN:
            layout.setContentsMargins(0, 18, 0, 0)
            layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        else:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignVCenter | Qt.AlignCenter)

        self.setLayout(layout)
        self.set_description_label_direction('Bottom')

    def __initialize_timer(self):
        """Initialize the timer for dot animation."""
        if self.__dot_animation_flag:
            self.__timer = QTimer(self)
            if self.loader_type == LoaderDisplayModel.FULL_SCREEN.value:
                self.__timer.timeout.connect(self.__update_dot_animation)
                self.__timer.singleShot(0, self.__update_dot_animation)
            self.__timer.start(500)

    def __update_dot_animation(self):
        """Update the dot animation in the description label."""
        if self.loader_type == LoaderDisplayModel.FULL_SCREEN.value:
            cur_text = self.__description_lbl.text()
            dot_count = cur_text.count('.')
            self.__description_lbl.setText(
                self.__description_lbl_original_text +
                '.' * ((dot_count % 3) + 1),
            )

    def set_parent_thread(self, parent_thread: QThread):
        """Set the parent thread for the loading screen."""
        self.__thread = parent_thread

    def set_description_label_direction(self, direction: str):
        """Set the direction of the description label relative to the loader animation."""
        grid_layout = self.layout()
        positions = {
            'Left': [(self.__description_lbl, 0, 0), (self.__movie_lbl, 0, 1)],
            'Top': [(self.__description_lbl, 0, 0), (self.__movie_lbl, 1, 0)],
            'Right': [(self.__movie_lbl, 0, 0), (self.__description_lbl, 0, 1)],
            'Bottom': [(self.__movie_lbl, 0, 0), (self.__description_lbl, 1, 0)],
        }
        if direction not in positions:
            raise CommonException('Invalid direction.')
        for widget, row, col in positions[direction]:
            grid_layout.addWidget(widget, row, col)

    def start(self):
        """Start the loader animation and show the loading screen."""
        self.__loading_mv.start()
        self.__description_lbl.setVisible(True)
        self.raise_()
        self.setVisible(True)

        if self.loader_type == LoaderDisplayModel.FULL_SCREEN.value:
            self.setGraphicsEffect(QGraphicsOpacityEffect(opacity=0.75))

    def stop(self):
        """Stop the loader animation and hide the loading screen."""
        self.__loading_mv.stop()
        self.__description_lbl.setVisible(False)
        self.lower()
        self.setVisible(False)

    def make_parent_disabled_during_loading(self, loading=None):
        """Enable or disable the parent widget during loading."""
        if self.loader_type != LoaderDisplayModel.FULL_SCREEN.value:
            return

        if loading is not None:
            self.__parent.setEnabled(not loading)
        else:
            self.__parent.setEnabled(not self.__thread.isRunning())

    def paintEvent(self, event):  # pylint:disable=invalid-name
        """Draw the translucent background for the loading screen."""
        if self.loader_type == LoaderDisplayModel.FULL_SCREEN.value:
            self.setAutoFillBackground(True)
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(3, 11, 37, 100))
            self.setPalette(palette)
        super().paintEvent(event)

    def eventFilter(self, obj, event):  # pylint:disable=invalid-name
        """Filter events for the parent widget to adjust the loading screen size."""
        if isinstance(obj, QWidget) and event.type() == QEvent.Resize:
            self.setFixedSize(obj.size())
        return super().eventFilter(obj, event)
