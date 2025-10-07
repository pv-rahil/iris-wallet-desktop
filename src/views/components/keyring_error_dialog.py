"""Keyring error dialog box module"""
# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QCheckBox
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout

from accessible_constant import KEYRING_CANCEL_BUTTON
from accessible_constant import KEYRING_CONTINUE_BUTTON
from accessible_constant import KEYRING_DIALOG_BOX
from accessible_constant import KEYRING_FINGERPRINT_COPY_BUTTON
from accessible_constant import KEYRING_FINGERPRINT_FRAME
from accessible_constant import KEYRING_FINGERPRINT_VALUE_LABEL
from accessible_constant import KEYRING_MNEMONIC_COPY_BUTTON
from accessible_constant import KEYRING_MNEMONIC_VALUE_LABEL
from accessible_constant import KEYRING_MNEMONICS_FRAME
from accessible_constant import KEYRING_PASSWORD_COPY_BUTTON
from accessible_constant import KEYRING_PASSWORD_FRAME
from accessible_constant import KEYRING_PASSWORD_VALUE_LABEL
from accessible_constant import KEYRING_XPUB_COLORED_COPY_BUTTON
from accessible_constant import KEYRING_XPUB_COLORED_FRAME
from accessible_constant import KEYRING_XPUB_COLORED_VALUE_LABEL
from accessible_constant import KEYRING_XPUB_VANILLA_COPY_BUTTON
from accessible_constant import KEYRING_XPUB_VANILLA_FRAME
from accessible_constant import KEYRING_XPUB_VANILLA_VALUE_LABEL
from accessible_constant import SAVE_CREDENTIALS_CHECK_BOX
from src.data.repository.setting_repository import SettingRepository
from src.model.common_operation_model import KeyringDialogModel
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.common_utils import copy_text
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import IS_NATIVE_AUTHENTICATION_ENABLED
from src.utils.constant import NATIVE_LOGIN_ENABLED
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.custom_exception import CommonException
from src.utils.helpers import load_stylesheet
from src.utils.keyring_storage import delete_value
from src.utils.local_store import local_store
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.toast import ToastManager


