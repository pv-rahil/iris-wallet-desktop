# pylint: disable=too-many-instance-attributes, too-few-public-methods
"""This module contains the WalletInfoWidget classes,
Component for the wallet details.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.common_utils import copy_text
from src.utils.common_utils import translate_value
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class WalletInfoWidget(QWidget):
    """
    A widget that displays a public key with a label and a copy button.

    Attributes:
        value (str): The key value to be displayed.
        translation_key (str): The translated value of element.
        v_layout (QVBoxLayout): Vertical box layout of the page
        parent (QWidget, optional): The parent widget. Defaults to None.
    """

    def __init__(self, value: str, translation_key: str, v_layout: QVBoxLayout, parent=None):
        """
        Initializes the WalletInfoWidget.
        """
        super().__init__(parent)
        self.value = value
        self.translation_key = translation_key
        self.v_layout = v_layout
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the UI components of the widget.
        """
        self.horizontal_layout = QHBoxLayout(self)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # Key label
        self.key_label = QLabel()
        translate_value(self.key_label, self.translation_key)
        self.key_label.setObjectName('key_label')
        self.horizontal_layout.addWidget(self.key_label)

        # Value label
        self.value_label = QLabel()
        self.value_label.setText(str(self.value))
        self.value_label.setObjectName('value_label')
        self.horizontal_layout.addWidget(self.value_label)

        # Copy button
        self.copy_button = QPushButton()
        self.copy_button.setObjectName('node_pub_key_copy_button')
        self.copy_button.setMinimumSize(QSize(16, 16))
        self.copy_button.setMaximumSize(QSize(16, 16))
        self.copy_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Set copy icon
        self.copy_icon = QIcon()
        self.copy_icon.addFile(
            ':assets/copy.png', QSize(), QIcon.Normal, QIcon.Off,
        )
        self.copy_button.setIcon(self.copy_icon)

        # Set tooltip for the copy button
        self.translated_copy_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy', None,
        )
        self.tooltip_text = f"{self.translated_copy_text} {
            self.key_label.text().replace(':', '').lower()
        }"
        self.copy_button.setToolTip(self.tooltip_text)
        self.horizontal_layout.addWidget(self.copy_button)

        # Spacer item to push content to the left
        self.horizontal_spacer = QSpacerItem(
            337, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
        )
        self.horizontal_layout.addItem(self.horizontal_spacer)

        # Connect copy button signal
        self.copy_button.clicked.connect(
            lambda: copy_text(self.value_label),
        )

        self.v_layout.addWidget(self)
