"""Wallet mode summary dialog box module"""
from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout

from src.config.wallet_mode_config import WalletModeConfiguration
from src.data.repository.setting_repository import SettingRepository
from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton


class WalletModeSummaryDialog(QDialog):
    """Dialog box that shows the summary of selected wallet mode configuration"""

    def __init__(self, view_model, parent=None):
        """
        Initializes the WalletModeSummaryDialog with a given view model and parent.

        Args:
            view_model: The view model associated with this dialog.
            parent (QWidget, optional): The parent widget of this dialog. Defaults to None.
        """
        super().__init__(parent)
        self._view_model = view_model
        self.setObjectName('wallet_mode_summary')
        self.setMinimumSize(QSize(500, 550))
        self.setMaximumSize(QSize(500, 700))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)

        self.setStyleSheet(
            load_stylesheet(
                'views/qss/wallet_mode_summary_style.qss',
            ),
        )
        # Main vertical layout
        self.dialog_box_vertical_layout = QVBoxLayout(self)
        self.dialog_box_vertical_layout.setSpacing(10)
        self.dialog_box_vertical_layout.setObjectName(
            'dialog_box_vertical_layout',
        )
        self.dialog_box_vertical_layout.setContentsMargins(18, 10, 18, 16)

        # Mode name
        self.mode_name = QLabel(self)
        self.mode_name.setObjectName('mode_name')
        self.mode_name.setWordWrap(True)
        self.dialog_box_vertical_layout.addWidget(self.mode_name)

        # Capabilities frame
        self.capabilities_frame = QFrame(self)
        self.capabilities_frame.setObjectName('capabilities_frame')
        self.capabilities_frame.setFrameShape(QFrame.StyledPanel)
        self.capabilities_frame.setFrameShadow(QFrame.Raised)
        self.capabilities_frame.setMinimumSize(QSize(470, 150))
        self.capabilities_frame.setMaximumSize(QSize(470, 300))
        self.capabilities_layout = QVBoxLayout(self.capabilities_frame)
        self.capabilities_layout.setSpacing(2)
        self.capabilities_layout.setContentsMargins(10, 10, 10, 10)
        self.capabilities_title = QLabel('Capabilities')
        self.capabilities_title.setObjectName('section_title')
        self.capabilities_layout.addWidget(self.capabilities_title)
        self.capabilities_content_layout = QVBoxLayout()
        self.capabilities_layout.addLayout(self.capabilities_content_layout)
        self.dialog_box_vertical_layout.addWidget(self.capabilities_frame)

        # Limitations frame
        self.limitations_frame = QFrame(self)
        self.limitations_frame.setObjectName('limitations_frame')
        self.limitations_frame.setFrameShape(QFrame.StyledPanel)
        self.limitations_frame.setFrameShadow(QFrame.Raised)
        self.limitations_frame.setMinimumSize(QSize(470, 100))
        self.limitations_frame.setMaximumSize(QSize(470, 300))
        self.limitations_layout = QVBoxLayout(self.limitations_frame)
        self.limitations_layout.setSpacing(2)
        self.limitations_layout.setContentsMargins(10, 10, 10, 10)
        self.limitations_title = QLabel('Limitations')
        self.limitations_title.setObjectName('section_title')
        self.limitations_layout.addWidget(self.limitations_title)
        self.limitations_content_layout = QVBoxLayout()
        self.limitations_layout.addLayout(self.limitations_content_layout)
        self.dialog_box_vertical_layout.addWidget(self.limitations_frame)

        # Recommended frame
        self.recommended_frame = QFrame(self)
        self.recommended_frame.setObjectName('recommended_frame')
        self.recommended_frame.setFrameShape(QFrame.StyledPanel)
        self.recommended_frame.setFrameShadow(QFrame.Raised)
        self.recommended_frame.setMinimumSize(QSize(470, 100))
        self.recommended_frame.setMaximumSize(QSize(470, 300))
        self.recommended_layout = QVBoxLayout(self.recommended_frame)
        self.recommended_layout.setSpacing(2)
        self.recommended_layout.setContentsMargins(10, 10, 10, 10)
        self.recommended_title = QLabel('Recommended For')
        self.recommended_title.setObjectName('section_title')
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
        self.cancel_button.setMinimumSize(QSize(180, 35))
        self.cancel_button.setMaximumSize(QSize(300, 35))
        self.cancel_button.setText('Cancel')
        self.button_layout.addWidget(self.cancel_button)
        self.continue_button = PrimaryButton()
        self.continue_button.setMinimumSize(QSize(180, 35))
        self.continue_button.setMaximumSize(QSize(300, 35))
        self.continue_button.setText('Continue')
        self.button_layout.addWidget(self.continue_button)
        self.dialog_box_vertical_layout.addLayout(self.button_layout)

        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.continue_button.clicked.connect(self.accept)
        self.load_configuration()

    def set_two_column_list(self, layout, items):
        """
        Sets a two-column list layout with the given items.

        This method clears the previous items in the layout and then adds the given items in pairs to a two-column layout.

        Args:
            layout (QVBoxLayout): The layout to which the items will be added.
            items (list): A list of items to be added to the layout.
        """
        # Clear previous items
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
        # Add items in pairs
        for i in range(0, len(items), 2):
            row = QHBoxLayout()
            label1 = QLabel(items[i])
            row.addWidget(label1)
            if i + 1 < len(items):
                label2 = QLabel(items[i+1])
                row.addWidget(label2)
            else:
                row.addWidget(QLabel(''))  # Empty for alignment
            layout.addLayout(row)

    def clear_layout(self, layout):
        """
        Clears all items from a given layout.

        This method recursively clears all items from a layout, including nested layouts.

        Args:
            layout (QLayout): The layout to be cleared.
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

        This method retrieves the current wallet configuration, gets the mode configuration based on the wallet type, security type, entry type, and storage type, and updates the UI with the configuration details.
        """
        # Get current wallet configuration
        wallet_type = SettingRepository.get_wallet_type()
        security_type = SettingRepository.get_wallet_security_type()
        entry_type = SettingRepository.get_wallet_entry_type()
        storage_type = SettingRepository.get_key_storage_type()

        # Get mode configuration
        config = WalletModeConfiguration.get_mode_config(
            wallet_type, security_type, entry_type, storage_type,
        )

        # Update UI with configuration
        self.mode_name.setText(config.mode_name)

        # Update capabilities (use emoji-rich config.capabilities directly)
        self.set_two_column_list(
            self.capabilities_content_layout, config.capabilities,
        )
        self.capabilities_frame.setVisible(bool(config.capabilities))

        # Update limitations
        self.set_two_column_list(
            self.limitations_content_layout, config.limitations,
        )
        self.limitations_frame.setVisible(bool(config.limitations))
        if self.limitations_frame.setVisible(bool(config.limitations)) is None:
            self.setFixedSize(QSize(500, 430))
        # Update recommended uses
        self.set_two_column_list(
            self.recommended_content_layout, config.recommended_for,
        )
        self.recommended_frame.setVisible(bool(config.recommended_for))
