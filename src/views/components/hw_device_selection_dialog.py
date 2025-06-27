"""
Dialog for selecting and connecting to a hardware wallet device.
"""
from __future__ import annotations

import re

from hwilib.commands import enumerate as hwi_enumerate
from hwilib.common import Chain
from hwilib.devices.ledger import LedgerClient
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QButtonGroup
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QRadioButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.helpers import load_stylesheet
from src.utils.local_store import local_store
from src.views.components.buttons import PrimaryButton
from src.views.components.toast import ToastManager


class HWDeviceSelectionDialog(QDialog):
    """
    Dialog for selecting and connecting to a hardware wallet device.
    """

    def __init__(self, wallet_type, parent=None):
        """
        Initialize the hardware wallet device selection dialog.
        """
        super().__init__(parent)
        self.wallet_type = wallet_type
        self.setObjectName('hardware_wallet_device_dialog')
        self.setWindowTitle(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'select_device', f"Select {
                    self.wallet_type
                } Device",
            ),
        )
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

        self.title = QLabel()
        self.title.setObjectName('hardware_wallet_connect_title')
        layout.addWidget(self.title)

        # Device selection with radio buttons
        self.device_frame = QFrame()
        self.device_frame.setObjectName('hardware_wallet_device_frame')
        device_layout = QVBoxLayout(self.device_frame)
        device_layout.setSpacing(18)
        device_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.button_group = QButtonGroup(self)
        self.radio_buttons = []

        layout.addWidget(self.device_frame)

        # Error label above connect button
        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: red; font: 14px "Inter";')
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        self.connect_button = PrimaryButton()
        self.connect_button.setEnabled(False)
        self.connect_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed,
        )

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.connect_button)
        layout.addLayout(btn_layout)

        self.button_group.buttonClicked.connect(self._on_selection_changed)
        self.connect_button.clicked.connect(self._on_connect)

        # Timer for polling devices every 5 seconds
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll_devices)
        self.poll_timer.start(5000)
        self.poll_devices()  # Initial poll

        self.retranslate_ui()

    def retranslate_ui(self):
        """
        Set all translatable UI text for the dialog.
        """
        self.setWindowTitle(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'select_device', f"Select {
                    self.wallet_type
                } Device",
            ),
        )
        self.title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'available_devices', f"Available {
                    self.wallet_type
                } Devices",
            ),
        )
        self.connect_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'connect',
            ),
        )

    def populate_devices(self, devices, error_message=None):
        """
        Populate the device list with available hardware wallet devices.
        """
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
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'no_devices_found',
                ),
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
        # Show error message if present
        if error_message:
            self.error_label.setText(error_message)
            self.error_label.setVisible(True)
        else:
            self.error_label.clear()
            self.error_label.setVisible(False)

    def _on_selection_changed(self, button):
        """
        Enable connect button when a device is selected.
        """
        self.connect_button.setEnabled(button is not None)

    def _on_connect(self):
        """
        Handle connect button click, re-enumerate devices, and save xpubs/fingerprint.
        """
        selected_device_name = self.get_selected_device()
        if not selected_device_name:
            return
        # Re-enumerate devices to get latest info
        devices = hwi_enumerate()
        # Try to find the selected device by fingerprint in the enumerate result
        matched_device = None
        # Extract fingerprint from selected_device_name
        m = re.search(r'\(([^)]+)\)$', selected_device_name)
        selected_fingerprint = m.group(1) if m else None
        for d in devices:
            if d.get('fingerprint', 'no-fp') == selected_fingerprint:
                matched_device = d
                break
        if matched_device and matched_device.get('error'):
            ToastManager.error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'device_locked',
                ),
            )
            self.connect_button.setDisabled(True)
            return
        # Fetch and save xpubs and fingerprint to ini file
        try:
            master_fingerprint = matched_device.get('fingerprint')
            device_path = matched_device['path']
            password = None
            expert = True
            # Determine chain from app network
            network = SettingRepository.get_wallet_network()
            if network == NetworkEnumModel.MAINNET:
                chain = Chain.MAIN
            elif network == NetworkEnumModel.TESTNET:
                chain = Chain.TEST
            else:
                chain = Chain.REGTEST
            client = LedgerClient(device_path, password, expert, chain)
            account_xpub_vanilla = client.get_pubkey_at_path('m/86h/1h/0h')
            account_xpub_colored = client.get_pubkey_at_path(
                'm/86h/827167h/0h',
            )
            local_store.set_value(ACCOUNT_XPUB_VANILLA, account_xpub_vanilla)
            local_store.set_value(ACCOUNT_XPUB_COLORED, account_xpub_colored)
            local_store.set_value(MASTER_FINGERPRINT, master_fingerprint)
            if client:
                client.close()
        except Exception as e:
            ToastManager.error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'failed_to_fetch_xpubs', f"Failed to fetch xpubs or fingerprint: {
                        e
                    }",
                ),
            )
            return
        self.accept()

    def get_selected_device(self):
        """
        Return the currently selected device name, or None if not selected.
        """
        selected_button = self.button_group.checkedButton()
        if selected_button:
            return selected_button.text()
        return None

    def poll_devices(self):
        """
        Poll HWI enumerate and update device list and error label.
        """
        devices_info = hwi_enumerate()
        error_message = None
        # Try to find any error in the devices
        for d in devices_info:
            if d.get('error'):
                error_message = d.get('error')
                break
        # Map model names for display, include fingerprint for uniqueness
        device_names = [
            f"{self.map_model_name(d.get('model'))} ({
                d.get(
                    'fingerprint', 'no-fp'
                )
            })" for d in devices_info
        ]
        self.populate_devices(device_names, error_message=error_message)

    @staticmethod
    def map_model_name(model):
        """
        Map the model string to a user-friendly model name.
        """
        model = model or ''
        model_lower = model.lower()
        if 'nano_s_plus' in model_lower:
            return 'Ledger Nano S Plus'
        if 'nano_s' in model_lower:
            return 'Ledger Nano S'
        if 'nano_x' in model_lower:
            return 'Ledger Nano X'
        return model.title()
