# rgb_wallet_ui.py
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QStackedWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

APP_STYLE = """
QWidget {
    background-color: #030B25;
    font-family: 'Segoe UI';
    color: #ffffff;
    border: none;
    margin: 0;
    padding: 0;
}

QLabel {
    font-size: 16px;
    color: white;
    border: none;
}

QLabel[heading="true"] {
    font-size: 20px;
    font-weight: bold;
}

QPushButton {
    background-color: #333333;
    border: 2px solid #ffffff;
    border-radius: 5px;
    padding: 8px 20px;
    font-size: 14px;
    color: white;
}

QPushButton:hover {
    background-color: #444444;
}

QPushButton:pressed {
    background-color: #555555;
}

QFrame {
    border-radius: 12px;
    background-color: #030B25;
    border: none;
    padding: 20px;
}

QFrame#CardFrame {
    border: 5px solid #798094;
    background-color: transparent;
    padding: 15px;
}

QFrame#CardFrame:hover{
    border: 5px solid #ffffff;
}

QFrame#InfoFrame {
    border-radius: 12px;
    background-color: #030B25;
    border: 1px solid #aaaaaa;
    padding: 20px;
    margin-top: 70px;
    width: 90%;
}

QLabel#InfoLabel {
    font-size: 15px;
    color: #dddddd;
}

QStackedWidget {
    background: #030B25;
}

QPushButton#BackButton {
    width: 120px;
}

QWidget#SelectionScreen, QWidget#ResultScreen {
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    padding: 20px;
}
"""


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


class ClickableCard(QWidget):
    def __init__(self, image_path, label_text, on_click):
        super().__init__()
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Outer layout for the card (still a QVBoxLayout to hold the frame)
        outer_layout = QVBoxLayout()

        # Create the frame that will hold the image and text
        frame = QFrame()
        frame.setObjectName('CardFrame')
        frame.setFixedSize(QSize(250, 300))  # Fixed size for the frame

        # Using QGridLayout for precise control over widget positioning
        frame_layout = QGridLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Create the image label
        image = QLabel()
        pixmap = QPixmap(resource_path(image_path))
        image.setPixmap(pixmap)
        # Allow the pixmap to scale within the label
        image.setScaledContents(True)
        image.setMaximumSize(160, 160)  # Set a maximum visible area
        image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Center the image within the grid
        image.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Create the text label
        text = QLabel(label_text)
        text.setAlignment(Qt.AlignCenter)  # Center the text

        # Add the image and text to the grid layout
        frame_layout.addWidget(image, 0, 0, 1, 1, Qt.AlignCenter)
        frame_layout.addWidget(text, 1, 0, 1, 1, Qt.AlignCenter)

        # Set the layout for the frame
        frame.setLayout(frame_layout)

        # Add the frame to the outer layout
        outer_layout.addWidget(frame)

        # Set the outer layout for the widget
        self.setLayout(outer_layout)

        # Handle click event
        self.mousePressEvent = lambda event: on_click()


