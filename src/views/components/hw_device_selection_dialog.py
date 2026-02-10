# pylint: disable=too-many-instance-attributes,invalid-name,too-many-statements
"""
Dialog for selecting and connecting to a hardware wallet device.
Provides UI for device selection, error handling, and connection logic.
"""
from __future__ import annotations

from hwilib.commands import enumerate as hwi_enumerate
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QMovie
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QButtonGroup
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QRadioButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import HW_DEVICE_SELECTION_DIALOG
from accessible_constant import HW_DEVICE_SELECTION_DIALOG_CANCEL_BUTTON
from accessible_constant import HW_DEVICE_SELECTION_DIALOG_CONNECT_BUTTON
from src.data.repository.setting_repository import SettingRepository
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.viewmodels.hw_device_selection_view_model import HWDeviceSelectionViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.toast import ToastManager


class HWDeviceSelectionDialog(QDialog):
    """
    Dialog for selecting and connecting to a hardware wallet device.
    Handles device enumeration, user selection, error display, and connection logic.
    """

    def __init__(self, wallet_type, parent=None):
        """
        Initialize the hardware wallet device selection dialog.

        Args:
            wallet_type: The type of wallet (e.g., Ledger, Trezor).
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.wallet_type = wallet_type
        self._loader_label = None
        self._loader_movie = None
        self._loader_text = None
        self._device_selection_view_model = HWDeviceSelectionViewModel()
        self.setObjectName('hardware_wallet_device_dialog')
        self.setAccessibleName(HW_DEVICE_SELECTION_DIALOG)
        self.setMinimumWidth(450)
        self.setMaximumHeight(400)
        self.setModal(True)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint,
        )
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/hardware_wallet_connect_style.qss',
            ),
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 32, 0, 32)

        self.title = QLabel()
        self.title.setObjectName('hardware_wallet_connect_title')
        self.title.setMaximumHeight(50)
        layout.addWidget(self.title)

        # Device selection with radio buttons
        self.device_frame = QFrame()
        self.device_frame.setObjectName('hardware_wallet_device_frame')
        device_layout = QVBoxLayout(self.device_frame)
        device_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        device_layout.setContentsMargins(0, 0, 0, 0)

        self.button_group = QButtonGroup(self)
        self.radio_buttons = []

        layout.addWidget(self.device_frame)

        # Error label above connect button
        self.error_label = QLabel()
        self.error_label.setObjectName('error_label')
        self.error_label.setWordWrap(True)
        self.error_label.setMaximumWidth(400)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        self.connect_button = PrimaryButton()
        self.connect_button.setAccessibleName(
            HW_DEVICE_SELECTION_DIALOG_CONNECT_BUTTON,
        )
        self.connect_button.setEnabled(False)
        self.connect_button.setFixedSize(150, 50)
        self.connect_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )

        self.cancel_button = SecondaryButton()
        self.cancel_button.setAccessibleName(
            HW_DEVICE_SELECTION_DIALOG_CANCEL_BUTTON,
        )
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel',
            ),
        )
        self.cancel_button.setFixedSize(180, 50)
        self.cancel_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred,
        )
        self.cancel_button.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.connect_button)
        layout.addLayout(btn_layout)

        self.button_group.buttonClicked.connect(
            self._update_connect_button_state,
        )
        self.connect_button.clicked.connect(self._on_connect)

        # Timer for polling devices every 5 seconds
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.checking_devices)
        self.poll_timer.start(5000)
        self.checking_devices()  # Initial poll

        self.retranslate_ui()
        self._device_selection_view_model.connect_succeeded.connect(
            self.accept,
        )
        self._device_selection_view_model.connect_failed.connect(
            self.set_error,
        )

    def retranslate_ui(self):
        """
        Set all translatable UI text for the dialog.
        """
        self.setWindowTitle(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'select_device',
            ).format(self.wallet_type),
        )
        self.title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'available_devices',
            ).format(self.wallet_type),
        )
        self.connect_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'connect',
            ),
        )

    def _update_connect_button_state(self):
        """
        Enable connect button only if a radio button is selected and there is no error.
        """
        error_present = self.error_label.isVisible(
        ) and self.error_label.text().strip() != ''
        selected = self.button_group.checkedButton() is not None
        self.connect_button.setEnabled(selected and not error_present)

    def populate_devices(self, devices, error_message=None):
        """
        Populate the device list with available hardware wallet devices.

        Args:
            devices: List of device info dicts.
            error_message: Optional error message to display.
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
            no_device_label.setObjectName('no_device_label')
            no_device_label.setWordWrap(True)
            self.device_frame.layout().addWidget(no_device_label)
        else:
            for i, device in enumerate(devices):
                # device is expected to be a dict with model and fingerprint
                model_name = self.map_model_name(device.get('model'))
                fingerprint = device.get('fingerprint', 'no-fp')
                radio = QRadioButton(model_name)
                radio.setObjectName(f'radio_device_{i}')
                radio.setProperty('fingerprint', fingerprint)
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_widget = QFrame()
                row_widget.setLayout(row_layout)
                row_widget.setMaximumHeight(32)
                row_layout.addWidget(radio)
                row_layout.addStretch()
                self.button_group.addButton(radio)
                self.radio_buttons.append(radio)
                self.device_frame.layout().addWidget(row_widget)

        if error_message:
            self.error_label.setText(self.map_hwi_error(error_message))
            self.error_label.setVisible(True)
            for radio in self.radio_buttons:
                radio.setEnabled(False)
        else:
            self.error_label.clear()
            self.error_label.setVisible(False)
            for radio in self.radio_buttons:
                radio.setEnabled(True)

        self._update_connect_button_state()

    def _on_connect(self):
        """
        Handle connect button click, re-enumerate devices, and save xpubs/fingerprint.
        """
        # Stop polling while connecting
        if self.poll_timer:
            self.poll_timer.stop()
        self._show_connecting_loader()
        selected_button = self.button_group.checkedButton()
        if not selected_button:
            self._reset_connecting_loader()
            if self.poll_timer:
                self.poll_timer.start(5000)
            return
        selected_fingerprint = selected_button.property('fingerprint')
        devices = hwi_enumerate(allow_emulators=True)
        matched_device = None
        for d in devices:
            if d.get('fingerprint', 'no-fp') == selected_fingerprint:
                matched_device = d
                break
        if matched_device is None:
            ToastManager.error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'device_not_found',
                ),
            )
            self._reset_connecting_loader()
            return
        if matched_device and matched_device.get('error'):
            ToastManager.error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'device_locked',
                ),
            )
            self._reset_connecting_loader()
            return

        device_path = matched_device['path']
        network = SettingRepository.get_wallet_network()
        self._device_selection_view_model.connect_to_device(
            device_path, network,
        )

    def _show_connecting_loader(self):
        """
        Show loader animation and message while connecting to device.
        """
        # Hide all radio buttons and error labels
        self.title.hide()
        for radio in self.radio_buttons:
            radio.hide()
        self.error_label.hide()
        # Show loader and message
        self._loader_label = QLabel(self)
        self._loader_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._loader_movie = QMovie(':/assets/images/button_loading.gif')
        self._loader_movie.setScaledSize(QSize(45, 45))
        self._loader_label.setMovie(self._loader_movie)
        self._loader_movie.start()
        self.layout().insertWidget(2, self._loader_label)
        self._loader_text = QLabel(self)
        self._loader_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._loader_text.setObjectName('hardware_wallet_connect_info')
        self._loader_text.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'connecting_to_device',
            ),
        )
        self.layout().insertWidget(3, self._loader_text)
        self.connect_button.hide()

    def _reset_connecting_loader(self):
        """
        Restore UI to allow retry after connection attempt.
        """
        # Restore UI to allow retry
        self.title.show()
        for radio in self.radio_buttons:
            radio.show()
        self.error_label.show()
        self._loader_label.hide()
        self._loader_movie.stop()
        self._loader_text.hide()
        self.connect_button.show()

    def set_error(self, message: str):
        """
        Show error icon and message. Shows Done, hides Cancel.

        Args:
            message: The error message to display.
        """
        if self._loader_movie is not None:
            self._loader_movie.stop()

        message = self.map_hwi_error(message)
        self._loader_label.setPixmap(
            QPixmap(':/assets/x_circle_red.png').scaled(
                75, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        self._loader_text.setText(message)
        self.cancel_button.setVisible(True)
        self._loader_label.setVisible(True)

    def get_selected_device(self):
        """
        Return the currently selected device name, or None if not selected.
        Returns:
            str or None: The selected device name.
        """
        selected_button = self.button_group.checkedButton()
        if selected_button:
            return selected_button.text()
        return None

    def checking_devices(self):
        """
        Checking devices with HWI enumerate and update device list and error label.
        """
        # Store the currently selected fingerprint (if any)
        selected_fingerprint = None
        selected_button = self.button_group.checkedButton()
        if selected_button:
            selected_fingerprint = selected_button.property('fingerprint')

        devices_info = hwi_enumerate(allow_emulators=True)
        error_message = None
        for d in devices_info:
            if d.get('error'):
                error_message = d.get('error')
                break
        self.populate_devices(devices_info, error_message=error_message)

        # After repopulating, re-select the previously selected device if still present
        if selected_fingerprint:
            for radio in self.radio_buttons:
                if radio.property('fingerprint') == selected_fingerprint:
                    radio.setChecked(True)
                    break

        self._update_connect_button_state()

    @staticmethod
    def map_model_name(model):
        """
        Map the model string to a translated user-friendly model name.
        Args:
            model: The model string from the device info.
        Returns:
            str: Translated user-friendly model name.
        """
        model = model or ''
        model_lower = model.lower()

        if 'nano_s_plus' in model_lower:
            return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_nano_s_plus')
        if 'nano_s' in model_lower:
            return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_nano_s')
        if 'nano_x' in model_lower:
            return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_nano_x')
        if 'stax' in model_lower:
            return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_stax')
        if 'flex' in model_lower:
            return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger_flex')

        return model.title()

    @staticmethod
    def map_hwi_error(error_message: str) -> str:
        """
        Maps raw HWI error messages to user-friendly translated messages.
        Args:
            error_message: The raw error message from HWI.
        Returns:
            str: Translated or mapped error message.
        """
        if not error_message:
            return ''

        error_message_lower = error_message.lower()

        error_mapping: dict[str, str] = {
            'not in either the bitcoin or bitcoin testnet app': 'ledger_not_in_bitcoin_or_testnet_app',
            '0x5515': 'ledger_unlock_device',
            'open failed': 'ledger_open_failed',
            '0x6985': 'ledger_operation_cancelled',
            '0x6a82': 'ledger_command_not_supported',
            '0x0': 'ledger_operation_cancelled',
        }

        for pattern, translation_key in error_mapping.items():
            if pattern in error_message_lower:
                return QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, translation_key)

        return error_message

    def reject(self):
        """
        Stop polling and reject the dialog.
        """
        if hasattr(self, 'poll_timer') and self.poll_timer:
            self.poll_timer.stop()
        super().reject()

    def closeEvent(self, event):
        """
        Stop polling and handle dialog close event.
        """
        if hasattr(self, 'poll_timer') and self.poll_timer:
            self.poll_timer.stop()
        super().closeEvent(event)
