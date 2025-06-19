from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QSpacerItem
)

class HardwareWalletConnectPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_wallet = None
        self.setObjectName('hardware_wallet_connect_page')
        self.setStyleSheet(self._get_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Centered card
        card = QFrame()
        card.setObjectName('hw_card')
        card.setFixedSize(520, 420)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(24)

        # Title
        title = QLabel('Connect a hardware wallet')
        title.setObjectName('hw_title')
        card_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel('Select a hardware wallet you would like to use with this app.')
        subtitle.setObjectName('hw_subtitle')
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        # Wallet options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(24)
        self.wallets = [
            {'name': 'Ledger', 'icon': ':/assets/ledger.png'},
            {'name': 'Trezor', 'icon': ':/assets/trezor.png'},
            {'name': 'Lattice', 'icon': ':/assets/lattice.png'},
            {'name': 'QR-based', 'icon': ':/assets/qr.png'},
        ]
        self.option_buttons = []
        for wallet in self.wallets:
            btn = QFrame()
            btn.setObjectName('hw_option')
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedSize(110, 110)
            btn_layout = QVBoxLayout(btn)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Icon
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Use placeholder pixmap if asset not found
            try:
                pixmap = QPixmap(wallet['icon'])
                if pixmap.isNull():
                    raise Exception('Null pixmap')
            except:
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.gray)
            icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            btn_layout.addWidget(icon_label)
            # Name
            name_label = QLabel(wallet['name'])
            name_label.setObjectName('hw_option_name')
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_layout.addWidget(name_label)
            btn.mousePressEvent = self._make_option_click_handler(btn, wallet['name'])
            self.option_buttons.append(btn)
            options_layout.addWidget(btn)
        card_layout.addLayout(options_layout)

        # Spacer
        card_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Continue button
        self.continue_button = QPushButton('Continue')
        self.continue_button.setObjectName('hw_continue_btn')
        self.continue_button.setEnabled(False)
        card_layout.addWidget(self.continue_button)

        main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _make_option_click_handler(self, btn, wallet_name):
        def handler(event):
            for b in self.option_buttons:
                b.setProperty('selected', False)
                b.setStyleSheet("")
            btn.setProperty('selected', True)
            btn.setStyleSheet("")
            self.selected_wallet = wallet_name
            self.continue_button.setEnabled(True)
        return handler

    def _get_stylesheet(self):
        return """
        #hardware_wallet_connect_page {
            background-color: #101426;
        }
        #hw_card {
            background-color: #1B233B;
            border-radius: 12px;
        }
        #hw_title {
            color: #fff;
            font: 24px 'Inter';
            font-weight: 600;
            margin-bottom: 4px;
        }
        #hw_subtitle {
            color: #E6E1E5;
            font: 16px 'Inter';
            font-weight: 400;
            margin-bottom: 12px;
        }
        #hw_option {
            background-color: #030B25;
            border-radius: 8px;
            border: 2px solid transparent;
            transition: border 0.2s;
        }
        #hw_option[selected="true"] {
            border: 2px solid #5B8DEF;
            background-color: #16204A;
        }
        #hw_option:hover {
            border: 2px solid #5B8DEF;
        }
        #hw_option_name {
            color: #fff;
            font: 15px 'Inter';
            font-weight: 500;
            margin-top: 8px;
        }
        #hw_continue_btn {
            background-color: #3949AB;
            color: #fff;
            font: 16px 'Inter';
            font-weight: 600;
            border-radius: 8px;
            padding: 10px 0;
            margin-top: 16px;
        }
        #hw_continue_btn:disabled {
            background-color: #232A4A;
            color: #888;
        }
        """ 