class MultiStageSelection(QWidget):
    def __init__(self, stacked_widget, on_final_selection):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.on_final_selection = on_final_selection
        self.reset()

        self.label = QLabel('')
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setProperty('heading', True)

        self.central_frame = QFrame()
        central_layout = QVBoxLayout(self.central_frame)
        central_layout.setAlignment(Qt.AlignCenter)

        central_layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding,
            ),
        )
        central_layout.setContentsMargins(0, 0, 0, 40)
        central_layout.addWidget(self.label)

        self.column = QVBoxLayout()
        self.column.setAlignment(Qt.AlignHCenter)
        central_layout.addLayout(self.column)

        # Container for cards to ensure centering
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet('background-color: transparent;')
        self.row = QHBoxLayout()
        self.row.setAlignment(Qt.AlignCenter)
        self.cards_container.setLayout(self.row)

        # Add container to the column layout
        self.column.addWidget(self.cards_container, alignment=Qt.AlignCenter)

        self.info_frame = QFrame(self.central_frame)
        self.info_frame.setObjectName('InfoFrame')
        self.info_frame.setFixedSize(QSize(550, 300))
        self.info_frame.setVisible(False)

        info_layout = QVBoxLayout(self.info_frame)
        self.info_label = QLabel('')
        self.info_label.setObjectName('InfoLabel')
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)

        self.continue_button = QPushButton('Continue')
        self.continue_button.setFixedWidth(120)
        self.continue_button.clicked.connect(self.continue_stage)
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))
        info_layout.addWidget(self.continue_button, alignment=Qt.AlignCenter)

        self.column.addWidget(self.info_frame)
        central_layout.addItem(
            QSpacerItem(
                20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding,
            ),
        )

        self.back_button = QPushButton('Back')
        self.back_button.clicked.connect(self.go_back)
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        back_layout.addWidget(self.back_button)
        back_layout.addStretch()
        central_layout.addLayout(back_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.central_frame)
        self.setLayout(layout)

        self.setup_stage()

    def reset(self):
        self.stage = 0
        self.mode = None
        self.has_key = None
        self.wallet_action = None
        self.key_storage = None

    def clear_cards(self):
        for i in reversed(range(self.row.count())):
            item = self.row.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

    def setup_stage(self):
        self.clear_cards()
        self.info_frame.setVisible(False)
        self.back_button.setVisible(self.stage > 0)

        if self.stage == 0:
            self.label.setText('Select Wallet Mode')
            options = [
                ('Online', 'src/assets/online.png'),
                ('Offline', 'src/assets/offline.png'),
            ]
            for text, img in options:
                self.row.addWidget(
                    ClickableCard(
                        img, text, lambda t=text: self.select_mode(t),
                    ),
                )

        elif self.stage == 1:
            if self.mode == 'Offline':
                return  # should never reach here for offline; safeguard
            self.label.setText(
                f"<b>{self.mode}</b> mode — Choose Access Type:",
            )
            options = [
                ('With Private Key', 'src/assets/key.png', True),
                ('Watch-Only', 'src/assets/eye_icon.png', False),
            ]
            for text, img, has_key in options:
                self.row.addWidget(
                    ClickableCard(
                        img, text, lambda t=text, hk=has_key: self.select_key_type(
                            t, hk,
                        ),
                    ),
                )

        elif self.stage == 2:
            self.label.setText('Choose Wallet Action')
            options = [
                ('Create New Wallet', 'src/assets/create_wallet.png'),
                ('Load Existing Wallet', 'src/assets/loading.png'),
            ]
            for text, img in options:
                self.row.addWidget(
                    ClickableCard(
                        img, text, lambda t=text: self.select_wallet_action(t),
                    ),
                )

        elif self.stage == 3:
            self.label.setText('Where should the private key be stored?')
            options = [
                ('On Device', 'src/assets/desktop.png'),
                ('Hardware Wallet', 'src/assets/hw.png'),
            ]
            for text, img in options:
                self.row.addWidget(
                    ClickableCard(
                        img, text, lambda t=text: self.select_key_storage(t),
                    ),
                )

    def select_mode(self, mode):
        self.mode = mode
        self.info_label.setText(
            f"<b>{mode} Mode</b><br><br>" +
            (
                '🌐 Full-featured wallet with signing & broadcasting.<br>✅ Suitable for daily use.'
                if mode == 'Online'
                else '🛡️ Secure wallet.<br>📝 Sign PSBTs offline.<br>❄️ Ideal for cold storage.'
            ),
        )
        self.info_frame.setVisible(True)

    def select_key_type(self, text, has_key):
        self.has_key = has_key
        if has_key:
            if self.mode == 'Online':
                broadcast_line = '📤 Broadcast enabled'
            else:
                broadcast_line = '🚫 Cannot broadcast (offline mode)'
            self.info_label.setText(
                f"<b>Wallet with Private Key</b><br><br>"
                '🔐 Full control over funds<br>'
                '✍️ Sign transactions<br>'
                f"{broadcast_line}<br>",
            )
        else:
            if self.mode == 'Online':
                broadcast_line = '📤 Can broadcast signed PSBTs'
            else:
                broadcast_line = '🚫 Cannot broadcast (offline mode)'

            self.info_label.setText(
                f"<b>Watch-Only Wallet</b><br><br>"
                '👁️ View balances & transaction history<br>'
                f"{broadcast_line}<br>"
                '🚫 Cannot create or sign transactions<br>'
                '🔒 No private key involved',
            )

        self.info_frame.setVisible(True)

    def select_wallet_action(self, action):
        self.wallet_action = action
        if action == 'Create New Wallet':
            self.info_label.setText(
                f"<b>Create New Wallet</b><br><br>"
                '🆕 Generate a fresh wallet and private key<br>'
                '🧠 You’ll get a recovery phrase (mnemonic or xpub)',
            )
        elif action == 'Load Existing Wallet':
            self.info_label.setText(
                f"<b>Load Existing Wallet</b><br><br>"
                '📂 Restore wallet using mnemonic or xpub key<br>'
                '🔄 Continue with access setup',
            )
        self.info_frame.setVisible(True)

    def select_key_storage(self, storage):
        self.key_storage = storage
        if storage == 'On Device':
            self.info_label.setText(
                f"<b>🔐 {storage}</b><br><br>"
                '💾 Private key stored securely on this device<br>'
                '✅ Full control, local signing enabled',
            )
        elif storage == 'Hardware Wallet':
            self.info_label.setText(
                f"<b>🔐 {storage}</b><br><br>"
                '🧱 Private key stays on hardware wallet<br>'
                '🔌 Connect device when signing is needed<br>'
                '🛡️ Enhanced physical security',
            )
        self.info_frame.setVisible(True)

    def continue_stage(self):
        if self.stage == 0 and self.mode:
            if self.mode == 'Offline':
                self.has_key = False  # force watch-only for offline
                self.stage = 2        # skip key selection, go to wallet action
            else:
                self.stage = 1

        elif self.stage == 1 and self.has_key is not None:
            if self.has_key:
                self.stage = 2
            else:
                self.on_final_selection(self.mode, self.has_key, None, None)
                return
        elif self.stage == 2 and self.wallet_action:
            self.stage = 3
        elif self.stage == 3 and self.key_storage:
            self.on_final_selection(
                self.mode, self.has_key, self.wallet_action, self.key_storage,
            )
            return
        self.setup_stage()

    def go_back(self):
        if self.stage > 0:
            # Special case: skip stage 1 if we're in Offline mode
            if self.stage == 2 and self.mode == 'Offline':
                self.stage = 0
                self.reset()
            else:
                self.stage -= 1
                if self.stage == 0:
                    self.reset()
            self.setup_stage()

        else:
            self.stacked_widget.setCurrentIndex(0)


