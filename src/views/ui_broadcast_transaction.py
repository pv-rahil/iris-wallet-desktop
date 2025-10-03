# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
"""
Widget for broadcasting signed transactions (PSBTs) in the application.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import WalletSignatureType
import src.resources_rc
from accessible_constant import BROADCAST_TRANSACTION_METHOD_SELECTOR, BROADCAST_TRANSACTION_PAGE_BUTTON, BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON, BROADCAST_TRANSACTION_PSBT_INPUT, SIGN_PSBT_PAGE_BUTTON
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import ToastPreset
from src.utils.common_utils import get_current_wallet_mode_config
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame


class BroadcastTransactionWidget(QWidget):
    """
    Widget for broadcasting signed transactions (PSBTs) in the application.
    """

    def __init__(self, view_model, from_sidebar: bool = False):
        """
        Initialize the BroadcastTransactionWidget.
        """
        super().__init__()
        self.sidebar = None
        self.render_timer = RenderTimer(
            task_name='Broadcast Transaction Rendering',
        )
        self._view_model: MainViewModel = view_model
        self.from_sidebar = from_sidebar
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/broadcast_transaction_style.qss',
            ),
        )
        config = get_current_wallet_mode_config()
        self.priv = config.privileges
        self._is_multisig = (
            SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG
        )

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setObjectName('grid_layout')
        self.wallet_logo_frame = WalletLogoFrame(self)
        self.grid_layout.addWidget(self.wallet_logo_frame, 0, 0, 1, 1)

        self.broadcast_transaction_vertical_spacer_1 = QSpacerItem(
            20, 61, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.grid_layout.addItem(
            self.broadcast_transaction_vertical_spacer_1, 0, 2, 1, 1,
        )

        self.broadcast_transaction_widget = QWidget(self)
        self.broadcast_transaction_widget.setObjectName(
            'broadcast_transaction_widget',
        )
        # Wider card for multisig to match reference
        if self._is_multisig:
            self.broadcast_transaction_widget.setMinimumSize(QSize(800, 520))
            self.broadcast_transaction_widget.setMaximumSize(QSize(800, 520))
        else:
            self.broadcast_transaction_widget.setMinimumSize(QSize(630, 450))
            self.broadcast_transaction_widget.setMaximumSize(QSize(630, 450))
        self.vertical_layout = QVBoxLayout(self.broadcast_transaction_widget)
        self.vertical_layout.setObjectName('verticalLayout')
        # Multisig: tighten and equalize inner paddings similar to reference
        if self._is_multisig:
            self.vertical_layout.setContentsMargins(22, 12, 22, 16)
        self.vertical_layout.addSpacing(10)

        self.broadcast_transaction_title_layout = QHBoxLayout()
        self.broadcast_transaction_title_layout.setObjectName(
            'broadcast_transaction_title_layout',
        )
        self.broadcast_transaction_title_layout.setContentsMargins(
            22, -1, 28, -1,
        )
        # Multisig: no logo/icon in title per request

        self.broadcast_transaction_title_label = QLabel(self)
        self.broadcast_transaction_title_label.setObjectName(
            'broadcast_transaction_title_label',
        )
        self.broadcast_transaction_title_label.setMinimumSize(QSize(530, 63))
        self.broadcast_transaction_title_label.setMaximumSize(QSize(530, 63))

        self.broadcast_transaction_title_layout.addWidget(
            self.broadcast_transaction_title_label,
        )
        # Put stretch between title and close button so close goes to the far right
        self.broadcast_transaction_title_layout.addStretch(1)

        self.close_btn_broadcast_transaction_page = QPushButton(
            self.broadcast_transaction_widget,
        )
        self.close_btn_broadcast_transaction_page.setObjectName('close_btn')
        self.close_btn_broadcast_transaction_page.setAccessibleName(BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON)
        self.close_btn_broadcast_transaction_page.setMinimumSize(QSize(24, 24))
        self.close_btn_broadcast_transaction_page.setMaximumSize(QSize(50, 65))
        self.close_btn_broadcast_transaction_page.setAutoFillBackground(False)
        icon = QIcon()
        icon.addFile(
            ':/assets/x_circle.png', QSize(),
            QIcon.Mode.Normal, QIcon.State.Off,
        )
        self.close_btn_broadcast_transaction_page.setIcon(icon)
        self.close_btn_broadcast_transaction_page.setIconSize(QSize(24, 24))
        self.close_btn_broadcast_transaction_page.setCheckable(False)
        self.close_btn_broadcast_transaction_page.setChecked(False)
        self.close_btn_broadcast_transaction_page.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.broadcast_transaction_title_layout.addWidget(
            self.close_btn_broadcast_transaction_page,
        )
        # Multisig: ensure close button is vertically centered next to the title
        if self._is_multisig:
            self.broadcast_transaction_title_layout.setContentsMargins(
                0,0,0,0
            )


        self.vertical_layout.addLayout(self.broadcast_transaction_title_layout)

        self.header_line = QFrame(self.broadcast_transaction_widget)
        self.header_line.setObjectName('line_1')
        self.header_line.setFrameShape(QFrame.Shape.HLine)
        self.header_line.setFrameShadow(QFrame.Shadow.Sunken)
        self.vertical_layout.addWidget(self.header_line)

        self.broadcast_transaction_label = QLabel(
            self.broadcast_transaction_widget,
        )
        self.broadcast_transaction_label.setObjectName(
            'broadcast_transaction_label',
        )
        self.broadcast_transaction_label.setMinimumSize(QSize(0, 50))
        self.broadcast_transaction_label.setMaximumSize(QSize(16777215, 50))
        self.broadcast_transaction_label.setBaseSize(QSize(0, 0))
        self.broadcast_transaction_label.setAutoFillBackground(False)
        self.broadcast_transaction_label.setFrameShadow(QFrame.Plain)
        self.broadcast_transaction_label.setLineWidth(1)
        self.vertical_layout.addWidget(self.broadcast_transaction_label)
        # Multisig-only: add a small subtitle line below the section title
        if self._is_multisig:
            self.broadcast_subtitle_label = QLabel(self.broadcast_transaction_widget)
            self.broadcast_subtitle_label.setObjectName('broadcast_sub_label')
            self.broadcast_subtitle_label.setText(
                'Paste or import your Partially Signed Bitcoin Transaction'
            )
            self.broadcast_subtitle_label.setWordWrap(True)
            # Align with card edge (override QSS padding-left for multisig)
            self.broadcast_transaction_label.setStyleSheet('padding-left: 0px;')
            self.broadcast_subtitle_label.setStyleSheet('padding-left: 0px;')
            self.vertical_layout.addWidget(self.broadcast_subtitle_label)
        # Add a label for the method selector
        self.method_selector_label = QLabel(self.broadcast_transaction_widget)
        self.method_selector_label.setObjectName('broadcast_method_label')
        self.method_selector_label.setVisible(False)
        self.horizontal_layout_2 = QHBoxLayout()
        self.horizontal_layout_2.setContentsMargins(10, 15, 0, 15)
        self.method_selector = QComboBox(self.broadcast_transaction_widget)
        # Start hidden; loaders manage visibility and contents
        self.method_selector.setVisible(False)
        self.method_selector.setAccessibleName(BROADCAST_TRANSACTION_METHOD_SELECTOR)
        self.method_selector.setFixedWidth(300)
        self.method_selector.setFixedHeight(40)
        self.horizontal_layout_2.addWidget(self.method_selector_label)
        self.horizontal_layout_2.addWidget(self.method_selector)
        self.horizontal_layout_2.addStretch(1)  # Keep combobox left-aligned
        # For multisig, selector stays hidden and shouldn't add extra gaps
        if self._is_multisig:
            self.horizontal_layout_2.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.addLayout(self.horizontal_layout_2)

        # No toolbar under title in this design

        # Multisig: description + subtitle + status chip in a single horizontal row
        if self._is_multisig:
            self.desc_status_row = QHBoxLayout()
            self.desc_status_row.setContentsMargins(5, 4, 5, 6)
            self.desc_status_row.setSpacing(8)

            self.desc_col = QVBoxLayout()
            self.desc_col.setContentsMargins(0, 0, 0, 0)
            # Ensure description and subtitle line up neatly
            # reuse existing labels created above
            self.desc_col.addWidget(self.broadcast_transaction_label)
            self.desc_col.addWidget(self.broadcast_subtitle_label)
            self.desc_status_row.addLayout(self.desc_col)

            self.desc_status_row.addStretch(1)
            self.sign_status_label = QLabel(self.broadcast_transaction_widget)
            self.sign_status_label.setObjectName('status_chip')
            self.sign_status_label.setFixedHeight(50)
            self.desc_status_row.addWidget(self.sign_status_label)
            self.vertical_layout.addLayout(self.desc_status_row)

        self.horizontal_layout_1 = QHBoxLayout()
        # Ensure input aligns to card margins exactly
        if self._is_multisig:
            self.horizontal_layout_1.setContentsMargins(0, 0, 0, 0)
        self.broadcast_transaction_input = QPlainTextEdit(
            self.broadcast_transaction_widget,
        )
        self.broadcast_transaction_input.setObjectName(
            'broadcast_transaction_input',
        )
        self.broadcast_transaction_input.setAccessibleName(BROADCAST_TRANSACTION_PSBT_INPUT)
        if self._is_multisig:
            # Wider/taller input matching layout proportion and expand horizontally
            self.broadcast_transaction_input.setFixedWidth(747)
            self.broadcast_transaction_input.setMaximumHeight(200)
            self.broadcast_transaction_input.setPlaceholderText('cHNidP8BAH8CAAAAAe...')
        else:
            self.broadcast_transaction_input.setMinimumSize(QSize(550, 50))
            self.broadcast_transaction_input.setMaximumSize(QSize(550, 155))
        self.broadcast_transaction_input.setStyleSheet(
            load_stylesheet('views/qss/scrollbar.qss'),
        )
        self.horizontal_spacer_1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum,
        )
        self.horizontal_layout_1.addWidget(self.broadcast_transaction_input)
        # self.horizontal_layout_1.addSpacerItem(self.horizontal_spacer_1)
        self.vertical_layout.addLayout(
            self.horizontal_layout_1,
        )
        # Centered actions row (multisig only)
        if self._is_multisig:
            self.actions_center_row = QHBoxLayout()
            # Align buttons with input field edges and equal side space
            self.actions_center_row.setContentsMargins(5, 14, 0, 8)
            self.actions_center_row.setSpacing(16)
            self.btn_import = PrimaryButton()
            self.btn_import.setText('Import')
            self.btn_import.setFixedWidth(112)
            self.btn_import.setMinimumHeight(40)
            self.btn_import.setToolTip('Load a PSBT file from disk')
            
            self.btn_export = PrimaryButton()
            self.btn_export.setText('Export')
            self.btn_export.setFixedWidth(112)
            self.btn_export.setMinimumHeight(40)
            self.btn_export.setToolTip('Save the current PSBT to disk')
            
            self.btn_combine = PrimaryButton()
            self.btn_combine.setText('Combine')
            self.btn_combine.setFixedWidth(112)
            self.btn_combine.setMinimumHeight(40)
            self.btn_combine.setToolTip('Merge multiple partially signed PSBTs')
            
            self.broadcast_button = PrimaryButton()
            self.broadcast_button.setText('Sign PSBT')
            self.broadcast_button.setFixedWidth(112)
            self.broadcast_button.setMinimumHeight(40)
            self.broadcast_button.setToolTip('Sign the current PSBT')
            
            self.actions_center_row.addWidget(self.btn_import)
            self.actions_center_row.addWidget(self.btn_export)
            self.actions_center_row.addWidget(self.btn_combine)
            self.actions_center_row.addWidget(self.broadcast_button)
            # trailing stretch keeps left alignment while reserving right gap
            self.actions_center_row.addStretch(1)
            self.vertical_layout.addLayout(self.actions_center_row)

        self.vertical_spacer = QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.vertical_layout.addItem(self.vertical_spacer)

        # Prepare PSBT storage for optional signing flow
        if self._is_multisig:
            self._psbt_items: list[dict] = []
        # Prepare PSBT storage for broadcast flow
        if self.priv.can_broadcast_psbt:
            self._psbt_signed_items: list[dict] = []

        self.broadcast_button_horizontal_layout = QHBoxLayout()
        self.broadcast_button_horizontal_layout.setObjectName(
            'broadcast_button_horizontal_layout',
        )
        self.broadcast_button_horizontal_layout.setContentsMargins(
            -1, 0, -1, 25,
        )
        # Bottom primary button (footer):
        # - broadcast mode (any wallet)
        # - single-sig sign-only (original behavior)
        if self.priv.can_broadcast_psbt or (not self._is_multisig):
            self.broadcast_button = PrimaryButton()
            self.broadcast_button.setMinimumSize(QSize(0, 40))
            if self.priv.can_broadcast_psbt:
                self.broadcast_button.setMaximumSize(QSize(270, 16777215))
                self.broadcast_button.setAccessibleName(BROADCAST_TRANSACTION_PAGE_BUTTON)
            else:
                self.broadcast_button.setMaximumSize(QSize(270, 16777215))
                self.broadcast_button.setAccessibleName(SIGN_PSBT_PAGE_BUTTON)
            self.broadcast_button_horizontal_layout.addWidget(self.broadcast_button)
            self.vertical_layout.addLayout(self.broadcast_button_horizontal_layout)

        self.grid_layout.addWidget(
            self.broadcast_transaction_widget, 1, 1, 2, 2,
        )
        self.enter_ln_invoice_horizontal_spacer_2 = QSpacerItem(
            49, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.grid_layout.addItem(
            self.enter_ln_invoice_horizontal_spacer_2, 1, 3, 1, 1,
        )
        self.enter_ln_invoice_horizontal_spacer_1 = QSpacerItem(
            257, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.grid_layout.addItem(
            self.enter_ln_invoice_horizontal_spacer_1, 2, 0, 1, 1,
        )
        self.enter_ln_invoice_vertical_spacer_2 = QSpacerItem(
            20, 3, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
        )
        self.grid_layout.addItem(
            self.enter_ln_invoice_vertical_spacer_2, 3, 1, 1, 1,
        )
        self.broadcast_button.setDisabled(True)
        self.retranslate_ui()
        self.setup_ui_connection()
        # Always show input and label
        self.broadcast_transaction_label.setVisible(True)
        self.broadcast_transaction_input.setVisible(True)
        self.broadcast_button.setVisible(True)
        self.hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        # Evaluate initial button state once the UI is ready
        self.handle_button_enable()
        # Initialize multisig progress if applicable
        if self._is_multisig:
            # hide export/combine until sig count >= 1
            # self.btn_export.setVisible(False)
            # self.btn_combine.setVisible(False)
            _, total = SettingRepository.get_multisig_config()
            total_disp = total if total is not None else '?'
            self.sign_status_label.setText(f'Signatures collected: 0 of {total_disp}')

        # Load PSBTs for broadcast AFTER widgets exist
        if self.priv.can_broadcast_psbt and not self.from_sidebar:
            self._load_psbts_for_broadcast()

    def setup_ui_connection(self):
        """
        Set up connections for UI elements.
        """
        self.broadcast_transaction_input.textChanged.connect(
            self.handle_button_enable,
        )
        if self._is_multisig:
            self.broadcast_transaction_input.textChanged.connect(self._update_signature_progress)
        self.broadcast_button.clicked.connect(self.send_asset)
        self.close_btn_broadcast_transaction_page.clicked.connect(
            self.on_click_close_button,
        )
        self._view_model.broadcast_transaction_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self._view_model.broadcast_transaction_view_model.tx_broadcasted.connect(
            self.on_click_close_button,
        )
        self._view_model.broadcast_transaction_view_model.finalized_psbt.connect(
            self.show_signed_psbt_page,
        )
        self._view_model.broadcast_transaction_view_model.hw_dialog_update.connect(
            self.handle_nia_hw_dialog,
        )
        if self._is_multisig:
            # self._view_model.broadcast_transaction_view_model.signature_count_ready.connect(self._on_signature_count_ready)
            # self._view_model.broadcast_transaction_view_model.combined_psbt_ready.connect(self._on_combined_psbt_ready)
            self.btn_import.clicked.connect(self._on_import_psbt)
            self.btn_export.clicked.connect(self._on_export_psbt)
            self.btn_combine.clicked.connect(self._on_combine_psbts)

    def retranslate_ui(self):
        """
        Retranslate the UI elements.
        """
        if self.priv.can_broadcast_psbt:
            self.broadcast_transaction_title_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'broadcast_transaction',
                ),
            )
            self.broadcast_transaction_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'broadcast_transaction_label',
                ),
            )
            self.broadcast_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'broadcast_transaction',
                ),
            )
            # The selector label text is set dynamically in loader based on context
        else:
            self.broadcast_transaction_title_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sign_psbt',
                ),
            )
            self.broadcast_transaction_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sign_psbt_label',
                ),
            )
            self.broadcast_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sign_psbt',
                ),
            )

    def send_asset(self):
        """
        Broadcast the signed PSBT using the selected method.
        """
        signed_psbt = self.broadcast_transaction_input.toPlainText().strip()
        purpose = None

        if signed_psbt.startswith('psbt:'):
            parts = signed_psbt.split(':', 2)
            if len(parts) == 3:  # Format: psbt:<purpose>:<psbt>
                purpose, signed_psbt = parts[1], parts[2]
            elif len(parts) == 2:  # Format: psbt:<psbt>
                signed_psbt = parts[1]

        confirmation_dialog = ConfirmationDialog(
            message=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'data_sync_warning',
            ),
            parent=self,
            icon_type='warning',
        )

        if not confirmation_dialog.exec() == QDialog.Accepted:
            return

        if self.priv.can_broadcast_psbt:
            if purpose is None and self._psbt_signed_items:
                idx = self.method_selector.currentIndex() if self.method_selector.isVisible() else 0
                if 0 <= idx < len(self._psbt_signed_items):
                    purpose = self._psbt_signed_items[idx].get('purpose')

            purpose_map = {
                'send_btc': self._view_model.broadcast_transaction_view_model.send_btc_end,
                'send_asset': self._view_model.broadcast_transaction_view_model.send_end,
            }

            handler = purpose_map.get(
                purpose, self._view_model.broadcast_transaction_view_model.create_utxos_end,
            )
            handler(signed_psbt)

        else:
            # Determine purpose similarly for sign-only mode to set RGB mode
            if purpose is None and self._psbt_items:
                idx = self.method_selector.currentIndex() if self.method_selector.isVisible() else 0
                if 0 <= idx < len(self._psbt_items):
                    purpose = self._psbt_items[idx].get('purpose')

            # Enable RGB mode only for RGB asset signing; BTC/UTXO default to False
            hardware_client_store.set_rgb_mode(purpose == 'send_asset')

            self._view_model.broadcast_transaction_view_model.sign_and_finalize_psbt(
                signed_psbt,
            )

    def on_success_sent_navigation(self):
        """
        Navigate to collectibles or fungibles page when the originating page is create ln invoice.
        """
        self._view_model.page_navigation.fungibles_asset_page()

    def handle_button_enable(self):
        """
        Enable or disable the broadcast button based on input and method selection.
        """
        has_input = bool(self.broadcast_transaction_input.toPlainText())
        if self.priv.can_broadcast_psbt:
            selector_visible = self.method_selector.isVisible()
            method_ok = (not selector_visible) or (
                self.method_selector.currentIndex() >= 0
            )
            self.broadcast_button.setEnabled(has_input and method_ok)
        else:
            self.broadcast_button.setEnabled(has_input)

    # ----- Multisig helpers -----
    def _update_signature_progress(self):
        """Update the signature progress label for multisig (e.g., 1 of 3)."""
        required, total = SettingRepository.get_multisig_config()
        current_psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not current_psbt:
            total_disp = total if total is not None else '?'
            self.sign_status_label.setText(
                f'Signatures collected: 0 of {total_disp}' + (
                    '' if not required else f'  (Required: {required})'
                ),
            )
            if self._is_multisig:
                self.btn_export.setVisible(False)
                self.btn_combine.setVisible(False)
            return
        # self._view_model.broadcast_transaction_view_model.analyze_signature_count(current_psbt)
        self._on_signature_count_ready(0)

    def _on_signature_count_ready(self, count: int):
        required, total = SettingRepository.get_multisig_config()
        total_disp = total if total is not None else '?'
        self.sign_status_label.setText(
            f'Signatures collected: {count} of {total_disp}' + (
                '' if not required else f'  (Required: {required})'
            ),
        )
        # show export/combine only when at least 1 signature exists
        if self._is_multisig:
            has_one = isinstance(count, int) and count >= 1
            self.btn_export.setVisible(has_one)
            self.btn_combine.setVisible(has_one)

    def _on_import_psbt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import PSBT', '', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            self.broadcast_transaction_input.setPlainText(content)
        except Exception:
            pass

    def _on_export_psbt(self):
        current_psbt = self.broadcast_transaction_input.toPlainText().strip()
        # if not current_psbt:
        #     return
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export PSBT', 'transaction.psbt', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_psbt)
        except Exception:
            pass

    def _on_combine_psbts(self):
        # Ask user for an additional PSBT to combine with the current one
        base_psbt = self.broadcast_transaction_input.toPlainText().strip()
        # if not base_psbt:
        #     return
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Select PSBT to Combine', '', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                other = f.read().strip()
        except Exception:
            return
        # self._view_model.broadcast_transaction_view_model.combine_psbts(
        #     [base_psbt, other],
        # )

    def _on_combined_psbt_ready(self, combined: str):
        if combined:
            self.broadcast_transaction_input.setPlainText(combined)
            self._update_signature_progress()

    def update_loading_state(self, is_loading: bool):
        """
        Updates the loading state of the send button.
        """
        if is_loading:
            self.render_timer.start()
            self.broadcast_button.start_loading()
            self.broadcast_button.setEnabled(False)
        else:
            self.render_timer.stop()
            self.broadcast_button.stop_loading()
            self.handle_button_enable()

    def on_click_close_button(self):
        """
        Navigate to the specified page when the close button is clicked.
        """
        self.sidebar = self._view_model.page_navigation.sidebar()
        originating_page = self.get_checked_button_translation_key(
            self.sidebar,
        )
        navigation_map = {
            'fungibles': self._view_model.page_navigation.fungibles_asset_page,
            'NIA': self._view_model.page_navigation.fungibles_asset_page,
            'CFA': self._view_model.page_navigation.collectibles_asset_page,
            'collectibles': self._view_model.page_navigation.collectibles_asset_page,
            'faucets': self._view_model.page_navigation.faucets_page,
            'view_unspent_list': self._view_model.page_navigation.view_unspent_list_page,
            'help': self._view_model.page_navigation.help_page,
            'settings': self._view_model.page_navigation.settings_page,
            'backup': self._view_model.page_navigation.backup_page,
            'about': self._view_model.page_navigation.about_page,
            'broadcast_transaction': self._view_model.page_navigation.broadcast_transaction_page,
        }
        broadcast_navigation = navigation_map.get(originating_page)
        if broadcast_navigation:
            broadcast_navigation()
        else:
            ToastManager.show_toast(
                parent=self,
                preset=ToastPreset.ERROR,
                description=f'No navigation defined for {
                    originating_page
                }',
            )

    def get_checked_button_translation_key(self, sidebar):
        """
        Get the translation key of the checked sidebar button.
        """
        buttons = [
            sidebar.backup,
            sidebar.help,
            sidebar.view_unspent_list,
            sidebar.faucet,
            sidebar.my_fungibles,
            sidebar.my_collectibles,
            sidebar.settings,
            sidebar.about,
            sidebar.broadcast_transaction,
        ]
        for button in buttons:
            if button.isChecked():
                return button.get_translation_key()
        return None

    def _load_psbts_for_signing(self) -> None:
        """Populate the PSBT input from stored unsigned drafts.
        Reuse the existing method selector and label as a PSBT selector when
        broadcasting is not permitted (sign-only mode).
        """
        try:
            wallet_service = WalletDataService.get_session()
            drafts = wallet_service.list_psbt(
                False,
            ) if wallet_service is not None else []
        except Exception:
            drafts = []

        self._psbt_items = drafts or []
        count = len(self._psbt_items)

        # 0 PSBTs: hide selector, clear input, disable button
        if count == 0:
            self.method_selector_label.setVisible(False)
            self.method_selector.setVisible(False)
            self.broadcast_transaction_input.clear()
            self.broadcast_button.setEnabled(False)
            return

        # 1 PSBT: hide selector, set text, enable button
        if count == 1:
            self.method_selector_label.setVisible(False)
            self.method_selector.setVisible(False)
            self.broadcast_transaction_input.setPlainText(
                self._psbt_items[0].get('psbt', ''),
            )
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()
            return

        # >1 PSBTs: show and populate selector
        self.method_selector_label.setVisible(True)
        self.method_selector.setVisible(True)
        self.method_selector_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'select_psbt_for_sign',
            ),
        )

        self.method_selector.blockSignals(True)
        self.method_selector.clear()
        titles = []
        for item in self._psbt_items:
            purpose = item.get('purpose') or 'psbt'
            psbt_id = item.get('id', '')
            titles.append(f"{purpose} ({psbt_id[:8]})" if psbt_id else purpose)
        if titles:
            self.method_selector.addItems(titles)
        self.method_selector.blockSignals(False)

        def on_index_changed(idx: int):
            psbt_text = self._psbt_items[idx].get(
                'psbt', '',
            ) if 0 <= idx < len(self._psbt_items) else ''
            self.broadcast_transaction_input.setPlainText(psbt_text)
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()

        self.method_selector.currentIndexChanged.connect(on_index_changed)
        on_index_changed(0)

    def handle_nia_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        self.hw_dialog.update_dialog(message, dialog_type)
        if not self.hw_dialog.isVisible():
            self.hw_dialog.show()

    def show_signed_psbt_page(self, psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        if psbt:
            if self.hw_dialog.isVisible():
                self.hw_dialog.accept()
            self._view_model.page_navigation.receive_asset_page(
                ReceiveAssetModel(
                    page_name='NIA page',
                    address_info='psbt_info', psbt=psbt, is_signed=True,
                ),
            )

    def _load_psbts_for_broadcast(self) -> None:
        """Populate the PSBT input from stored signed drafts for broadcasting.
        Reuse the same selector as a PSBT selector (no separate widget).
        """
        try:
            wallet_service = WalletDataService.get_session()
            drafts = wallet_service.list_psbt(
                True,
            ) if wallet_service is not None else []
        except Exception:
            drafts = []

        self._psbt_signed_items = drafts or []
        count = len(self._psbt_signed_items)

        # 0 PSBTs: hide selector, clear input, disable button
        if count == 0:
            self.method_selector_label.setVisible(False)
            self.method_selector.setVisible(False)
            self.handle_button_enable()
            return

        # 1 PSBT: hide selector, set text, enable button
        if count == 1:
            self.method_selector_label.setVisible(False)
            self.method_selector.setVisible(False)
            self.broadcast_transaction_input.setPlainText(
                self._psbt_signed_items[0].get('psbt', ''),
            )
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()
            return

        # >1 PSBTs: show and populate selector
        self.method_selector_label.setVisible(True)
        self.method_selector.setVisible(True)
        self.method_selector_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'select_psbt_for_broadcast',
            ),
        )

        self.method_selector.blockSignals(True)
        self.method_selector.clear()
        titles = []
        for item in self._psbt_signed_items:
            purpose = item.get('purpose') or 'psbt'
            psbt_id = item.get('id', '')
            titles.append(f"{purpose} ({psbt_id[:8]})" if psbt_id else purpose)
        if titles:
            self.method_selector.addItems(titles)
        self.method_selector.blockSignals(False)

        def on_index_changed(idx: int):
            psbt_text = self._psbt_signed_items[idx].get(
                'psbt', '',
            ) if 0 <= idx < len(self._psbt_signed_items) else ''
            self.broadcast_transaction_input.setPlainText(psbt_text)
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()

        self.method_selector.currentIndexChanged.connect(on_index_changed)
        on_index_changed(0)
