from __future__ import annotations

import hwilib.commands
from PySide6.QtCore import QEvent
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
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

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletEntryType
from src.utils.clickable_frame import ClickableFrame
from src.utils.helpers import load_stylesheet
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.hw_device_selection_dialog import HWDeviceSelectionDialog
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.views.ui_restore_mnemonic import RestoreMnemonicWidget


class HardwareWalletConnectWidget(QWidget):
    def __init__(self, view_model):
        super().__init__()
        self._view_model: MainViewModel = view_model
        self.selected_wallet = None
        self.setObjectName('hardware_wallet_connect_page')
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/hardware_wallet_connect_style.qss',
            ),
        )

        # Main grid layout
        main_grid = QGridLayout(self)
        main_grid.setObjectName('hardware_wallet_connect_grid_layout')

        # Wallet logo frame at the top
        self.wallet_logo = WalletLogoFrame(self)
        main_grid.addWidget(self.wallet_logo, 0, 0, 1, 1)

        # Top vertical spacer (more space)
        vertical_spacer_1 = QSpacerItem(
            20, 320, QSizePolicy.Minimum, QSizePolicy.Preferred,
        )
        main_grid.addItem(vertical_spacer_1, 0, 2, 1, 1)

        # Centered card (QFrame)
        card = QFrame(self)
        card.setObjectName('hardware_wallet_connect_card')
        card.setMinimumSize(QSize(520, 380))
        card.setMaximumSize(QSize(600, 700))
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(28)

        # Title and close button in one row
        title_close_layout = QHBoxLayout()
        title_close_layout.setContentsMargins(0, 0, 0, 0)
        title_close_layout.setSpacing(8)
        title = QLabel('Connect a hardware wallet')
        title.setObjectName('hardware_wallet_connect_title')
        title_close_layout.addWidget(title)
        title_close_layout.addStretch()
        close_btn = QPushButton()
        close_btn.setObjectName('close_button')
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setFixedSize(38, 38)
        close_icon = QIcon(':/assets/x_circle.png')
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(QSize(24, 24))
        close_btn.clicked.connect(self.handle_close)
        title_close_layout.addWidget(close_btn)
        card_layout.addLayout(title_close_layout)

        # Subtitle
        subtitle = QLabel(
            'Select a hardware wallet you would like to use with this app.',
        )
        subtitle.setObjectName('hardware_wallet_connect_subtitle')
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        # Wallet options (centered grid, more spacing)
        grid_frame = QFrame()
        horizontal_layout = QHBoxLayout(grid_frame)
        horizontal_layout.setSpacing(15)
        horizontal_layout.setContentsMargins(12, 0, 0, 0)
        horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.option_buttons = []

        # Ledger option
        ledger_btn = ClickableFrame()
        ledger_btn.setObjectName('hardware_wallet_option')
        ledger_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ledger_btn.setFixedSize(197, 115)
        ledger_btn.setProperty('selected', False)
        ledger_layout = QVBoxLayout(ledger_btn)
        ledger_layout.setContentsMargins(0, 0, 0, 0)
        ledger_layout.setSpacing(20)
        ledger_icon = QLabel()
        ledger_icon.setObjectName('hardware_wallet_icon')
        ledger_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ledger_btn.icon_label = ledger_icon
        ledger_btn.original_icon_path = ':/assets/ledger.png'
        ledger_btn.hover_icon_path = ':/assets/white_ledger.png'
        ledger_pixmap = QPixmap(ledger_btn.original_icon_path)
        ledger_icon.setPixmap(
            ledger_pixmap.scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        ledger_label = QLabel('Ledger')
        ledger_label.setObjectName('hardware_wallet_option_name')
        ledger_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ledger_btn.name_label = ledger_label
        ledger_layout.addWidget(ledger_icon)
        ledger_layout.addWidget(ledger_label)
        ledger_btn.clicked.connect(
            self._make_option_click_handler(ledger_btn, 'Ledger'),
        )
        ledger_btn.installEventFilter(self)
        self.option_buttons.append(ledger_btn)
        horizontal_layout.addWidget(ledger_btn)

        # Trezor option
        trezor_btn = ClickableFrame()
        trezor_btn.setObjectName('hardware_wallet_option')
        trezor_btn.setCursor(QCursor(Qt.PointingHandCursor))
        trezor_btn.setFixedSize(197, 115)
        trezor_btn.setProperty('selected', False)
        trezor_layout = QVBoxLayout(trezor_btn)
        trezor_layout.setContentsMargins(0, 0, 0, 0)
        trezor_layout.setSpacing(25)
        trezor_icon = QLabel()
        trezor_icon.setObjectName('hardware_wallet_icon')
        trezor_icon.setAlignment(Qt.AlignmentFlag.AlignLeft)
        trezor_btn.icon_label = trezor_icon
        trezor_btn.original_icon_path = ':/assets/trezor.png'
        trezor_btn.hover_icon_path = ':/assets/white_trezor.png'
        trezor_pixmap = QPixmap(trezor_btn.original_icon_path)
        trezor_icon.setPixmap(
            trezor_pixmap.scaled(
                125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation,
            ),
        )
        trezor_label = QLabel('Trezor')
        trezor_label.setObjectName('hardware_wallet_option_name')
        trezor_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        trezor_btn.name_label = trezor_label
        trezor_layout.addWidget(trezor_icon)
        trezor_layout.addWidget(trezor_label)
        trezor_btn.clicked.connect(
            self._make_option_click_handler(trezor_btn, 'Trezor'),
        )
        trezor_btn.installEventFilter(self)
        self.option_buttons.append(trezor_btn)
        horizontal_layout.addWidget(trezor_btn)

        card_layout.addWidget(grid_frame, alignment=Qt.AlignmentFlag.AlignLeft)

        # Spacer above Continue button
        card_layout.addSpacing(18)

        # Continue button (centered, more padding)
        self.continue_button = PrimaryButton('Continue')
        self.continue_button.setObjectName('primary_button')
        self.continue_button.setEnabled(False)
        card_layout.addWidget(
            self.continue_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # Add card to grid layout
        main_grid.addWidget(card, 1, 1, 2, 2)

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

        self.continue_button.clicked.connect(self.show_device_dialog)

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self._view_model.restore_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self._view_model.restore_view_model.message.connect(
            self.handle_message,
        )

    def eventFilter(self, watched, event):
        if watched in self.option_buttons:
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

    def _make_option_click_handler(self, btn, wallet_name):
        def handler():
            for b in self.option_buttons:
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

            self.selected_wallet = wallet_name
            self.continue_button.setEnabled(True)
        return handler

    def show_device_dialog(self):
        wallet_type = self.selected_wallet  # 'Ledger' or 'Trezor'
        # 1. Call HWI enumerate
        devices = hwilib.commands.enumerate()
        # 2. Filter by model type
        filtered_devices = [
            d for d in devices if d.get(
                'type', '',
            ).lower() == wallet_type.lower()
        ]
        # 3. Display device names in dialog
        device_names = [
            f"{d.get('model')} ({d.get('fingerprint', '')})" for d in filtered_devices
        ]
        dialog = HWDeviceSelectionDialog(
            wallet_type, devices=device_names, parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            selected_name = dialog.get_selected_device()
            # 4. Find the selected device dict
            selected_device = next(
                (
                    d for d in filtered_devices if f"{d.get('model')} ({
                        d.get('fingerprint', '')
                    })" == selected_name
                ), None,
            )
            if SettingRepository.get_wallet_entry_type() == WalletEntryType.LOAD:
                blur_effect = QGraphicsBlurEffect()
                blur_effect.setBlurRadius(10)
                restore_dialog = RestoreMnemonicWidget(
                    view_model=self._view_model, parent=self,
                )
                if restore_dialog.exec() == QDialog.Accepted:
                    self._view_model.page_navigation.welcome_page()
            else:
                self._view_model.page_navigation.welcome_page()

    def handle_close(self):
        # Navigate back to selection page (not welcome page)
        self._view_model.page_navigation.selection_page()

    # def update_loading_state(self, is_loading: bool):
    #     """
    #     Updates the loading state of the proceed_wallet_password object.

    #     This method prints the loading state and starts or stops the loading animation
    #     of the proceed_wallet_password object based on the value of is_loading.
    #     """
    #     if is_loading:
    #         self.create_btn.setEnabled(False)
    #         self.restore_btn.start_loading()
    #     else:
    #         self.create_btn.setEnabled(True)
    #         self.restore_btn.stop_loading()

    # def handle_message(self, msg_type: ToastPreset, message: str):
    #     """This method handled to show message."""
    #     if msg_type == ToastPreset.ERROR:
    #         ToastManager.error(message)
    #     else:
    #         ToastManager.success(message)
