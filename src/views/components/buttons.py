# pylint: disable=unused-import,too-few-public-methods
"""This module contains the buttons classes,
which represents the multiple type of button.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QRect
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Slot
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QMovie
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import QStyleOptionButton

import src.resources_rc
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet


class SecondaryButton(QPushButton):
    """This class represents secondary button of the application."""

    def __init__(self, text=None, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setObjectName('secondary_button')
        self.set_icon(icon_path)  # Set icon if provided
        self.setFixedSize(150, 50)  # Set fixed size
        self.setStyleSheet(load_stylesheet('views/qss/button.qss'))
        self.setIconSize(QSize(24, 24))
        self._movie = None
        self.set_loading_gif()
        self.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )

    def set_icon(self, icon_path):
        """This method used set secondary button icon."""
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(self.size())  # Set icon size to match button size

    @Slot()
    def start_loading(self):
        """This method used to start loading state in secondary button"""
        if self._movie:
            self._movie.start()
            self.setDisabled(True)

    @Slot()
    def stop_loading(self):
        """This method used to stop loading state in secondary button"""
        if self._movie:
            self._movie.stop()
            self.setIcon(QIcon())
            self.setDisabled(False)

    def set_loading_gif(self, filename=':assets/images/button_loading.gif'):
        """This method used to set loading gif for loading state in secondary button"""
        if not self._movie:
            self._movie = QMovie(self)
            self._movie.setFileName(filename)
            self._movie.frameChanged.connect(self.on_frame_changed)
            if self._movie.loopCount() != -1:
                self._movie.finished.connect(self.start_loading)
        self.stop_loading()

    @Slot(int)
    def on_frame_changed(self):
        """This method used to change the movie current pixmap in secondary button"""
        self.setIcon(QIcon(self._movie.currentPixmap()))


class PrimaryButton(QPushButton):
    """This class represents primary button of the application."""

    def __init__(self, text=None, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setObjectName('primary_button')
        self.set_icon(icon_path)  # Set icon if provided
        self.setFixedSize(150, 50)  # Set fixed size
        self.setStyleSheet(load_stylesheet('views/qss/button.qss'))
        self._movie = None
        self.set_loading_gif()
        self.setIconSize(QSize(24, 24))
        self.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )

    def set_icon(self, icon_path):
        """This method used set primary button icon."""
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(self.size())  # Set icon size to match button size

    @Slot()
    def start_loading(self):
        """This method used to start loading state in primary button"""
        if self._movie:
            self._movie.start()
            self.setDisabled(True)

    @Slot()
    def stop_loading(self):
        """This method used to stop loading state in primary button"""
        if self._movie:
            self._movie.stop()
            self.setIcon(QIcon())
            self.setDisabled(False)

    def set_loading_gif(self, filename=':assets/images/button_loading.gif'):
        """This method used to set loading gif for loading state in secondary button"""
        if not self._movie:
            self._movie = QMovie(self)
            self._movie.setFileName(filename)
            self._movie.frameChanged.connect(self.on_frame_changed)
            if self._movie.loopCount() != -1:
                self._movie.finished.connect(self.start_loading)
        self.stop_loading()

    @Slot(int)
    def on_frame_changed(self):
        """This method used to change the movie current pixmap in primary button"""
        self.setIcon(QIcon(self._movie.currentPixmap()))


class SidebarButton(QPushButton):
    """This class represents Sidebar button of the application."""

    def __init__(self, text=None, icon_path=None, parent=None, translation_key=None):
        super().__init__(parent)
        self.translation_key = translation_key
        self.setObjectName(text)
        self.setMinimumSize(QSize(296, 56))
        self.setObjectName('sidebar_button')
        self.setLayoutDirection(Qt.LeftToRight)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setText(QCoreApplication.translate('MainWindow', text, None))
        if icon_path:
            self.set_sidebar_icon(icon_path)  # Set icon if provided
        self.setStyleSheet(load_stylesheet('views/qss/button.qss'))
        self.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                self.translation_key,
                None,
            ),
        )
        self.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.icon_spacing = 8

    def get_translation_key(self):
        """This method retrieve the translation key"""
        return self.translation_key

    def set_sidebar_icon(self, icon_path):
        """This method represents set the icon of the sidebar button"""
        if icon_path:
            icon = QIcon()
            icon.addFile(icon_path, QSize(), QIcon.Normal, QIcon.Off)
            self.setIcon(icon)

    def paintEvent(self, _event):  # pylint:disable=invalid-name
        """This methods handles the paint event for sidebar button and adjusts the icon and text padding, size, and position"""
        painter = QPainter(self)

        option = QStyleOptionButton()
        self.initStyleOption(option)
        self.style().drawPrimitive(QStyle.PE_PanelButtonCommand, option, painter, self)

        icon_rect = QRect(16, (self.height() - 16) // 2, 16, 16)
        text_rect = self.rect().adjusted(36 + self.icon_spacing, 0, 0, 0)

        # Draw icon
        if not self.icon().isNull():
            self.icon().paint(painter, icon_rect)

        # Draw text
        painter.drawText(
            text_rect, Qt.AlignVCenter |
            Qt.AlignLeft, self.text(),
        )
        painter.end()


class AssetTransferButton(QPushButton):
    """This class represents Asset Transfer Button of the application."""

    def __init__(self, text=None, icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName('transfer_button')
        self.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, text, None,
            ),
        )
        self.set_icon(icon_path)  # Set icon if provided
        asset_transfer_button_size_policy = QSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed,
        )
        asset_transfer_button_size_policy.setHorizontalStretch(1)
        asset_transfer_button_size_policy.setVerticalStretch(0)
        asset_transfer_button_size_policy.setHeightForWidth(
            self.sizePolicy().hasHeightForWidth(),
        )
        self.setSizePolicy(asset_transfer_button_size_policy)
        self.setMinimumSize(QSize(157, 45))
        self.setMaximumSize(QSize(157, 45))
        self.setStyleSheet(
            load_stylesheet('views/qss/button.qss'),
        )
        self.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )

    def set_icon(self, icon_path):
        """This method represents set the icon of the Asset Transfer Button"""
        if icon_path:
            icon = QIcon()
            icon.addFile(icon_path, QSize(), QIcon.Normal, QIcon.Off)
            self.setIcon(icon)