class ResultScreen(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget

        # Outer layout
        outer_layout = QVBoxLayout()
        outer_layout.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel('Wallet Summary')
        title.setProperty('heading', True)
        title.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(title)

        # Centering container for label
        label_container = QWidget()
        label_layout = QVBoxLayout()
        label_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel('')
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)  # Center text horizontally
        # Optional: make text selectable
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setStyleSheet('font-size: 16px;')
        label_layout.addWidget(self.label)

        label_container.setLayout(label_layout)
        outer_layout.addWidget(label_container, alignment=Qt.AlignCenter)

        # Back button
        back = QPushButton('Back')
        back.setCursor(QCursor(Qt.PointingHandCursor))
        back.clicked.connect(self.go_back)
        outer_layout.addWidget(back, alignment=Qt.AlignCenter)

        self.setLayout(outer_layout)

    def show_result(self, mode, has_key, wallet_action, key_storage):
        if not has_key:
            content = f"<b>{mode} Watch-Only Wallet</b><br>"
            content += '👁️ View balances & transaction history<br>'

            if mode == 'Online':
                content += '📥 Import signed PSBT<br>'
                content += '📤 Broadcast signed PSBT<br>'
            else:
                content += '🚫 Cannot import signed PSBT<br>'
                content += '🚫 Cannot broadcast<br>'

            content += '🚫 Cannot create or sign transactions<br>'
            content += '🔒 No private key access'

        else:
            # Wallet with Private Key
            content = (
                f"<b>{mode} Wallet with Private Key</b><br>"
                f"⚙️ Action: <b>{wallet_action}</b><br>"
                f"🔐 Key Storage: <b>{key_storage}</b><br><br>"
            )

            if key_storage == 'On Device':
                content += (
                    '💾 Private key stored securely on device<br>'
                    '✍️ Allows direct signing of transactions<br>'
                    '📡 Broadcast supported directly'
                )
            elif key_storage == 'Hardware Wallet':
                content += (
                    '🧱 Private key secured on hardware wallet<br>'
                    '🔌 Requires connection for signing<br>'
                    '🛡️ Enhanced physical security'
                )

            if mode == 'Offline':
                content += (
                    '<br><br>📤 Can create and sign PSBTs<br>'
                    '🌐 No broadcasting (requires Online Mode)<br>'
                    '🔁 Export signed PSBT to Online wallet for broadcasting'
                )
            elif mode == 'Online':
                content += (
                    '<br><br>🧠 Full-featured access: Create, Sign & Broadcast<br>'
                    '🌐 Direct network access enabled'
                )

        self.label.setText(content)

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)


def run_app():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    stacked_widget = QStackedWidget()
    stacked_widget.setWindowTitle('RGB Wallet')

    result_screen = ResultScreen(stacked_widget)

    def handle_final_selection(mode, has_key, wallet_action, key_storage):
        result_screen.show_result(mode, has_key, wallet_action, key_storage)
        stacked_widget.setCurrentWidget(result_screen)

    selection_screen = MultiStageSelection(
        stacked_widget, handle_final_selection,
    )

    stacked_widget.addWidget(selection_screen)
    stacked_widget.addWidget(result_screen)
    stacked_widget.showMaximized()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_app()
