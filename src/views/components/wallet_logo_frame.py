# pylint: disable=unused-import, too-few-public-methods
"""This module contains the WalletLogoFrame classes,
which represents the WalletLogo of the application.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import NetworkEnumModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


class WalletLogoFrame(QFrame):
    """This class represents secondary button of the application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_logo()

    def set_logo(self):
        """This method used set logo."""
        self.network = SettingRepository.get_wallet_network()
        self.setObjectName('wallet_logo_frame')
        self.setMinimumSize(QSize(0, 64))
        self.setStyleSheet(
            'background: transparent;'
            'border: none;',
        )
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setObjectName('gridLayout_28')
        self.grid_layout.setContentsMargins(40, -1, -1, -1)
        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.setObjectName('horizontalLayout_14')
        self.logo_label = QLabel(self)
        self.logo_label.setObjectName('label_29')
        self.logo_label.setMinimumSize(QSize(64, 0))
        self.logo_label.setMaximumSize(QSize(64, 64))
        self.logo_label.setStyleSheet(
            'background: transparent;'
            'border: none;',
        )
        self.logo_label.setPixmap(QPixmap(':/assets/iris_logo.png'))

        self.horizontal_layout.addWidget(self.logo_label)

        self.logo_text = QLabel(self)
        self.logo_text.setObjectName('label_30')
        self.logo_text.setStyleSheet(
            'font: 24px "Inter";'
            'font-weight: 600;'
            'background:transparent;'
            'color: white',
        )

        self.horizontal_layout.addWidget(self.logo_text)

        self.grid_layout.addLayout(self.horizontal_layout, 0, 0, 1, 1)
        network_text = (
            f" {
                self.network.capitalize(
                )
            }" if self.network != NetworkEnumModel.MAINNET.value else ''
        )
        self.logo_text.setText(
            f"{QCoreApplication.translate(IRIS_WALLET_TRANSLATIONS_CONTEXT, 'iris_wallet', None)}{
                network_text
            }",
        )

        return self.logo_label, self.logo_text
