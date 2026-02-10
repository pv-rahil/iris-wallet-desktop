# pylint: disable = too-many-statements,invalid-name,too-many-instance-attributes
"""
Widget for connecting to a hardware wallet in the application.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QEvent
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGraphicsBlurEffect
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_CONTINUE_BUTTON
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_LEDGER_OPTION
from accessible_constant import HARDWARE_WALLET_CONNECT_PAGE_TREZOR_OPTION
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletEntryType
from src.utils.clickable_frame import ClickableFrame
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


class HardwareWalletConnectWidget(QWidget):
    """
    Widget for connecting to a hardware wallet in the application.
    """

    def __init__(self, view_model, is_multisig=False):
        """
        Initialize the HardwareWalletConnectWidget.
        """
        super().__init__()
        self._view_model: MainViewModel = view_model
        self._selected_wallet = None
        self._is_multisig = is_multisig
        self.setObjectName('hardware_wallet_connect_page')
        self.setAccessibleName(HARDWARE_WALLET_CONNECT_PAGE)
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/hardware_wallet_connect_style.qss',
            ),
        )

        # Main grid layout
        main_grid = QGridLayout(self)
        main_grid.setObjectName('hardware_wallet_connect_grid_layout')

        # Wallet logo frame at the top
        _wallet_logo = WalletLogoFrame(self)
        main_grid.addWidget(_wallet_logo, 0, 0, 1, 1)

        # Top vertical spacer (more space)
        vertical_spacer_1 = QSpacerItem(
            20, 320, QSizePolicy.Minimum, QSizePolicy.Preferred,
        )
        main_grid.addItem(vertical_spacer_1, 0, 2, 1, 1)

        # Centered card (QFrame)
        self.card = QFrame(self)
        self.card.setObjectName('hardware_wallet_connect_card')
        self.card.setMinimumSize(QSize(520, 380))
        self.card.setMaximumSize(QSize(600, 700))
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.card_layout.setContentsMargins(40, 40, 40, 40)
        self.card_layout.setSpacing(28)

        # Title and close button in one row
        title_close_layout = QHBoxLayout()
        title_close_layout.setContentsMargins(0, 0, 0, 0)
        title_close_layout.setSpacing(8)
        self.title = QLabel()
        self.title.setObjectName('hardware_wallet_selection_title')
        title_close_layout.addWidget(self.title)
        title_close_layout.addStretch()
        self.close_btn = QPushButton()
        self.close_btn.setObjectName('close_button')
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setFixedSize(38, 38)
        close_icon = QIcon(':/assets/x_circle.png')
        self.close_btn.setIcon(close_icon)
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.clicked.connect(self.handle_close)
        title_close_layout.addWidget(self.close_btn)
        self.card_layout.addLayout(title_close_layout)

        # Subtitle
        self.subtitle = QLabel()
        self.subtitle.setObjectName('hardware_wallet_connect_subtitle')
        self.subtitle.setWordWrap(True)
        self.card_layout.addWidget(self.subtitle)

        # Wallet options (centered grid, more spacing)
        self.grid_frame = QFrame()
        horizontal_layout = QHBoxLayout(self.grid_frame)
        horizontal_layout.setSpacing(15)
        horizontal_layout.setContentsMargins(12, 0, 0, 0)
        horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._option_buttons = []

        # Ledger option
        self.ledger_btn = ClickableFrame()
        self.ledger_btn.setObjectName('hardware_wallet_option')
        self.ledger_btn.setAccessibleName(
            HARDWARE_WALLET_CONNECT_PAGE_LEDGER_OPTION,
        )
        self.ledger_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ledger_btn.setFixedSize(197, 115)
        self.ledger_btn.setProperty('selected', False)
        ledger_layout = QVBoxLayout(self.ledger_btn)
        ledger_layout.setContentsMargins(0, 0, 0, 0)
        ledger_layout.setSpacing(20)
        ledger_icon = QLabel()
        ledger_icon.setObjectName('hardware_wallet_icon')
        ledger_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.ledger_btn.icon_label = ledger_icon
        self.ledger_btn.original_icon_path = ':/assets/ledger.png'
        self.ledger_btn.hover_icon_path = ':/assets/white_ledger.png'
        ledger_pixmap = QPixmap(self.ledger_btn.original_icon_path)
        ledger_icon.setPixmap(
            ledger_pixmap.scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        self.ledger_label = QLabel()
        self.ledger_label.setObjectName('hardware_wallet_option_name')
        self.ledger_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.ledger_btn.name_label = self.ledger_label
        ledger_layout.addWidget(ledger_icon)
        ledger_layout.addWidget(self.ledger_label)
        self.ledger_btn.clicked.connect(
            self.make_option_click_handler(self.ledger_btn, 'Ledger'),
        )
        self.ledger_btn.installEventFilter(self)
        self._option_buttons.append(self.ledger_btn)
        horizontal_layout.addWidget(self.ledger_btn)

        # Trezor option
        self.trezor_btn = ClickableFrame()
        self.trezor_btn.setObjectName('hardware_wallet_option')
        self.trezor_btn.setAccessibleName(
            HARDWARE_WALLET_CONNECT_PAGE_TREZOR_OPTION,
        )
        self.trezor_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.trezor_btn.setFixedSize(197, 115)
        self.trezor_btn.setProperty('selected', False)
        trezor_layout = QVBoxLayout(self.trezor_btn)
        trezor_layout.setContentsMargins(0, 0, 0, 0)
        trezor_layout.setSpacing(25)
        trezor_icon = QLabel()
        trezor_icon.setObjectName('hardware_wallet_icon')
        trezor_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.trezor_btn.icon_label = trezor_icon
        self.trezor_btn.original_icon_path = ':/assets/trezor.png'
        self.trezor_btn.hover_icon_path = ':/assets/white_trezor.png'
        trezor_pixmap = QPixmap(self.trezor_btn.original_icon_path)
        trezor_icon.setPixmap(
            trezor_pixmap.scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        self.trezor_label = QLabel()
        self.trezor_label.setObjectName('hardware_wallet_option_name')
        self.trezor_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.trezor_btn.name_label = self.trezor_label
        trezor_layout.addWidget(trezor_icon)
        trezor_layout.addWidget(self.trezor_label)
        self.trezor_btn.setDisabled(True)
        self.trezor_btn.clicked.connect(
            self.make_option_click_handler(self.trezor_btn, 'Trezor'),
        )
        self.trezor_btn.installEventFilter(self)
        self._option_buttons.append(self.trezor_btn)
        horizontal_layout.addWidget(self.trezor_btn)

        self.card_layout.addWidget(
            self.grid_frame, alignment=Qt.AlignmentFlag.AlignLeft,
        )

        # Spacer above Continue button
        self.card_layout.addSpacing(18)

        # Continue button (centered, more padding)
        self.continue_btn = PrimaryButton()
        self.continue_btn.setAccessibleName(
            HARDWARE_WALLET_CONNECT_PAGE_CONTINUE_BUTTON,
        )
        self.continue_btn.setObjectName('primary_button')
        self.continue_btn.setEnabled(False)
        self.card_layout.addWidget(
            self.continue_btn,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # Add card to grid layout
        main_grid.addWidget(self.card, 1, 1, 2, 2)

        # Horizontal spacers (left and right)
        horizontal_spacer_3 = QSpacerItem(
            338, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
        )
        main_grid.addItem(horizontal_spacer_3, 1, 3, 1, 1)
        horizontal_spacer_4 = QSpacerItem(
            338, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
        )
        main_grid.addItem(horizontal_spacer_4, 2, 0, 1, 1)

        # Bottom vertical spacer (more space)
        vertical_spacer_3 = QSpacerItem(
            20, 320, QSizePolicy.Minimum, QSizePolicy.Expanding,
        )
        main_grid.addItem(vertical_spacer_3, 4, 1, 1, 1)

        self.continue_btn.clicked.connect(self.show_device_dialog)
        self.retranslate_ui()

    def setup_ui_connection(self):
        """
        Set up connections for UI elements.
        """
        self._view_model.restore_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self._view_model.restore_view_model.message.connect(
            self.handle_message,
        )

    def eventFilter(self, watched, event):
        """
        Handle hover and click events for hardware wallet option buttons.
        """
        if watched in self._option_buttons:
            # Only apply hover effect if the button is enabled
            if not watched.isEnabled():
                return super().eventFilter(watched, event)
            icon_label = watched.icon_label
            name_label = watched.name_label
            original_pixmap = QPixmap(watched.original_icon_path).scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            hover_pixmap = QPixmap(watched.hover_icon_path).scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )

            if event.type() == QEvent.Type.Enter:
                icon_label.setPixmap(hover_pixmap)
                name_label.setStyleSheet('color: white;')
                return True
            if event.type() == QEvent.Type.Leave:
                if not watched.property('selected'):
                    icon_label.setPixmap(original_pixmap)
                    name_label.setStyleSheet('color: rgb(140, 145, 160);')
                return True
        return super().eventFilter(watched, event)

    def make_option_click_handler(self, btn, wallet_name):
        """
        Return a handler function for wallet option button clicks.
        """
        def handler():
            for b in self._option_buttons:
                b.setProperty('selected', False)
                b.icon_label.setPixmap(
                    QPixmap(b.original_icon_path).scaled(
                        125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                    ),
                )
                b.name_label.setStyleSheet('color: rgb(140, 145, 160);')

            btn.setProperty('selected', True)
            btn.icon_label.setPixmap(
                QPixmap(btn.hover_icon_path).scaled(
                    125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
                ),
            )
            btn.name_label.setStyleSheet('color: white;')

            self._selected_wallet = wallet_name
            self.continue_btn.setEnabled(True)
        return handler

    def show_device_dialog(self):
        """
        Show the hardware wallet device selection dialog.
        """
        wallet_type = self._selected_wallet  # 'Ledger' or 'Trezor'
        dialog = HWDeviceSelectionDialog(wallet_type, parent=self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            if SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD:
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(10)
                restore_dialog = RestoreMnemonicWidget(
                    view_model=self._view_model, parent=self,
                )
                if restore_dialog.exec() == QDialog.Accepted:
                    self._view_model.page_navigation.welcome_page()
            else:
                # Check if this is multisig flow
                if self._is_multisig:
                    # Navigate back to multisig setup page after successful connection
                    self._view_model.page_navigation.multisig_setup_page()
                else:
                    self._view_model.page_navigation.welcome_page()

    def handle_close(self):
        """
        Navigate back to selection page if not multisig setup page.
        """
        # Navigate back to selection page (not welcome page)
        if self._is_multisig:
            self._view_model.page_navigation.multisig_setup_page()
        else:
            self._view_model.page_navigation.selection_page()

    def retranslate_ui(self):
        """
        Set all translatable UI text for the widget.
        """
        self.title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'connect_hardware_wallet',
            ),
        )
        self.subtitle.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'select_hardware_wallet',
            ),
        )
        self.ledger_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ledger',
            ),
        )
        self.trezor_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'trezor',
            ),
        )
        self.continue_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
            ),
        )
