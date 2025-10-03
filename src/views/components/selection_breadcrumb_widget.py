# pylint: disable = invalid-name,too-few-public-methods,too-many-statements
"""
Breadcrumb bar widget for navigation in the application.
Provides a visual breadcrumb trail and hover effects for navigation steps.
"""
from __future__ import annotations

import functools
import re

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QEvent
from PySide6.QtCore import QObject
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QWidget

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class CrumbHoverHelper(QObject):
    """
    A helper class to manage hover events for a breadcrumb.
    Changes the style and icon of a breadcrumb on mouse enter/leave.
    """

    def __init__(self, frame, title_label, logo_label, logo_path, logo_white_path):
        """
        Initialize the hover helper for a breadcrumb.
        Args:
            frame (QWidget): The frame containing the breadcrumb.
            title_label (QLabel): The label displaying the breadcrumb title.
            logo_label (QLabel): The label displaying the breadcrumb logo.
            logo_path (str): The path to the default logo image.
            logo_white_path (str): The path to the white logo image for hover state.
        """
        super().__init__(frame)
        self._title_label = title_label
        self._logo_label = logo_label
        self._logo_path = logo_path
        self._logo_white_path = logo_white_path

    def eventFilter(self, _obj, event):
        """
        Handle hover events for the breadcrumb (Enter/Leave).
        """
        if event.type() == QEvent.Enter:
            self._title_label.setStyleSheet(
                'color: white; font-weight: 700; font-size: 17px; background: transparent; border: none;',
            )
            if self._logo_white_path:
                self._logo_label.setPixmap(
                    QPixmap(self._logo_white_path).scaled(
                        24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                    ),
                )
        elif event.type() == QEvent.Leave:
            self._title_label.setStyleSheet(
                'color: rgb(102, 108, 129); font-weight: 600; font-size: 17px; background: transparent; border: none;',
            )
            if self._logo_path:
                self._logo_label.setPixmap(
                    QPixmap(self._logo_path).scaled(
                        24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                    ),
                )
        return False


class BreadcrumbBar(QWidget):
    """
    Breadcrumb bar widget for navigation in the application.
    Displays a series of clickable breadcrumbs and manages their appearance and events.
    """
    crumb_clicked = Signal(int)

    def __init__(self, parent=None):
        """
        Initialize the BreadcrumbBar widget.
        """
        super().__init__(parent)
        self.crumbs = []
        self._active_index = 0
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(38, 15, 35, 15)
        self.layout.setSpacing(4)

        self.cls_button = QPushButton(self)
        self.cls_button.setObjectName('close_button')
        self.cls_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cls_button.setMinimumSize(QSize(24, 24))
        self.cls_button.setMaximumSize(QSize(50, 65))
        self.cls_button.setIcon(QIcon(':/assets/x_circle.png'))
        self.cls_button.setIconSize(QSize(24, 24))
        self.cls_button.setCheckable(False)

        self.setStyleSheet("""
            QFrame#breadcrumb_frame {
                background: transparent;
                border: none;
            }
            QLabel {
                color: #2c3e50;
                font-size: 14px;
            }
        """)
        self.retranslate_ui()

    def retranslate_ui(self):
        """
        Set all translatable UI text for the widget.
        """
        self.separator_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'breadcrumb_separator',
        )

    @staticmethod
    def get_white_logo_path(logo_path: str) -> str:
        """
        Given a logo path, return the corresponding white logo path if possible.
        """
        if not logo_path:
            return ''
        match = re.match(r'^(.*/)?([^/]+)\.png$', logo_path)
        if match:
            base = match.group(1) or ''
            name = match.group(2)
            return f"{base}white_{name}.png"
        return ''

    def set_breadcrumbs(self, crumbs, active_index=0):
        """
        Set the breadcrumbs for the breadcrumb bar.
        Args:
            crumbs (list): List of breadcrumb dicts with 'logo', 'title', etc.
            active_index (int): The index of the currently active breadcrumb.
        """
        self._active_index = active_index
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.crumbs = []

        for i, crumb in enumerate(crumbs):
            frame = QFrame()
            frame.setObjectName('breadcrumb_frame')
            frame.setFixedHeight(48)
            frame.setCursor(Qt.PointingHandCursor)
            frame.is_pending = crumb.get('pending', False)

            layout = QHBoxLayout(frame)
            layout.setContentsMargins(5, 8, 0, 8)

            content_frame = QFrame()
            content_frame.setObjectName('crumb_content_frame')
            content_frame.setStyleSheet(
                'QFrame { background: transparent; border: none; }',
            )

            content_layout = QHBoxLayout(content_frame)
            content_layout.setContentsMargins(4, 0, 4, 0)
            content_layout.setSpacing(2)

            logo_label = QLabel()
            logo_path = crumb.get('logo', '')
            logo_white_path = crumb.get(
                'logo_white',
            ) or self.get_white_logo_path(logo_path)
            logo_label.setPixmap(
                QPixmap(logo_path).scaled(
                    24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                ),
            )

            logo_container = QFrame()
            logo_container.setFixedSize(26, 26)
            logo_container.setStyleSheet(
                'QFrame { background: transparent; border: none; }',
            )
            logo_layout = QHBoxLayout(logo_container)
            logo_layout.setContentsMargins(0, 0, 0, 0)
            logo_layout.addWidget(logo_label)

            content_layout.addWidget(logo_container)

            title = QLabel(crumb['title'])
            if i == self._active_index:
                title.setStyleSheet(
                    'color: white; font-weight: 700; font-size: 17px; background: transparent; border: none;',
                )
                if logo_white_path:
                    logo_label.setPixmap(
                        QPixmap(logo_white_path).scaled(
                            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                        ),
                    )
            else:
                title.setStyleSheet(
                    'color: rgb(102, 108, 129); font-weight: 600; font-size: 17px; background: transparent; border: none;',
                )

            content_layout.addWidget(title)
            layout.addWidget(content_frame)

            if i != self._active_index:
                hover_helper = CrumbHoverHelper(
                    content_frame, title, logo_label, logo_path, logo_white_path,
                )
                content_frame.installEventFilter(hover_helper)
                # content_frame._hover_helper = hover_helper

            if not frame.is_pending:
                frame.mousePressEvent = functools.partial(
                    lambda self, e, idx: self.crumb_clicked.emit(idx), self, idx=i,
                )
            else:
                frame.mousePressEvent = lambda e: None

            self.layout.addWidget(frame)
            self.crumbs.append(frame)

            if i < len(crumbs) - 1:
                separator = QLabel(self.separator_text)
                separator.setStyleSheet(
                    'QLabel { color: #95a5a6; font-size: 20px; font-weight: bold; }',
                )
                self.layout.addWidget(separator)

        self.layout.addStretch()
        self.layout.addWidget(self.cls_button)
