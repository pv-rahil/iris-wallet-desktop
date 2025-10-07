# pylint: disable=too-many-instance-attributes, too-many-statements
"""
Dialog box that shows the summary of selected wallet mode configuration.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import WALLET_MODE_SUMMARY_DIALOG
from accessible_constant import WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON
from accessible_constant import WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON
from src.utils.common_utils import get_current_wallet_mode_config
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class WalletModeSummaryDialog(QDialog):
    """
    Dialog box that shows the summary of selected wallet mode configuration.
    """

    def __init__(self, parent=None):
        """
        Initializes the WalletModeSummaryDialog with a given parent.
        """
        super().__init__(parent)
        self.setObjectName('wallet_mode_summary')
        self.setAccessibleName(WALLET_MODE_SUMMARY_DIALOG)
        self.setMinimumWidth(500)  # Consistent minimum width
        self.setMaximumSize(QSize(600, 700))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/wallet_mode_summary_style.qss',
            ),
        )
        # Main vertical layout
        self.dialog_box_vertical_layout = QVBoxLayout(self)
        self.dialog_box_vertical_layout.setSpacing(
            16,
        )  # Even space between frames
        self.dialog_box_vertical_layout.setObjectName(
            'dialog_box_vertical_layout',
        )
        self.dialog_box_vertical_layout.setContentsMargins(18, 16, 18, 16)

        # Mode name
        self.mode_name = QLabel(self)
        self.mode_name.setObjectName('mode_name')
        self.mode_name.setContentsMargins(-8, 0, 0, 0)
        self.mode_name.setWordWrap(True)
        self.dialog_box_vertical_layout.addWidget(self.mode_name)

        # Capabilities frame
        self.capabilities_frame = QFrame(self)
        self.capabilities_frame.setObjectName('capabilities_frame')
        self.capabilities_frame.setFrameShape(QFrame.StyledPanel)
        self.capabilities_frame.setFrameShadow(QFrame.Raised)
        self.capabilities_frame.setMinimumWidth(550)
        self.capabilities_frame.setMinimumHeight(120)  # Set minimum height
        self.capabilities_layout = QVBoxLayout(self.capabilities_frame)
        self.capabilities_layout.setSpacing(2)
        self.capabilities_layout.setContentsMargins(16, 12, 16, 16)
        self.capabilities_title = QLabel()
        self.capabilities_title.setObjectName('section_title')
        self.capabilities_title.setContentsMargins(
            0, 0, 0, 12,
        )  # Add bottom margin
        self.capabilities_layout.addWidget(self.capabilities_title)
        self.capabilities_content_layout = QVBoxLayout()
        self.capabilities_layout.addLayout(self.capabilities_content_layout)
        self.dialog_box_vertical_layout.addWidget(self.capabilities_frame)

        # Limitations frame
        self.limitations_frame = QFrame(self)
        self.limitations_frame.setObjectName('limitations_frame')
        self.limitations_frame.setFrameShape(QFrame.StyledPanel)
        self.limitations_frame.setFrameShadow(QFrame.Raised)
        self.limitations_frame.setMinimumWidth(550)
        self.limitations_frame.setMinimumHeight(120)  # Set minimum height
        self.limitations_layout = QVBoxLayout(self.limitations_frame)
        self.limitations_layout.setSpacing(2)
        self.limitations_layout.setContentsMargins(16, 12, 16, 16)
        self.limitations_title = QLabel()
        self.limitations_title.setObjectName('section_title')
        self.limitations_title.setContentsMargins(
            0, 0, 0, 12,
        )  # Add bottom margin
        self.limitations_layout.addWidget(self.limitations_title)
        self.limitations_content_layout = QVBoxLayout()
        self.limitations_layout.addLayout(self.limitations_content_layout)
        self.dialog_box_vertical_layout.addWidget(self.limitations_frame)

        # Recommended frame
        self.recommended_frame = QFrame(self)
        self.recommended_frame.setObjectName('recommended_frame')
        self.recommended_frame.setFrameShape(QFrame.StyledPanel)
        self.recommended_frame.setFrameShadow(QFrame.Raised)
        self.recommended_frame.setMinimumWidth(550)
        self.recommended_frame.setMinimumHeight(120)
        self.recommended_layout = QVBoxLayout(self.recommended_frame)
        self.recommended_layout.setSpacing(2)
        self.recommended_layout.setContentsMargins(16, 12, 16, 16)
        self.recommended_title = QLabel()
        self.recommended_title.setObjectName('section_title')
        self.recommended_title.setContentsMargins(0, 0, 0, 12)
        self.recommended_layout.addWidget(self.recommended_title)
        self.recommended_content_layout = QVBoxLayout()
        self.recommended_layout.addLayout(self.recommended_content_layout)
        self.dialog_box_vertical_layout.addWidget(self.recommended_frame)

        # Buttons
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName('button_layout')
        self.button_layout.setContentsMargins(0, 20, 0, 20)
        self.button_layout.setSpacing(10)
        self.cancel_button = SecondaryButton()
        self.cancel_button.setAccessibleName(
            WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON,
        )
        self.cancel_button.setMinimumSize(QSize(180, 35))
        self.cancel_button.setMaximumSize(QSize(300, 35))
        self.button_layout.addWidget(self.cancel_button)
        self.continue_button = PrimaryButton()
        self.continue_button.setAccessibleName(
            WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON,
        )
        self.continue_button.setMinimumSize(QSize(180, 35))
        self.continue_button.setMaximumSize(QSize(300, 35))
        self.button_layout.addWidget(self.continue_button)
        self.dialog_box_vertical_layout.addLayout(self.button_layout)

        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.continue_button.clicked.connect(self.accept)
        self.retranslate_ui()
        self.load_configuration()

    def retranslate_ui(self):
        """
        Set all translatable UI text for the dialog.
        """
        self.capabilities_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'capabilities',
            ),
        )
        self.limitations_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'limitations',
            ),
        )
        self.recommended_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'recommended_for',
            ),
        )
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel',
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
            ),
        )

    def set_two_column_list(self, layout, items):
        """
        Sets a two-column grid layout with the given items.
        Now expects a list of dicts with 'emoji' and 'text' keys.
        """
        # Clear previous items
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
        # Use a grid layout for better alignment
        grid = QGridLayout()
        grid.setVerticalSpacing(8)    # Space between rows
        columns = 2  # two (emoji, text) pairs per row
        for i, item in enumerate(items):
            row = i // columns
            col = (i % columns) * 2
            emoji_label = QLabel(item['emoji'])
            emoji_label.setObjectName('emoji_label')
            emoji_label.setFixedWidth(26)
            emoji_label.setAlignment(Qt.AlignTop | Qt.AlignmentFlag.AlignRight)
            text_label = QLabel(item['text'])
            text_label.setObjectName('text_label')
            text_label.setWordWrap(True)
            text_label.setFixedWidth(200)
            text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            grid.addWidget(emoji_label, row, col)
            grid.addWidget(text_label, row, col + 1)
        layout.addLayout(grid)

    def clear_layout(self, layout):
        """
        Clears all items from a given layout, including nested layouts.
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def load_configuration(self):
        """
        Loads the wallet mode configuration and updates the UI accordingly.
        """
        # Get current wallet configuration
        config = get_current_wallet_mode_config()

        # Update UI with configuration
        self.mode_name.setText(config.mode_name)

        # Update capabilities (use emoji-rich config.capabilities directly)
        self.set_two_column_list(
            self.capabilities_content_layout, config.capabilities,
        )
        self.capabilities_frame.setVisible(bool(config.capabilities))

        # Update limitations
        if not config.limitations:
            # Remove limitations_frame from layout if present
            idx = self.dialog_box_vertical_layout.indexOf(
                self.limitations_frame,
            )
            if idx != -1:
                self.dialog_box_vertical_layout.removeWidget(
                    self.limitations_frame,
                )
                self.limitations_frame.setParent(None)
        else:
            # Add limitations_frame back if not present
            if self.dialog_box_vertical_layout.indexOf(self.limitations_frame) == -1:
                idx = self.dialog_box_vertical_layout.indexOf(
                    self.capabilities_frame,
                )
                self.dialog_box_vertical_layout.insertWidget(
                    idx + 1, self.limitations_frame,
                )
            # Always update the content when showing
            self.set_two_column_list(
                self.limitations_content_layout, config.limitations,
            )
            self.limitations_frame.setVisible(True)

        # Update recommended uses
        self.set_two_column_list(
            self.recommended_content_layout, config.recommended_for,
        )
        self.recommended_frame.setVisible(bool(config.recommended_for))

        self.adjustSize()
