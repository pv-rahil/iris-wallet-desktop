from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QRadioButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout

from src.utils.helpers import load_stylesheet
from src.views.components.buttons import PrimaryButton


class HWDeviceSelectionDialog(QDialog):
    def __init__(self, wallet_type, devices=None, parent=None):
        super().__init__(parent)
        self.setObjectName('hardware_wallet_device_dialog')
        self.setWindowTitle(f"Select {wallet_type} Device")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/hardware_wallet_connect_style.qss',
            ),
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(28)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel(f"Available {wallet_type} Devices")
        title.setObjectName('hardware_wallet_connect_title')
        layout.addWidget(title)

        # Device selection with radio buttons
        self.device_frame = QFrame()
        self.device_frame.setObjectName('hardware_wallet_device_frame')
        device_layout = QVBoxLayout(self.device_frame)
        device_layout.setSpacing(18)
        device_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.button_group = QButtonGroup(self)
        self.radio_buttons = []

        layout.addWidget(self.device_frame)

        self.refresh_button = PrimaryButton('Refresh')
        self.connect_button = PrimaryButton('Connect')
        self.connect_button.setEnabled(False)
        self.connect_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed,
        )
        self.refresh_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed,
        )

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.refresh_button)
        btn_layout.addWidget(self.connect_button)
        layout.addLayout(btn_layout)

        self.button_group.buttonClicked.connect(self._on_selection_changed)
        self.connect_button.clicked.connect(self.accept)
        self.refresh_button.clicked.connect(self._on_refresh)

        self.devices = devices or []
        self.populate_devices(self.devices)

    def populate_devices(self, devices):
        # Clear existing radio buttons
        for radio in self.radio_buttons:
            self.button_group.removeButton(radio)
            radio.deleteLater()
        self.radio_buttons.clear()

        # Clear the layout
        while self.device_frame.layout().count():
            child = self.device_frame.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not devices:
            no_device_label = QLabel(
                'No devices found. Please connect your device and refresh.',
            )
            no_device_label.setStyleSheet(
                'font: 16px "Inter"; color: rgb(140, 145, 160); padding: 8px 10px;',
            )
            self.device_frame.layout().addWidget(no_device_label)
            self.connect_button.setEnabled(False)
        else:
            for i, device in enumerate(devices):
                radio = QRadioButton(device)
                radio.setObjectName(f'radio_device_{i}')
                radio.setStyleSheet(
                    'font: 16px "Inter"; color: rgb(220, 223, 235); padding: 8px 10px;',
                )
                self.button_group.addButton(radio)
                self.radio_buttons.append(radio)
                self.device_frame.layout().addWidget(radio)

            # Enable connect button if devices are available
            if devices:
                self.connect_button.setEnabled(True)

    def _on_selection_changed(self, button):
        # Enable connect button when a device is selected
        self.connect_button.setEnabled(button is not None)

    def _on_refresh(self):
        # TODO: Implement device refresh logic
        # For now, just repopulate the same list
        self.populate_devices(self.devices)

    def get_selected_device(self):
        selected_button = self.button_group.checkedButton()
        if selected_button:
            return selected_button.text()
        return None
