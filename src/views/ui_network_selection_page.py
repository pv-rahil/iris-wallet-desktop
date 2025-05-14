# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the NetworkSelectionWidget class,
which represents the UI for wallet or transfer selection methods.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.model.setting_model import IsWalletInitialized
from src.utils.clickable_frame import ClickableFrame
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.helpers import load_stylesheet
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.wallet_logo_frame import WalletLogoFrame


class NetworkSelectionWidget(QWidget):
    """This class represents all the UI elements of the network selection page."""

    def __init__(self, view_model, originating_page, network):
        super().__init__()
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/wallet_or_transfer_selection_style.qss',
            ),
        )
        self._prev_network = network
        self.originating_page = originating_page
        self.__loading_translucent_screen = None
        self.view_model: MainViewModel = view_model
        self.current_network = None
        self.grid_layout_main = QGridLayout(self)
        self.grid_layout_main.setObjectName('grid_layout')
        self.grid_layout_main.setContentsMargins(0, 0, 0, 0)
        self.wallet_logo = WalletLogoFrame()
        self.grid_layout_main.addWidget(self.wallet_logo, 0, 0, 1, 8)

        self.vertical_spacer_1 = QSpacerItem(
            20, 208, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.grid_layout_main.addItem(self.vertical_spacer_1, 0, 3, 1, 1)

        self.horizontal_spacer = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.grid_layout_main.addItem(self.horizontal_spacer, 1, 0, 1, 1)

        self.network_selection_widget = QWidget(self)
        self.network_selection_widget.setObjectName('widget_page')
        self.network_selection_widget.setMinimumSize(QSize(870, 440))
        self.network_selection_widget.setMaximumSize(QSize(880, 526))

        self.vertical_layout = QVBoxLayout(self.network_selection_widget)
        self.vertical_layout.setSpacing(6)
        self.vertical_layout.setObjectName('vertical_layout_9')
        self.vertical_layout.setContentsMargins(1, 11, 1, 10)
        self.vertical_layout_1 = QVBoxLayout()
        self.vertical_layout_1.setObjectName('vertical_layout_24')
        self.vertical_layout_1.setContentsMargins(0, 3, 25, 0)
        self.horizontal_layout_title = QHBoxLayout()
        self.horizontal_layout_title.setObjectName('horizontal_layout_title')
        self.horizontal_layout_title.setContentsMargins(35, 9, 40, 0)

        self.title_text_1 = QLabel(self.network_selection_widget)
        self.title_text_1.setObjectName('title_text_1')
        self.title_text_1.setMinimumSize(QSize(750, 50))
        self.horizontal_layout_title.addWidget(self.title_text_1)
        self.select_network_close_btn = QPushButton(
            self.network_selection_widget,
        )
        self.select_network_close_btn.setObjectName('select_network_close_btn')
        self.select_network_close_btn.setMinimumSize(QSize(24, 24))
        self.select_network_close_btn.setMaximumSize(QSize(50, 65))
        self.select_network_close_btn.setAutoFillBackground(False)

        select_network_close_icon = QIcon()
        select_network_close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(),
            QIcon.Normal,
            QIcon.Off,
        )
        self.select_network_close_btn.setIcon(select_network_close_icon)
        self.select_network_close_btn.setIconSize(QSize(24, 24))
        self.select_network_close_btn.setCheckable(False)
        self.select_network_close_btn.setChecked(False)

        self.horizontal_layout_title.addWidget(
            self.select_network_close_btn, 0, Qt.AlignHCenter,
        )

        self.vertical_layout.addLayout(
            self.horizontal_layout_title,
        )
        self.vertical_layout.addLayout(self.vertical_layout_1)

        self.line = QFrame(self.network_selection_widget)
        self.line.setObjectName('line_2')

        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.vertical_layout.addWidget(self.line)

        self.vertical_spacer_2 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout.addItem(self.vertical_spacer_2)

        self.select_network_layout = QHBoxLayout()
        self.select_network_layout.setObjectName('select_option_layout')
        self.select_network_layout.setContentsMargins(-1, -1, -1, 0)
        self.regtest_frame = ClickableFrame(
            NetworkEnumModel.REGTEST.value,
        )
        self.regtest_frame.setObjectName('option_1_frame')
        self.regtest_frame.setMinimumSize(QSize(220, 200))
        self.regtest_frame.setMaximumSize(QSize(220, 200))

        self.regtest_frame.setFrameShape(QFrame.StyledPanel)
        self.regtest_frame.setFrameShadow(QFrame.Raised)
        self.grid_layout = QGridLayout(self.regtest_frame)
        self.grid_layout.setSpacing(0)
        self.grid_layout.setObjectName('grid_layout')
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.regtest_logo = QLabel(self.regtest_frame)
        self.regtest_logo.setObjectName('option_2_logo')
        self.regtest_logo.setMinimumSize(QSize(100, 100))
        self.regtest_logo.setMaximumSize(QSize(100, 100))
        self.regtest_logo.setStyleSheet('border:none')
        self.regtest_logo.setPixmap(QPixmap(':assets/rBitcoin.png'))

        self.grid_layout.addWidget(
            self.regtest_logo, 0, 0, 1, 1, Qt.AlignHCenter,
        )

        self.regtest_text_label = QLabel(self.regtest_frame)
        self.regtest_text_label.setObjectName('option_1_text_label')
        self.regtest_text_label.setMinimumSize(QSize(0, 30))
        self.regtest_text_label.setMaximumSize(QSize(16777215, 30))

        self.grid_layout.addWidget(
            self.regtest_text_label, 1, 0, 1, 1, Qt.AlignHCenter,
        )

        self.select_network_layout.addWidget(self.regtest_frame)

        self.mainnet_frame = ClickableFrame(
            NetworkEnumModel.MAINNET.value, self.network_selection_widget,
        )
        self.mainnet_frame.setObjectName('frame_8')
        self.mainnet_frame.setMinimumSize(QSize(220, 200))
        self.mainnet_frame.setMaximumSize(QSize(220, 200))

        self.mainnet_frame.setFrameShape(QFrame.StyledPanel)
        self.mainnet_frame.setFrameShadow(QFrame.Raised)
        self.grid_layout_2 = QGridLayout(self.mainnet_frame)
        self.grid_layout_2.setSpacing(0)
        self.grid_layout_2.setObjectName('grid_layout_2')
        self.grid_layout_2.setContentsMargins(0, 0, 0, 0)
        self.mainnet_logo_label = QLabel(self.mainnet_frame)
        self.mainnet_logo_label.setObjectName('option_1_logo_label')
        self.mainnet_logo_label.setMaximumSize(QSize(100, 100))
        self.mainnet_logo_label.setStyleSheet('border:none')
        self.mainnet_logo_label.setPixmap(QPixmap(':assets/on_chain.png'))

        self.grid_layout_2.addWidget(self.mainnet_logo_label, 0, 0, 1, 1)
        self.testnet_frame = ClickableFrame(
            NetworkEnumModel.TESTNET.value, self.network_selection_widget,
        )

        self.testnet_text_label = QLabel(self.testnet_frame)
        self.testnet_text_label.setObjectName('option_2_text_label')
        self.testnet_text_label.setMinimumSize(QSize(0, 30))
        self.testnet_text_label.setMaximumSize(QSize(16777215, 30))

        self.testnet_frame.setObjectName('option_3_frame')
        self.testnet_frame.setMinimumSize(QSize(220, 200))
        self.testnet_frame.setMaximumSize(QSize(220, 200))

        self.testnet_frame.setFrameShape(QFrame.StyledPanel)
        self.testnet_frame.setFrameShadow(QFrame.Raised)
        self.select_network_layout.addWidget(self.testnet_frame)

        self.grid_layout_3 = QGridLayout(self.testnet_frame)
        self.grid_layout_3.setSpacing(0)
        self.grid_layout_3.setObjectName('grid_layout_3')
        self.grid_layout_3.setContentsMargins(0, 0, 0, 0)
        self.testnet_logo_label = QLabel(self.testnet_frame)
        self.testnet_logo_label.setObjectName('option_3_logo_label')
        self.testnet_logo_label.setMaximumSize(QSize(100, 100))
        self.testnet_logo_label.setStyleSheet('border:none')
        self.testnet_logo_label.setPixmap(QPixmap(':assets/tBitcoin.png'))

        self.grid_layout_3.addWidget(self.testnet_logo_label, 0, 0, 1, 1)

        self.mainnet_text_label = QLabel(self.testnet_frame)
        self.mainnet_text_label.setObjectName('option_3_text_label')
        self.mainnet_text_label.setMinimumSize(QSize(0, 30))
        self.mainnet_text_label.setMaximumSize(QSize(16777215, 30))

        self.select_network_layout.addWidget(self.mainnet_frame)

        self.grid_layout_3.addWidget(
            self.testnet_text_label, 1, 0, 1, 1, Qt.AlignHCenter,
        )
        self.grid_layout_2.addWidget(
            self.mainnet_text_label, 1, 0, 1, 1, Qt.AlignHCenter,
        )

        self.regtest_note_label = QLabel()
        self.regtest_note_label.setObjectName('regtest_note_label')
        self.regtest_note_label.setWordWrap(True)
        self.regtest_note_label.setMinimumHeight(50)

        self.vertical_layout.addLayout(self.select_network_layout)

        self.vertical_spacer_3 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout.addWidget(self.regtest_note_label)
        self.vertical_layout.addItem(self.vertical_spacer_3)

        self.grid_layout_main.addWidget(
            self.network_selection_widget, 1, 1, 2, 3,
        )

        self.horizontal_spacer_2 = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.grid_layout_main.addItem(self.horizontal_spacer_2, 2, 4, 1, 1)
        self.vertical_spacer_4 = QSpacerItem(
            20, 208, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.grid_layout_main.addItem(self.vertical_spacer_4, 3, 2, 1, 1)

        self.retranslate_ui()
        self.setup_ui_connection()
        self.set_frame_click()
        self.ln_message = QApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'ln_message', 'Starting LN node',
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.title_text_1.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'select_network_type', None,
            ),
        )
        self.regtest_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'regtest', None,
            ),
        )
        self.testnet_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'testnet', None,
            ),
        )
        self.mainnet_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'mainnet', None,
            ),
        )
        self.regtest_note_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'regtest_note', None,
            ),
        )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.hide_mainnet_frame()
        self.regtest_frame.clicked.connect(self.handle_frame_click)
        self.testnet_frame.clicked.connect(self.handle_frame_click)
        self.mainnet_frame.clicked.connect(self.handle_frame_click)
        # self.select_network_close_btn.clicked.connect(
        #     lambda: close_button_navigation(self),
        # )
        self.view_model.wallet_transfer_selection_view_model.ln_node_process_status.connect(
            self.show_wallet_loading_screen,
        )
        self.view_model.wallet_transfer_selection_view_model.prev_ln_node_stopping.connect(
            self.show_wallet_loading_screen,
        )

    def handle_frame_click(self, network):
        """Handle the click event for the network frame."""
        network_enum = NetworkEnumModel(network)
        self.view_model.wallet_transfer_selection_view_model.start_node_for_embedded_option(
            network=network_enum, prev_network=self._prev_network,
        )

    def show_wallet_loading_screen(self, status, message: str | None = None):
        """This method handled show loading screen on network selection page"""
        if status is True:
            self.regtest_frame.setDisabled(True)
            self.testnet_frame.setDisabled(True)
            self.regtest_frame.setDisabled(True)
            if message is not None:
                self.__loading_translucent_screen = LoadingTranslucentScreen(
                    parent=self, description_text=message, dot_animation=True,
                )
            else:
                self.__loading_translucent_screen = LoadingTranslucentScreen(
                    parent=self, description_text=self.ln_message, dot_animation=True,
                )
            self.__loading_translucent_screen.start()

            self.__loading_translucent_screen.make_parent_disabled_during_loading(
                True,
            )

        if not status:
            self.regtest_frame.setDisabled(False)
            self.testnet_frame.setDisabled(False)
            self.regtest_frame.setDisabled(False)
            self.__loading_translucent_screen.stop()
            self.__loading_translucent_screen.make_parent_disabled_during_loading(
                False,
            )
            self.handle_close_button_visibility()
        if status is False:
            self.__loading_translucent_screen.stop()
            self.__loading_translucent_screen.make_parent_disabled_during_loading(
                False,
            )
            self.handle_close_button_visibility()

    def hide_mainnet_frame(self):
        """This method hide the mainnet wallet frame"""
        self.mainnet_frame.hide()
        self.network_selection_widget.setMinimumSize(QSize(696, 400))
        self.network_selection_widget.setMaximumSize(QSize(696, 400))

    def set_frame_click(self):
        """This method handle frame click accounting to the network"""
        self.set_current_network()
        wallet: IsWalletInitialized = SettingRepository.is_wallet_initialized()
        if self.current_network is not None and wallet.is_wallet_initialized:
            networks = {
                self.testnet_text_label.text().lower(): self.testnet_frame,
                self.regtest_text_label.text().lower(): self.regtest_frame,
                self.mainnet_text_label.text().lower(): self.mainnet_frame,
            }

            for network_name, frame in networks.items():
                frame.setDisabled(network_name == self.current_network)

    def handle_close_button_visibility(self):
        """This method handle close button visibility"""
        if self.current_network == self._prev_network:
            self.select_network_close_btn.hide()

    def set_current_network(self):
        """This method current network from the local storage"""
        try:
            self.current_network = SettingRepository.get_wallet_network().value.lower()
        except CommonException:
            self.current_network = None
