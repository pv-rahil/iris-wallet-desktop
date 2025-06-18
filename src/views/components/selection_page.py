# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the WalletSelectionWidget class,
which represents the UI for wallet selection methods.
"""
from __future__ import annotations

from PySide6.QtCore import Property
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QEasingCurve
from PySide6.QtCore import QEvent
from PySide6.QtCore import QPropertyAnimation
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletEntryType
from src.model.enums.enums_model import WalletSecurityType
from src.model.enums.enums_model import WalletType
from src.model.selection_page_model import SelectionPageModel
from src.utils.clickable_frame import ClickableFrame
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import load_stylesheet
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
# from accessible_constant import OPTION_1_FRAME
# from accessible_constant import OPTION_2_FRAME
# from accessible_constant import WALLET_OR_TRANSFER_SELECTION_CLOSE_BUTTON
# from accessible_constant import WALLET_OR_TRANSFER_SELECTION_CONTINUE_BUTTON


class SelectionPage(QWidget):
    """This class represents all the UI elements of the selection page."""

    selection_changed = Signal(str, str)  # title, logo

    def __init__(self, view_model, params):
        super().__init__()
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/wallet_selection_style.qss',
            ),
        )
        self._view_model: MainViewModel = view_model
        self._params: SelectionPageModel = params
        self.selected_frame = None
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setObjectName('grid_layout')
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.horizontal_spacer_1 = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.grid_layout.addItem(self.horizontal_spacer_1, 1, 0, 1, 1)

        self.widget_page = QWidget(self)
        self.widget_page.setObjectName('widget_page')
        self.widget_page.setMinimumSize(QSize(736, 400))
        self.widget_page.setMaximumSize(QSize(736, 600))

        self.vertical_layout = QVBoxLayout(self.widget_page)
        self.vertical_layout.setSpacing(4)
        self.vertical_layout.setObjectName('vertical_layout_9')
        self.vertical_layout.setContentsMargins(1, 5, 1, 5)
        self.header_line = QFrame(self.widget_page)
        self.header_line.setObjectName('line_2')
        self.header_line.setFrameShape(QFrame.Shape.HLine)
        self.header_line.setFrameShadow(QFrame.Shadow.Sunken)
        self.header_line.hide()  # Hide by default

        self.vertical_layout.addWidget(self.header_line)
        self.header_horizontal_layout = QHBoxLayout()
        self.header_horizontal_layout.setObjectName('header_horizontal_layout')
        self.header_horizontal_layout.setContentsMargins(0, 0, 25, 0)

        self.title_text = QLabel(self.widget_page)
        self.title_text.setObjectName('title_text')
        self.title_text.setMinimumSize(QSize(0, 50))
        self.title_text.setMaximumSize(QSize(16777215, 50))
        self.title_text.setCursor(QCursor(Qt.PointingHandCursor))
        self.title_text.installEventFilter(self)

        self.header_horizontal_layout.addWidget(self.title_text)

        self.close_button = QPushButton(self.widget_page)
        self.close_button.setObjectName('close_button')
        # self.close_button.setAccessibleName(
        #     WALLET_OR_TRANSFER_SELECTION_CLOSE_BUTTON,
        # )
        self.close_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_button.setMinimumSize(QSize(24, 24))
        self.close_button.setMaximumSize(QSize(50, 65))
        self.close_button.setAutoFillBackground(False)

        close_icon = QIcon()
        close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(), QIcon.Normal, QIcon.Off,
        )
        self.close_button.setIcon(close_icon)
        self.close_button.setIconSize(QSize(24, 24))
        self.close_button.setCheckable(False)
        self.close_button.setChecked(False)
        self.header_horizontal_layout.addWidget(self.close_button)

        self.vertical_layout.addLayout(self.header_horizontal_layout)

        self.vertical_spacer_2 = QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout.addItem(self.vertical_spacer_2)

        self.select_option_layout = QHBoxLayout()
        self.select_option_layout.setObjectName('select_option_layout')
        self.select_option_layout.setContentsMargins(42, 0, 0, 0)
        self.select_option_layout.setSpacing(40)
        self.option_1_frame = ClickableFrame(
            self._params.logo_1_title,
        )
        self.option_1_frame.setObjectName('option_1_frame')
        # self.option_1_frame.setAccessibleName(OPTION_1_FRAME)
        self.option_1_frame.setMinimumSize(QSize(300, 200))
        self.option_1_frame.setMaximumSize(QSize(300, 200))

        self.option_1_frame.setFrameShape(QFrame.StyledPanel)
        self.option_1_frame.setFrameShadow(QFrame.Raised)
        self.option_1_frame_grid_layout = QGridLayout(self.option_1_frame)
        self.option_1_frame_grid_layout.setSpacing(0)
        self.option_1_frame_grid_layout.setObjectName('gridLayout_27')
        self.option_1_frame_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.option_2_logo = QLabel(self.option_1_frame)
        self.option_2_logo.setObjectName('option_2_logo')
        self.option_2_logo.setMinimumSize(QSize(100, 100))
        self.option_2_logo.setMaximumSize(QSize(100, 100))
        self.option_2_logo.setStyleSheet('border:none')
        self.option_2_logo.setPixmap(QPixmap(self._params.logo_1_path))
        # Allow the pixmap to scale within the label
        self.option_2_logo.setScaledContents(True)
        self.option_2_logo.setMaximumSize(
            100, 100,
        )  # Set a maximum visible area
        self.option_2_logo.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding,
        )
        self.option_2_logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.option_1_frame_grid_layout.addWidget(
            self.option_2_logo, 0, 0, 1, 1, Qt.AlignHCenter,
        )

        self.option_1_text_label = QLabel(self.option_1_frame)
        self.option_1_text_label.setObjectName('option_1_text_label')
        self.option_1_text_label.setMinimumSize(QSize(0, 30))
        self.option_1_text_label.setMaximumSize(QSize(16777215, 30))

        self.option_1_frame_grid_layout.addWidget(
            self.option_1_text_label, 1, 0, 1, 1, Qt.AlignHCenter,
        )

        self.select_option_layout.addWidget(self.option_1_frame, Qt.AlignLeft)

        self.option_2_frame = ClickableFrame(
            self._params.logo_2_title, self.widget_page,
        )
        self.option_2_frame.setObjectName('option_2_frame')
        # self.option_2_frame.setAccessibleName(OPTION_2_FRAME)
        self.option_2_frame.setMinimumSize(QSize(300, 200))
        self.option_2_frame.setMaximumSize(QSize(300, 200))

        self.option_2_frame.setFrameShape(QFrame.StyledPanel)
        self.option_2_frame.setFrameShadow(QFrame.Raised)
        self.option_2_frame_grid_layout = QGridLayout(self.option_2_frame)
        self.option_2_frame_grid_layout.setSpacing(0)
        self.option_2_frame_grid_layout.setObjectName('grid_layout_28')
        self.option_2_frame_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.option_1_logo_label = QLabel(self.option_2_frame)
        self.option_1_logo_label.setObjectName('option_1_logo_label')
        self.option_1_logo_label.setMaximumSize(QSize(100, 100))
        self.option_1_logo_label.setStyleSheet('border:none')
        self.option_1_logo_label.setPixmap(QPixmap(self._params.logo_2_path))
        # Allow the pixmap to scale within the label
        self.option_1_logo_label.setScaledContents(True)
        self.option_1_logo_label.setMaximumSize(
            100, 100,
        )  # Set a maximum visible area
        self.option_1_logo_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding,
        )
        self.option_1_logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.option_2_frame_grid_layout.addWidget(
            self.option_1_logo_label, 0, 0, 1, 1,
        )

        self.option_2_text_label = QLabel(self.option_2_frame)
        self.option_2_text_label.setObjectName('option_2_text_label')
        self.option_2_text_label.setMinimumSize(QSize(0, 30))
        self.option_2_text_label.setMaximumSize(QSize(16777215, 30))

        self.option_2_frame_grid_layout.addWidget(
            self.option_2_text_label, 1, 0, 1, 1, Qt.AlignHCenter,
        )

        self.select_option_layout.addWidget(self.option_2_frame, Qt.AlignLeft)

        self.vertical_layout.addLayout(self.select_option_layout)

        self.vertical_spacer_5 = QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.horizontal_spacer_3 = QSpacerItem(
            265, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.select_option_layout.addSpacerItem(self.horizontal_spacer_3)

        self.info_frame = QFrame(self.widget_page)
        self.info_frame.setObjectName('info_frame')
        self.info_frame.setMinimumSize(QSize(645, 80))
        self.info_frame.setMaximumSize(QSize(645, 80))
        self.info_frame.hide()

        self.info_frame_layout = QHBoxLayout(self.info_frame)
        self.info_frame_layout.setContentsMargins(20, 0, 20, 0)
        self.info_frame_layout.setSpacing(10)
        self.wallet_connection_info_label = QLabel(self.info_frame)
        self.wallet_connection_info_label.setObjectName(
            'wallet_connection_info_label',
        )
        self.wallet_connection_info_label.setWordWrap(True)
        self.info_frame_layout.addWidget(self.wallet_connection_info_label)

        self.continue_button = PrimaryButton()
        # self.continue_button.setAccessibleName(
        #     WALLET_OR_TRANSFER_SELECTION_CONTINUE_BUTTON,
        # )
        self.info_frame_layout.addWidget(self.continue_button)
        self.info_frame_wrapper = QHBoxLayout()
        self.info_frame_wrapper.setContentsMargins(42, 0, 0, 0)
        self.info_frame_wrapper.addStretch()
        self.info_frame_wrapper.addWidget(self.info_frame)
        self.horizontal_spacer_4 = QSpacerItem(
            265, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.info_frame_wrapper.addSpacerItem(self.horizontal_spacer_4)
        self.info_frame_wrapper.addStretch()
        self.vertical_spacer_6 = QSpacerItem(
            10, 35, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed,
        )
        self.vertical_layout.addSpacerItem(self.vertical_spacer_6)
        self.vertical_layout.addLayout(self.info_frame_wrapper)
        self.vertical_spacer_3 = QSpacerItem(
            20, 35, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed,
        )

        self.vertical_layout.addItem(self.vertical_spacer_3)

        self.grid_layout.addWidget(self.widget_page, 1, 1)
        self.grid_layout.addItem(self.vertical_spacer_5, 3, 1)

        self.horizontal_spacer_2 = QSpacerItem(
            268, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.grid_layout.addItem(self.horizontal_spacer_2, 2, 4, 1, 1)

        self.vertical_spacer_4 = QSpacerItem(
            20, 283, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.grid_layout.addItem(self.vertical_spacer_4, 5, 2, 1, 1)
        # self.adjust_size()
        self.retranslate_ui()
        self.setup_ui_connection()
        # Select option 1 by default and show info frame
        self.selected_frame = self._params.logo_1_title
        self.on_click_frame(self._params.logo_1_title, True)
        self.info_frame.show()
        self._set_text_for_frame_info(self._params.logo_1_title)

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.title_text.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self._params.title, None,
            ),
        )
        self.option_1_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self._params.logo_1_title, None,
            ),
        )
        self.option_2_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, self._params.logo_2_title, None,
            ),
        )
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue', None,
            ),
        )

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.option_1_frame.clicked.connect(self.handle_frame_click)
        self.option_2_frame.clicked.connect(self.handle_frame_click)
        self.close_button.clicked.connect(
            self._view_model.page_navigation.term_and_condition_page,
        )
        self.continue_button.clicked.connect(self.on_click_continue)

    def handle_frame_click(self, _id):
        """Handles frame click"""
        if self.selected_frame == _id:
            return
        self.info_frame.show()
        self._set_text_for_frame_info(_id)
        if self.selected_frame is not None:
            self.on_click_frame(self.selected_frame, False)
        self.on_click_frame(_id, True)
        self.selected_frame = _id
        # Emit the signal with the new title and logo
        if _id == self._params.logo_1_title:
            self.selection_changed.emit(
                self._params.logo_1_title, self._params.logo_1_path,
            )
        elif _id == self._params.logo_2_title:
            self.selection_changed.emit(
                self._params.logo_2_title, self._params.logo_2_path,
            )

    def _set_text_for_frame_info(self, _id):
        """This method sets the text for the information label for the selected frame."""
        if _id == self._params.logo_1_title:
            self.wallet_connection_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, self._params.logo_1_info, None,
                ),
            )

        elif _id == self._params.logo_2_title:
            self.wallet_connection_info_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, self._params.logo_2_info, None,
                ),
            )

    def close_button_navigation(self):
        """
        Handles navigation to the previous page.
        """

    def on_click_frame(self, _id, is_selected: bool):
        """Handles frame click styling."""
        if is_selected:
            if _id == self._params.logo_1_title:
                self.option_1_frame.setStyleSheet(
                    load_stylesheet(
                        'views/qss/style.qss',
                    ),
                )
            elif _id == self._params.logo_2_title:
                self.option_2_frame.setStyleSheet(
                    load_stylesheet(
                        'views/qss/style.qss',
                    ),
                )

        else:
            if _id == self._params.logo_1_title:
                self.option_1_frame.setStyleSheet(
                    load_stylesheet(
                        'views/qss/wallet_selection_style.qss',
                    ),
                )
            elif _id == self._params.logo_2_title:
                self.option_2_frame.setStyleSheet(
                    load_stylesheet(
                        'views/qss/wallet_selection_style.qss',
                    ),
                )

    def on_click_continue(self):
        """Handles continue button click."""
        if self.selected_frame == WalletType.ONLINE_TYPE_WALLET.value:
            SettingRepository.set_wallet_type(WalletType.ONLINE_TYPE_WALLET)
        elif self.selected_frame == WalletType.OFFLINE_TYPE_WALLET.value:
            SettingRepository.set_wallet_type(WalletType.OFFLINE_TYPE_WALLET)
        elif self.selected_frame == WalletSecurityType.WITH_PRIVATE_KEY.value:
            SettingRepository.set_wallet_security_type(
                WalletSecurityType.WITH_PRIVATE_KEY,
            )
        elif self.selected_frame == WalletSecurityType.WATCH_ONLY.value:
            SettingRepository.set_wallet_security_type(
                WalletSecurityType.WATCH_ONLY,
            )
        elif self.selected_frame == WalletEntryType.CREATE.value:
            SettingRepository.set_wallet_entry_type(WalletEntryType.CREATE)
        elif self.selected_frame == WalletEntryType.LOAD.value:
            SettingRepository.set_wallet_entry_type(WalletEntryType.LOAD)
        elif self.selected_frame == KeyStorageType.ON_DEVICE.value:
            SettingRepository.set_key_storage_type(KeyStorageType.ON_DEVICE)
        elif self.selected_frame == KeyStorageType.HARDWARE_WALLET.value:
            SettingRepository.set_key_storage_type(
                KeyStorageType.HARDWARE_WALLET,
            )

    def adjust_size(self):
        """This method adjusts the size of the card"""
        self.widget_page.setMinimumSize(QSize(580, 450))
        self.widget_page.setMaximumSize(QSize(580, 560))
        self.option_1_frame.setMinimumSize(QSize(224, 204))
        self.option_1_frame.setMaximumSize(QSize(224, 204))
        self.option_2_frame.setMinimumSize(QSize(224, 204))
        self.option_2_frame.setMaximumSize(QSize(224, 204))

    def reset_selection(self):
        """This method reset the selection"""
        # Reset the selection to initial state (select first option by default)
        self.selected_frame = self._params.logo_1_title
        self.on_click_frame(self._params.logo_1_title, True)
        self.info_frame.show()
        self._set_text_for_frame_info(self._params.logo_1_title)

    def clear_all_types(self):
        """Clear all stored wallet types."""
        SettingRepository.set_wallet_type(None)
        SettingRepository.set_wallet_security_type(None)
        SettingRepository.set_wallet_entry_type(None)
        SettingRepository.set_key_storage_type(None)
