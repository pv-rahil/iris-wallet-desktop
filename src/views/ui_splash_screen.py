# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""This module contains the SplashScreenWidget class,
which represents the UI for splash screen.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import SYNCING_CHAIN_LABEL_TIMER
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel


class SplashScreenWidget(QWidget):
    """This class represents all the UI elements of the splash screen."""

    def __init__(self, view_model):
        self.render_timer = RenderTimer(task_name='SplashScreenWidget')
        self.render_timer.start()
        super().__init__()
        self.setObjectName('splash_page')
        self._view_model: MainViewModel = view_model
        self.syncing_chain_label_timer = QTimer(self)
        self.syncing_chain_label_timer.setSingleShot(True)
        self.main_grid_layout = QGridLayout(self)
        self.network = SettingRepository.get_wallet_network().value
        self.main_grid_layout.setObjectName('main_grid_layout')
        self.main_grid_layout.setContentsMargins(1, 1, 1, 1)
        self.vertical_spacer = QSpacerItem(
            20, 164, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.main_grid_layout.addItem(self.vertical_spacer, 0, 2, 1, 1)

        self.horizontal_spacer = QSpacerItem(
            228, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.main_grid_layout.addItem(self.horizontal_spacer, 1, 0, 1, 1)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName('main_frame')
        self.main_frame.setFrameShape(QFrame.StyledPanel)
        self.main_frame.setFrameShadow(QFrame.Raised)
        self.main_frame.setStyleSheet('border: none')
        self.frame_vertical_layout = QVBoxLayout(self.main_frame)
        self.frame_vertical_layout.setObjectName('frame_vertical_layout')

        self.logo_text_label = QLabel(self.main_frame)
        self.logo_text_label.setObjectName('logo_text_label')
        self.logo_text_label.setStyleSheet(
            'QLabel#logo_text_label,#note_text_label{\n'
            "font: 24px \"Inter\";\n"
            'font-weight: 600;\n'
            'color: white\n'
            '}',
        )

        self.note_text_label = QLabel(self.main_frame)
        self.note_text_label.setObjectName('note_text_label')

        self.spinner_label = QLabel(self.main_frame)
        self.spinner_label.setMinimumSize(200, 200)
        self.spinner_label.setMaximumSize(200, 200)

        # Set transparent background
        self.setStyleSheet('background:transparent;')

        # Load spinner image
        # Ensure this path is correct
        self.pixmap = QPixmap(':/assets/logo_large.png')
        self.angle = 0

        # Set timer to rotate the spinner
        self.timer = QTimer(self)
        self.timer.setInterval(50)  # Rotate every 50 ms
        self.timer.timeout.connect(self.rotate_spinner)
        self.timer.start()

        self.frame_vertical_layout.addWidget(
            self.spinner_label, 0, Qt.AlignHCenter,
        )
        self.frame_vertical_layout.addWidget(
            self.logo_text_label, 0, Qt.AlignHCenter,
        )
        self.frame_vertical_layout.addWidget(
            self.note_text_label, 0, Qt.AlignHCenter,
        )
        self.main_grid_layout.addWidget(self.main_frame, 1, 1, 2, 2)

        self.horizontal_spacer_2 = QSpacerItem(
            228, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.main_grid_layout.addItem(self.horizontal_spacer_2, 2, 3, 1, 1)

        self.vertical_spacer_2 = QSpacerItem(
            20, 164, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )

        self.main_grid_layout.addItem(self.vertical_spacer_2, 3, 1, 1, 1)
        self._view_model.splash_view_model.sync_chain_info_label.connect(
            self.set_sync_chain_info_label,
        )
        self._view_model.splash_view_model.splash_screen_message.connect(
            self.set_message_text,
        )
        self.retranslate_ui()
        self.on_page_load()

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        network_text = (
            f" {
                self.network.capitalize(
                )
            }" if self.network != NetworkEnumModel.MAINNET.value else ''
        )
        self.logo_text_label.setText(
            f"{QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'iris_wallet', None)}{
                network_text
            }",
        )
        self.note_text_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'auth_message', None,
            ),
        )

    def on_page_load(self):
        """Method run when page load"""
        self._view_model.splash_view_model.is_login_authentication_enabled()

    def rotate_spinner(self):
        """This method rotate the iris logo"""
        self.angle = (self.angle + 10) % 360
        transform = QTransform().rotate(self.angle)
        rotated_pixmap = self.pixmap.transformed(
            transform, Qt.SmoothTransformation,
        )
        scaled_pixmap = rotated_pixmap.scaled(
            self.spinner_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        self.spinner_label.setPixmap(scaled_pixmap)

    def set_message_text(self, message):
        """This method set text for the splash screen message"""
        self.note_text_label.setText(message)

    def set_sync_chain_info_label(self):
        """This method sets the sync chain label for the splash screen message if unlock takes more than 5 sec"""
        self.syncing_chain_label_timer.start(SYNCING_CHAIN_LABEL_TIMER)
        self.syncing_chain_label_timer.timeout.connect(
            lambda: self.note_text_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'syncing_chain_info', None,
                ),
            ),
        )