class KeyringErrorDialog(QDialog):
    """
    KeyringErrorDialog is a custom dialog box that informs the user of an error when attempting
    to store the mnemonic and password in the keyring. This dialog allows the user to view their
    mnemonic and password and provides actions such as copying the mnemonic for safekeeping.
    """
    error = Signal(
        str,
    )    # This signal will emit a string message in case of an error
    # This signal will emit a string message in case of success
    success = Signal(str)

    def __init__(self, keyring_data: KeyringDialogModel):
        super().__init__(keyring_data.parent)
        self.keyring_data = keyring_data
        self._password = keyring_data.password
        self._mnemonic = keyring_data.mnemonic
        self._xpub_vanilla = keyring_data.xpub_vanilla
        self._xpub_colored = keyring_data.xpub_colored
        self._master_fingerprint = keyring_data.master_fingerprint
        self.navigate_to = keyring_data.navigate_to
        self.originating_page = keyring_data.originating_page
        # Check if this is a watch-only wallet
        self.is_watch_only = bool(
            not self._mnemonic and self._xpub_vanilla and self._xpub_colored and self._master_fingerprint,
        )
        self.setObjectName('keyring')
        self.setAccessibleName(KEYRING_DIALOG_BOX)
        if self.is_watch_only:
            self.resize(570, 500)
        else:
            self.resize(570, 401)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/keyring_error_dialog.qss',
            ),
        )
        self.dialog_box_vertical_layout = QVBoxLayout(self)
        self.dialog_box_vertical_layout.setSpacing(12)
        self.dialog_box_vertical_layout.setObjectName(
            'dialog_box_vertical_layout',
        )
        self.dialog_box_vertical_layout.setContentsMargins(18, -1, 18, 20)
        self.info_label = QLabel(self)
        self.info_label.setObjectName('info_label')
        self.info_label.setWordWrap(True)

        self.dialog_box_vertical_layout.addWidget(self.info_label)

        self.mnemonic_frame = QFrame(self)
        self.mnemonic_frame.setObjectName('mnemonic_frame')
        self.mnemonic_frame.setAccessibleName(KEYRING_MNEMONICS_FRAME)
        self.mnemonic_frame.setFrameShape(QFrame.StyledPanel)
        self.mnemonic_frame.setFrameShadow(QFrame.Raised)
        self.vertical_layout = QVBoxLayout(self.mnemonic_frame)
        self.vertical_layout.setSpacing(2)
        self.vertical_layout.setObjectName('verticalLayout')
        self.vertical_layout.setContentsMargins(6, 13, 12, -1)
        self.mnemonic_horizontal_layout = QHBoxLayout()
        self.mnemonic_horizontal_layout.setObjectName(
            'mnemonic_horizontal_layout',
        )
        self.mnemonic_horizontal_layout.setContentsMargins(-1, -1, 5, -1)
        self.mnemonic_title_label = QLabel(self.mnemonic_frame)
        self.mnemonic_title_label.setObjectName('mnemonic_title_label')

        self.mnemonic_horizontal_layout.addWidget(self.mnemonic_title_label)

        self.mnemonic_copy_button = QPushButton(self.mnemonic_frame)
        self.mnemonic_copy_button.setObjectName('mnemonic_copy_button')
        self.mnemonic_copy_button.setAccessibleName(
            KEYRING_MNEMONIC_COPY_BUTTON,
        )
        self.mnemonic_copy_button.setMinimumSize(QSize(16, 16))
        self.mnemonic_copy_button.setMaximumSize(QSize(16, 16))
        self.mnemonic_copy_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.mnemonic_copy_button.setStyleSheet('')
        icon = QIcon()
        icon.addFile(':assets/copy.png', QSize(), QIcon.Normal, QIcon.Off)
        self.mnemonic_copy_button.setIcon(icon)

        self.mnemonic_horizontal_layout.addWidget(self.mnemonic_copy_button)

        self.mnemonic_value_label = QLabel(self.mnemonic_frame)
        self.mnemonic_value_label.setObjectName('mnemonic_value_label')
        self.mnemonic_value_label.setAccessibleDescription(
            KEYRING_MNEMONIC_VALUE_LABEL,
        )
        self.mnemonic_value_label.setWordWrap(True)

        self.xpub_vanilla_frame = QFrame(self)
        self.xpub_vanilla_frame.setObjectName('xpub_vanilla_frame')
        self.xpub_vanilla_frame.setAccessibleName(KEYRING_XPUB_VANILLA_FRAME)
        self.xpub_vanilla_frame.setFrameShape(QFrame.StyledPanel)
        self.xpub_vanilla_frame.setFrameShadow(QFrame.Raised)
        self.xpub_vanilla_layout = QVBoxLayout(self.xpub_vanilla_frame)
        self.xpub_vanilla_layout.setSpacing(2)
        self.xpub_vanilla_layout.setContentsMargins(6, 13, 12, -1)

        self.xpub_vanilla_header = QHBoxLayout()
        self.xpub_vanilla_label = QLabel()
        self.xpub_vanilla_label.setObjectName('xpub_vanilla_label')
        self.xpub_vanilla_copy = QPushButton()
        self.xpub_vanilla_copy.setObjectName('xpub_vanilla_copy_button')
        self.xpub_vanilla_copy.setAccessibleName(
            KEYRING_XPUB_VANILLA_COPY_BUTTON,
        )
        self.xpub_vanilla_copy.setIcon(icon)
        self.xpub_vanilla_copy.setMinimumSize(QSize(16, 16))
        self.xpub_vanilla_copy.setMaximumSize(QSize(16, 16))
        self.xpub_vanilla_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self.xpub_vanilla_header.addWidget(self.xpub_vanilla_label)
        self.xpub_vanilla_header.addWidget(self.xpub_vanilla_copy)
        self.xpub_vanilla_value = QLabel()
        self.xpub_vanilla_value.setObjectName('xpub_vanilla_value_label')
        self.xpub_vanilla_value.setAccessibleDescription(
            KEYRING_XPUB_VANILLA_VALUE_LABEL,
        )
        self.xpub_vanilla_value.setWordWrap(True)
        self.xpub_vanilla_layout.addLayout(self.xpub_vanilla_header)
        self.xpub_vanilla_layout.addWidget(self.xpub_vanilla_value)

        self.xpub_colored_frame = QFrame(self)
        self.xpub_colored_frame.setObjectName('xpub_colored_frame')
        self.xpub_colored_frame.setAccessibleName(KEYRING_XPUB_COLORED_FRAME)
        self.xpub_colored_frame.setFrameShape(QFrame.StyledPanel)
        self.xpub_colored_frame.setFrameShadow(QFrame.Raised)
        self.xpub_colored_layout = QVBoxLayout(self.xpub_colored_frame)
        self.xpub_colored_layout.setSpacing(2)
        self.xpub_colored_layout.setContentsMargins(6, 13, 12, -1)

        self.xpub_colored_header = QHBoxLayout()
        self.xpub_colored_label = QLabel()
        self.xpub_colored_label.setObjectName('xpub_colored_label')
        self.xpub_colored_copy = QPushButton()
        self.xpub_colored_copy.setObjectName('xpub_colored_copy_button')
        self.xpub_colored_copy.setAccessibleName(
            KEYRING_XPUB_COLORED_COPY_BUTTON,
        )
        self.xpub_colored_copy.setIcon(icon)
        self.xpub_colored_copy.setMinimumSize(QSize(16, 16))
        self.xpub_colored_copy.setMaximumSize(QSize(16, 16))
        self.xpub_colored_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self.xpub_colored_header.addWidget(self.xpub_colored_label)
        self.xpub_colored_header.addWidget(self.xpub_colored_copy)
        self.xpub_colored_value = QLabel()
        self.xpub_colored_value.setObjectName('xpub_colored_value_label')
        self.xpub_colored_value.setAccessibleDescription(
            KEYRING_XPUB_COLORED_VALUE_LABEL,
        )
        self.xpub_colored_value.setWordWrap(True)
        self.xpub_colored_layout.addLayout(self.xpub_colored_header)
        self.xpub_colored_layout.addWidget(self.xpub_colored_value)

        self.fingerprint_frame = QFrame(self)
        self.fingerprint_frame.setObjectName('fingerprint_frame')
        self.fingerprint_frame.setAccessibleName(KEYRING_FINGERPRINT_FRAME)
        self.fingerprint_frame.setFrameShape(QFrame.StyledPanel)
        self.fingerprint_frame.setFrameShadow(QFrame.Raised)
        self.fingerprint_layout = QVBoxLayout(self.fingerprint_frame)
        self.fingerprint_layout.setSpacing(2)
        self.fingerprint_layout.setContentsMargins(6, 13, 12, -1)

        self.fingerprint_header = QHBoxLayout()
        self.fingerprint_label = QLabel()
        self.fingerprint_label.setObjectName('fingerprint_title_label')
        self.fingerprint_copy = QPushButton()
        self.fingerprint_copy.setObjectName('fingerprint_copy_button')
        self.fingerprint_copy.setAccessibleName(
            KEYRING_FINGERPRINT_COPY_BUTTON,
        )
        self.fingerprint_copy.setIcon(icon)
        self.fingerprint_copy.setMinimumSize(QSize(16, 16))
        self.fingerprint_copy.setMaximumSize(QSize(16, 16))
        self.fingerprint_copy.setCursor(QCursor(Qt.PointingHandCursor))
        self.fingerprint_header.addWidget(self.fingerprint_label)
        self.fingerprint_header.addWidget(self.fingerprint_copy)
        self.fingerprint_value = QLabel()
        self.fingerprint_value.setObjectName('fingerprint_value_label')
        self.fingerprint_value.setAccessibleDescription(
            KEYRING_FINGERPRINT_VALUE_LABEL,
        )
        self.fingerprint_value.setWordWrap(True)
        self.fingerprint_layout.addLayout(self.fingerprint_header)
        self.fingerprint_layout.addWidget(self.fingerprint_value)

        # Add watch-only frames to dialog layout
        if self.is_watch_only:
            self.dialog_box_vertical_layout.addWidget(self.xpub_vanilla_frame)
            self.dialog_box_vertical_layout.addWidget(self.xpub_colored_frame)
            self.dialog_box_vertical_layout.addWidget(self.fingerprint_frame)
            # Hide mnemonic frame for watch-only
            self.mnemonic_frame.hide()
        else:
            # Hide watch-only frames for regular wallet
            self.xpub_vanilla_frame.hide()
            self.xpub_colored_frame.hide()
            self.fingerprint_frame.hide()
            self.vertical_layout.addLayout(self.mnemonic_horizontal_layout)
            self.vertical_layout.addWidget(self.mnemonic_value_label)

        self.dialog_box_vertical_layout.addWidget(self.mnemonic_frame)

        self.wallet_password_vertical_layout = QVBoxLayout()
        self.wallet_password_vertical_layout.setObjectName(
            'wallet_password_vertical_layout',
        )
        self.password_frame = QFrame(self)
        self.password_frame.setObjectName('password_frame')
        self.password_frame.setAccessibleName(KEYRING_PASSWORD_FRAME)
        self.password_frame.setFrameShape(QFrame.StyledPanel)
        self.password_frame.setFrameShadow(QFrame.Raised)
        self.password_frame_vertical_layout = QVBoxLayout(self.password_frame)
        self.password_frame_vertical_layout.setSpacing(2)
        self.password_frame_vertical_layout.setObjectName(
            'password_frame_vertical_layout',
        )
        self.password_frame_vertical_layout.setContentsMargins(6, 13, 9, -1)
        self.wallet_password_horizontal_layout = QHBoxLayout()
        self.wallet_password_horizontal_layout.setObjectName(
            'wallet_password_horizontalLayout',
        )
        self.wallet_password_horizontal_layout.setContentsMargins(0, -1, 5, -1)
        self.wallet_password_title_label = QLabel(self.password_frame)
        self.wallet_password_title_label.setObjectName(
            'wallet_password_title_label',
        )

        self.wallet_password_horizontal_layout.addWidget(
            self.wallet_password_title_label,
        )

        self.password_copy_button = QPushButton(self.password_frame)
        self.password_copy_button.setObjectName('password_copy_button')
        self.password_copy_button.setAccessibleName(
            KEYRING_PASSWORD_COPY_BUTTON,
        )
        self.password_copy_button.setMinimumSize(QSize(16, 16))
        self.password_copy_button.setMaximumSize(QSize(16, 16))
        self.password_copy_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.password_copy_button.setToolTipDuration(19)
        self.password_copy_button.setIcon(icon)

        self.wallet_password_horizontal_layout.addWidget(
            self.password_copy_button,
        )

        self.password_frame_vertical_layout.addLayout(
            self.wallet_password_horizontal_layout,
        )

        self.wallet_password_value = QLabel(self.password_frame)
        self.wallet_password_value.setObjectName('wallet_password_value')
        self.wallet_password_value.setAccessibleDescription(
            KEYRING_PASSWORD_VALUE_LABEL,
        )
        self.wallet_password_value.setMinimumSize(QSize(300, 0))
        self.wallet_password_value.setMaximumSize(QSize(16777215, 16777215))
        self.wallet_password_value.setStyleSheet('')

        self.password_frame_vertical_layout.addWidget(
            self.wallet_password_value,
        )

        self.wallet_password_vertical_layout.addWidget(self.password_frame)

        self.dialog_box_vertical_layout.addLayout(
            self.wallet_password_vertical_layout,
        )

        self.check_box = QCheckBox(self)
        self.check_box.setObjectName('check_box')
        self.check_box.setAccessibleName(SAVE_CREDENTIALS_CHECK_BOX)
        self.check_box.setCursor(QCursor(Qt.PointingHandCursor))

        self.dialog_box_vertical_layout.addWidget(self.check_box)
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName('buttton_layout')
        self.cancel_button = SecondaryButton()
        self.cancel_button.setAccessibleName(KEYRING_CANCEL_BUTTON)
        self.cancel_button.setMinimumSize(QSize(220, 35))
        self.cancel_button.setMaximumSize(QSize(300, 35))
        self.cancel_button.hide()

        self.button_layout.addWidget(self.cancel_button)
        self.continue_button = PrimaryButton()
        self.continue_button.setAccessibleName(KEYRING_CONTINUE_BUTTON)
        self.continue_button.setMinimumSize(QSize(220, 35))
        self.continue_button.setMaximumSize(QSize(300, 35))
        self.continue_button.setEnabled(False)
        self.button_layout.addWidget(self.continue_button)

        self.dialog_box_vertical_layout.addLayout(self.button_layout)

        self.retranslate_ui()
        self.setup_ui_connection()
        self.handle_disable_keyring()

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.check_box.stateChanged.connect(self.handle_continue_button)
        self.continue_button.clicked.connect(self.on_click_continue)

        if self.is_watch_only:
            self.xpub_vanilla_copy.clicked.connect(
                lambda: self.on_click_copy_button(button_name='xpub_vanilla'),
            )
            self.xpub_colored_copy.clicked.connect(
                lambda: self.on_click_copy_button(button_name='xpub_colored'),
            )
            self.fingerprint_copy.clicked.connect(
                lambda: self.on_click_copy_button(button_name='fingerprint'),
            )
        else:
            self.mnemonic_copy_button.clicked.connect(
                lambda: self.on_click_copy_button(button_name='mnemonic_text'),
            )

        self.password_copy_button.clicked.connect(
            lambda: self.on_click_copy_button(button_name='password_text'),
        )
        self.cancel_button.clicked.connect(self.on_click_cancel)

    def retranslate_ui(self):
        """Retranslate ui"""
        if self.is_watch_only:
            self.info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keyring_error_message_watch_only', None,
                ),
            )
            self.xpub_vanilla_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'vanilla_xpub', None,
                ),
            )
            self.xpub_vanilla_copy.setToolTip(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_vanilla_xpub', None,
                ),
            )
            self.xpub_vanilla_value.setText(
                self._truncate_xpub(self._xpub_vanilla),
            )
            self.xpub_colored_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'colored_xpub', None,
                ),
            )
            self.xpub_colored_copy.setToolTip(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_colored_xpub', None,
                ),
            )
            self.xpub_colored_value.setText(
                self._truncate_xpub(self._xpub_colored),
            )
            self.fingerprint_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'master_fingerprint', None,
                ),
            )
            self.fingerprint_copy.setToolTip(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_fingerprint', None,
                ),
            )
            self.fingerprint_value.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, self._master_fingerprint, None,
                ),
            )
        else:
            self.info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keyring_error_message', None,
                ),
            )
            self.mnemonic_title_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'Mnemonic', None,
                ),
            )
            self.mnemonic_copy_button.setToolTip(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_mnemonic', None,
                ),
            )
            self.mnemonic_value_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, self._mnemonic, None,
                ),
            )

        # Common elements for both wallet types
        self.wallet_password_title_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'wallet_password', None,
            ),
        )
        self.password_copy_button.setToolTip(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'copy_password', None,
            ),
        )
        self.wallet_password_value.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self._password, None,
            ),
        )
        self.check_box.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'store_mnemoic_checkbox_message', None,
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue', None,
            ),
        )
        self.cancel_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'cancel', None,
            ),
        )

    def handle_continue_button(self):
        """
        Enables or disables the 'Continue' button based on whether the checkbox is checked.
        If the checkbox is checked, the 'Continue' button is enabled; otherwise, it is disabled.
        """
        is_checked = self.check_box.isChecked()
        if is_checked is True:
            self.continue_button.setEnabled(True)
        if is_checked is False:
            self.continue_button.setEnabled(False)

    def handle_when_origin_page_set_wallet(self):
        """
        If user accept (isChecked = True) then continue otherwise stop application and clean local data
        """
        try:
            if self.check_box.isChecked():
                SettingRepository.set_keyring_status(status=True)
                self.navigate_to()
                self.close()
            else:
                local_store.clear_settings()
                self.close()
                QApplication.instance().exit()
        except CommonException as exc:
            self.error.emit(exc.message)
            ToastManager.error(
                exc.message or 'Something went wrong',
            )
        except Exception as exc:
            self.error.emit('Something went wrong')
            ToastManager.error(
                exc or 'Something went wrong',
            )

    def handle_when_origin_setting_page(self):
        """Handle when keyring toggle disable by user"""
        try:
            network: NetworkEnumModel = SettingRepository.get_wallet_network()
            delete_value(WALLET_PASSWORD_KEY, network.value)
            delete_value(NATIVE_LOGIN_ENABLED)
            delete_value(IS_NATIVE_AUTHENTICATION_ENABLED)
            SettingRepository.set_keyring_status(status=True)
            self.close()
            self.navigate_to()
        except CommonException as exc:
            self.error.emit(exc.message)
            ToastManager.error(
                exc.message or 'Something went wrong',
            )
        except Exception as exc:
            self.error.emit('Something went wrong')
            ToastManager.error(
                exc or 'Something went wrong',
            )

    def on_click_continue(self):
        """
        If user accept (isChecked = True) then continue otherwise stop application and clean local data
        """
        if self.originating_page == 'settings_page':
            self.handle_when_origin_setting_page()
        else:
            self.handle_when_origin_page_set_wallet()

    def on_click_copy_button(self, button_name: str):
        """
        Handles the 'Copy' button click events for copying the mnemonic, password, or watch-only wallet data.
        Based on the button name, it copies the appropriate text to the clipboard.

        Args:
            button_name (str): The identifier for the button clicked.
        """
        if button_name == 'mnemonic_text':
            copy_text(self.mnemonic_value_label)
        elif button_name == 'password_text':
            copy_text(self.wallet_password_value)
        elif button_name == 'xpub_vanilla':
            copy_text(self._xpub_vanilla)
        elif button_name == 'xpub_colored':
            copy_text(self._xpub_colored)
        elif button_name == 'fingerprint':
            copy_text(self.fingerprint_value)

    def handle_disable_keyring(self):
        """
        Handles the disable keyring action by displaying a warning message when the user is on the settings page.
        """
        if self.originating_page == 'settings_page':
            if self.is_watch_only:
                self.info_label.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keyring_error_message_watch_only', None,
                    ),
                )
            else:
                self.info_label.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'keyring_removal_message', None,
                    ),
                )
            self.cancel_button.show()
        else:
            self.cancel_button.hide()

    def on_click_cancel(self):
        """The `on_click_cancel` method closes the dialog when the cancel button is clicked."""
        self.close()

    def _truncate_xpub(self, xpub: str, head: int = 12, tail: int = 12) -> str:
        """
        Truncates an xpub string to a specified length, showing the head and tail parts with an ellipsis in between.
        """
        if not xpub or len(xpub) <= head + tail + 3:
            return xpub
        return f"{xpub[:head]}...{xpub[-tail:]}"
