# pylint: disable=too-many-instance-attributes, too-many-statements, too-many-branches, too-many-lines
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
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFileDialog
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
from rgb_lib import Operation

from accessible_constant import BROADCAST_TRANSACTION_METHOD_SELECTOR
from accessible_constant import BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PSBT_INPUT
from src.data.repository.setting_repository import SettingRepository
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.model.broadcast_transaction_model import PsbtDraftItem
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.common_utils import close_button_navigation
from src.utils.common_utils import get_current_wallet_mode_config
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.error_message import ERROR_OPERATION_NOT_FOUND_TO_REJECT
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import load_stylesheet
from src.utils.helpers import set_widgets_visible
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.broadcast_inspection_details import BroadcastInspectionDetails
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.loading_screen import LoadingTranslucentScreen
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame


class BroadcastTransactionWidget(QWidget):
    """
    Widget for broadcasting signed transactions (PSBTs) in the application.
    """

    def __init__(self, view_model, from_sidebar: bool = False, pending_operation: object = None):
        """
        Initialize the BroadcastTransactionWidget.
        """
        super().__init__()
        self.sidebar = None
        self.render_timer = RenderTimer(
            task_name='Broadcast Transaction Rendering',
        )
        self.view_model: MainViewModel = view_model
        self.from_sidebar = from_sidebar
        self.pending_operation = pending_operation

        self.setStyleSheet(
            load_stylesheet(
                'views/qss/broadcast_transaction_style.qss',
            ),
        )
        config = get_current_wallet_mode_config()
        self.priv = config.privileges
        # Inspection state (to avoid partial renders)
        self._psbt_details = None
        self._rgb_details = None
        self._last_inspected_psbt = None
        self._op_details_ready = False
        self._rgb_expected: bool = False
        self._is_inflation_context: bool = False
        self._pending_transfer_type = None
        self._inspection_epoch = 0
        self.is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        self.is_watch_only = SettingRepository.get_wallet_access_type(
        ) == WalletAccessType.WATCH_ONLY
        # Minimum characters to consider PSBT input valid for enabling Sign button
        self.min_psbt_len = 80
        self.is_initiator_of_pending = False
        self.is_psbt_validated = False  # Strict validation flag
        self._current_operation = None
        self._signals_connected: bool = False
        self._programmatic_psbt_set: bool = False

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setObjectName('grid_layout')
        for i in range(3):
            self.grid_layout.setColumnStretch(i, 1)

        self.wallet_logo_frame = WalletLogoFrame(self)
        self.grid_layout.addWidget(self.wallet_logo_frame, 0, 0, 1, 1)
        self.grid_layout.addItem(
            QSpacerItem(
                20, 61, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding,
            ), 0, 2, 1, 1,
        )

        self.broadcast_transaction_widget = QWidget(self)
        self.broadcast_transaction_widget.setObjectName(
            'broadcast_transaction_widget',
        )
        self.broadcast_transaction_widget.setFixedWidth(
            800 if self.is_multisig else 700,
        )
        self.broadcast_transaction_widget.setMinimumHeight(
            450 if self.is_multisig else 380,
        )

        self.vertical_layout = QVBoxLayout(self.broadcast_transaction_widget)
        margin = 22 if self.is_multisig else 23
        self.vertical_layout.setContentsMargins(margin, 8, margin, 10)
        self.vertical_layout.addSpacing(4)

        self._loading_overlay = LoadingTranslucentScreen(
            parent=self, description_text='Loading',
        )
        self._loading_overlay.stop()

        self.broadcast_transaction_title_layout = QHBoxLayout()
        self.broadcast_transaction_title_label = QLabel(self)
        self.broadcast_transaction_title_label.setObjectName(
            'broadcast_transaction_title_label',
        )
        self.broadcast_transaction_title_label.setFixedSize(QSize(400, 63))
        self.broadcast_transaction_title_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
        )

        self.close_btn_broadcast_transaction_page = QPushButton(
            self.broadcast_transaction_widget,
        )
        self.close_btn_broadcast_transaction_page.setObjectName('close_btn')
        self.close_btn_broadcast_transaction_page.setAccessibleName(
            BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON,
        )
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
            self.broadcast_transaction_title_label,
        )
        self.broadcast_transaction_title_layout.addStretch(1)
        self.broadcast_transaction_title_layout.addWidget(
            self.close_btn_broadcast_transaction_page,
        )
        self.vertical_layout.addLayout(self.broadcast_transaction_title_layout)

        self.header_line = QFrame(self.broadcast_transaction_widget)
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
        # For multisig, this label will be placed inside a compact row later
        if not self.is_multisig:
            self.vertical_layout.addWidget(self.broadcast_transaction_label)
        # Multisig-only: add a small subtitle line below the section title
        if self.is_multisig:
            self.broadcast_subtitle_label = QLabel(
                self.broadcast_transaction_widget,
            )
            self.broadcast_subtitle_label.setObjectName('broadcast_sub_label')
            self.broadcast_subtitle_label.setMinimumSize(QSize(500, 24))
            self.broadcast_subtitle_label.setMaximumSize(QSize(16777215, 28))
            self.broadcast_subtitle_label.setWordWrap(True)
            self.broadcast_transaction_label.setStyleSheet(
                'padding-left: 0px;',
            )
            self.broadcast_subtitle_label.setStyleSheet('padding-left: 0px;')

        # Add a label for the method selector
        self.method_selector_label = QLabel(self.broadcast_transaction_widget)
        self.method_selector_label.setObjectName('broadcast_method_label')
        self.method_selector_label.hide()
        self.method_selector_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'select_psbt_for_broadcast',
            ),
        )
        self.horizontal_layout_2 = QHBoxLayout()
        self.horizontal_layout_2.setContentsMargins(0, 8, 0, 4)
        self.method_selector = QComboBox(self.broadcast_transaction_widget)
        # Start hidden; loaders manage visibility and contents
        self.method_selector.hide()
        self.method_selector.setAccessibleName(
            BROADCAST_TRANSACTION_METHOD_SELECTOR,
        )
        self.method_selector.setFixedWidth(300)
        self.method_selector.setFixedHeight(40)
        self.horizontal_layout_2.addWidget(self.method_selector_label)
        self.horizontal_layout_2.addWidget(self.method_selector)
        self.horizontal_layout_2.addStretch(1)  # Keep combobox left-aligned
        self.vertical_layout.addLayout(self.horizontal_layout_2)

        # No toolbar under title in this design

        # Multisig: description + subtitle + status chip in a single horizontal row
        if self.is_multisig:
            self.desc_status_row = QHBoxLayout()
            self.desc_status_row.setContentsMargins(4, 2, 4, 4)
            self.desc_status_row.setSpacing(6)

            self.desc_col = QVBoxLayout()
            self.desc_col.setContentsMargins(0, 0, 0, 0)
            self.desc_col.setSpacing(0)
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
            # Hide the chip until a PSBT is inspected and details are valid
            self.sign_status_label.hide()

        self.horizontal_layout_1 = QHBoxLayout()
        # Ensure input aligns to card margins exactly
        self.horizontal_layout_1.setContentsMargins(0, 0, 0, 0)
        self.broadcast_transaction_input = QPlainTextEdit(
            self.broadcast_transaction_widget,
        )
        self.broadcast_transaction_input.setObjectName(
            'broadcast_transaction_input',
        )
        self.broadcast_transaction_input.setAccessibleName(
            BROADCAST_TRANSACTION_PSBT_INPUT,
        )
        if self.is_multisig:
            # For multisig, let input expand to available width and keep a compact height
            self.broadcast_transaction_input.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed,
            )
            self.broadcast_transaction_input.setFixedWidth(747)
            self.broadcast_transaction_input.setMaximumHeight(200)
            self.broadcast_transaction_input.setPlaceholderText(
                'cHNidP8BAH8CAAAAAe...',
            )
        else:
            self.broadcast_transaction_input.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed,
            )
            self.broadcast_transaction_input.setFixedWidth(647)
            self.broadcast_transaction_input.setMinimumHeight(50)
            self.broadcast_transaction_input.setMaximumHeight(155)
        # Base styling (no font override). We will apply compact monospace font
        # only when multisig PSBT is validated and details are showing.
        self._psbt_input_base_style = (
            load_stylesheet('views/qss/scrollbar.qss') +
            '\nQPlainTextEdit#broadcast_transaction_input { border: none; border-radius: 12px; padding: 12px; background-color: rgba(255,255,255,0.06); }'
        )
        self.broadcast_transaction_input.setStyleSheet(
            self._psbt_input_base_style,
        )
        self.horizontal_spacer_1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum,
        )
        self.horizontal_layout_1.addWidget(self.broadcast_transaction_input)
        # self.horizontal_layout_1.addSpacerItem(self.horizontal_spacer_1)
        self.vertical_layout.addLayout(
            self.horizontal_layout_1,
        )

        self.inspection_details = BroadcastInspectionDetails(
            self.broadcast_transaction_widget,
        )
        self.inspection_details.set_config(
            is_multisig=self.is_multisig,
            is_watch_only=self.is_watch_only,
            can_broadcast=self.priv.can_broadcast_psbt,
        )
        self.vertical_layout.addWidget(self.inspection_details)

        # Legacy button reference for compatibility during transition
        self.broadcast_button = self.inspection_details.btn_primary

        # Prepare PSBT storage for optional signing flow
        if self.is_multisig:
            self._psbt_items: list[PsbtDraftItem] = []
        # Prepare PSBT storage for broadcast flow
        if self.priv.can_broadcast_psbt:
            self._psbt_signed_items: list[PsbtDraftItem] = []

        # Always hide Export in this flow (not needed now)
        if self.is_multisig:
            self.inspection_details.btn_export.hide()
            self.inspection_details.btn_export.setEnabled(False)

        self.grid_layout.addWidget(
            self.broadcast_transaction_widget, 1, 1, 1, 1,
        )
        # Symmetric side spacers in the same row to keep the card perfectly centered
        self.enter_ln_invoice_horizontal_spacer_left = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.enter_ln_invoice_horizontal_spacer_right = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )
        self.grid_layout.addItem(
            self.enter_ln_invoice_horizontal_spacer_left, 1, 0, 1, 1,
        )
        self.grid_layout.addItem(
            self.enter_ln_invoice_horizontal_spacer_right, 1, 2, 1, 1,
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
        if self.is_multisig:
            _, total = SettingRepository.get_multisig_config()
            total_disp = total if total is not None else '?'
            self.sign_status_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'signature_count',
                ).format(0, total_disp),
            )
            # Ensure chip is hidden until a valid PSBT is inspected
            self.sign_status_label.hide()

        # Load PSBTs AFTER widgets exist
        if not self.from_sidebar:
            if self.priv.can_broadcast_psbt:
                self._load_psbts_for_broadcast()
            else:
                self._load_psbts_for_signing()

    def setup_ui_connection(self):
        """Set up all signals and slots in a compact manner."""
        if self._signals_connected:
            return

        self.broadcast_transaction_input.textChanged.connect(
            self.handle_button_enable,
        )
        if self.is_multisig:
            self.broadcast_transaction_input.textChanged.connect(
                self._on_psbt_text_changed,
            )
            self.broadcast_transaction_input.textChanged.connect(
                self._update_signature_progress,
            )
        self.close_btn_broadcast_transaction_page.clicked.connect(
            lambda: close_button_navigation(self),
        )

        self.view_model.broadcast_transaction_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self.view_model.broadcast_transaction_view_model.is_reject_loading.connect(
            self.update_reject_button_state,
        )
        self.view_model.broadcast_transaction_view_model.tx_broadcasted.connect(
            lambda: close_button_navigation(self),
        )
        self.view_model.broadcast_transaction_view_model.tx_broadcasted.connect(
            self._cleanup_secondary_draft_if_any,
        )
        self.view_model.broadcast_transaction_view_model.finalized_psbt.connect(
            self.show_signed_psbt_page,
        )
        self.view_model.broadcast_transaction_view_model.hw_dialog_update.connect(
            self.handle_nia_hw_dialog,
        )
        self.view_model.broadcast_transaction_view_model.psbt_inspection_ready.connect(
            self._handle_psbt_inspection_result,
        )
        self.view_model.broadcast_transaction_view_model.rgb_transfer_inspection_ready.connect(
            self._handle_rgb_transfer_inspection_result,
        )
        self.view_model.broadcast_transaction_view_model.pending_operation_ready.connect(
            self._on_pending_operation_ready,
        )
        self.view_model.broadcast_transaction_view_model.psbts_loaded.connect(
            self._on_psbts_loaded,
        )
        self.view_model.broadcast_transaction_view_model.trigger_bridge_sync.connect(
            self.view_model.header_frame_view_model.sync_multisig_bridge,
        )
        self.method_selector.currentIndexChanged.connect(
            self._on_method_selector_index_changed,
        )

        if self.is_multisig:
            self.inspection_details.btn_import.clicked.connect(
                self._on_import_psbt,
            )
            self.inspection_details.btn_export.clicked.connect(
                self._on_export_psbt,
            )
            self.inspection_details.btn_clear.clicked.connect(
                self._on_clear_psbt,
            )
            self.inspection_details.btn_reject.clicked.connect(
                self._on_reject_operation,
            )
            self.view_model.broadcast_transaction_view_model.finalized_psbt.connect(
                self._on_finalized_psbt_ready,
            )
            self.inspection_details.btn_primary.clicked.connect(
                self._on_respond_multisig if self.is_watch_only else self._on_sign_and_post_multisig,
            )
        else:
            self.inspection_details.btn_primary.clicked.connect(
                self.send_asset,
            )

        self._signals_connected = True

    def _on_psbt_text_changed(self):
        """Auto-trigger inspection when the user pastes/types a PSBT."""
        if self._programmatic_psbt_set:
            self._programmatic_psbt_set = False

        if not self.is_multisig:
            return

        psbt_text = self.broadcast_transaction_input.toPlainText().strip()
        context = BroadcastTransactionService.prepare_psbt_text_changed_state(
            psbt_text, self._last_inspected_psbt, self.min_psbt_len,
        )

        if context.is_same_as_last:
            return

        if context.should_inspect:
            self._last_inspected_psbt = context.psbt_body
            self.inspection_details.show_inspection_details(False)
            if self.is_multisig:
                self.sign_status_label.hide()
            self._loading_overlay.start()
            self._loading_overlay.make_parent_disabled_during_loading(True)

            self._inspection_epoch += 1
            self._psbt_details = None
            self._rgb_details = None
            self._rgb_expected = context.is_rgb
            self._is_inflation_context = context.is_inflation
            self._pending_transfer_type = context.purpose

            if self.is_multisig:
                self._update_signature_progress()
                self.view_model.broadcast_transaction_view_model.fetch_pending_operation()
        else:
            self._last_inspected_psbt = None
            self.inspection_details.show_inspection_details(False)
            if self.is_multisig:
                self.sign_status_label.hide()
            self._loading_overlay.stop()
            self.handle_button_enable()

    def _render_inspection_if_ready(self):
        """Checks if both inspections are complete and renders the UI."""
        current_text = self.broadcast_transaction_input.toPlainText().strip()
        current_psbt = BroadcastTransactionService.parse_psbt_input(
            current_text,
        ).psbt

        is_offline_wallet = (
            SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET
        )

        render_result = BroadcastTransactionService.prepare_render_inspection_state(
            self._psbt_details, bool(
                self.is_multisig and self._rgb_expected,
            ), self._rgb_details,
            is_offline_wallet, current_psbt, self.min_psbt_len,
        )

        if not render_result.should_render:
            return

        self.inspection_details.inspect_loading.hide()
        self.inspection_details.show_inspection_details(True)
        self.is_psbt_validated = True
        self.handle_button_enable()

        if self.is_multisig:
            if render_result.should_show_sign_status:
                self.sign_status_label.show()

            self.broadcast_transaction_input.setStyleSheet(
                self._psbt_input_base_style +
                '\nQPlainTextEdit#broadcast_transaction_input { font: 12px "JetBrains Mono", monospace; }',
            )

        self._loading_overlay.stop()
        self._loading_overlay.make_parent_disabled_during_loading(False)

    def retranslate_ui(self):
        """Translate the UI elements using service logic."""
        is_signed = self.priv.can_broadcast_psbt
        data = BroadcastTransactionService.get_retranslate_data(
            is_signed, self.is_multisig, self.is_watch_only,
        )

        self.broadcast_transaction_title_label.setText(data['title'])
        self.broadcast_transaction_label.setText(data['label'])
        self.broadcast_button.setText(data['button'])

        if self.is_multisig:
            self.broadcast_subtitle_label.setText(data['subtitle'])
            self.inspection_details.retranslate_ui()

    def send_asset(self):
        """
        Broadcast the signed PSBT using the selected method.
        """
        psbt_text = self.broadcast_transaction_input.toPlainText().strip()

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

        items = self._psbt_signed_items if self.priv.can_broadcast_psbt else self._psbt_items
        idx = self.method_selector.currentIndex() if self.method_selector.isVisible() else 0
        selector_purpose = BroadcastTransactionService.selected_purpose(
            items, idx if len(items) > idx else -1,
        )

        self.view_model.broadcast_transaction_view_model.execute_psbt_action(
            psbt_text=psbt_text,
            selector_purpose=selector_purpose,
            can_broadcast=self.priv.can_broadcast_psbt,
        )

    def _cleanup_secondary_draft_if_any(self, *_):
        """Delete the latest active IFA secondary draft (watch-only/offline)."""
        try:
            psbt_text = self.broadcast_transaction_input.toPlainText().strip()
            explicit_purpose = None
            if self._current_operation:
                if self._current_operation.is_INFLATION_TO_REVIEW():
                    explicit_purpose = 'inflate_asset'
            BroadcastTransactionService.cleanup_secondary_draft_if_any(
                psbt_text,
                explicit_purpose,
            )
        except Exception:
            pass

    def _on_psbts_loaded(self, items: list[PsbtDraftItem]) -> None:
        set_widgets_visible(
            [self.method_selector, self.method_selector_label], False,
        )

        is_signed = self.priv.can_broadcast_psbt
        if is_signed:
            self._psbt_signed_items = items
        else:
            self._psbt_items = items

        data = BroadcastTransactionService.psbts_loaded_data(items, is_signed)

        if not data['has_items']:
            self.handle_button_enable()
            return

        if data.get('is_single'):
            self._programmatic_psbt_set = True
            self.broadcast_transaction_input.setPlainText(data['psbt'])
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()
            return

        if not self.is_multisig:
            self.method_selector_label.show()
            self.method_selector.show()

        self.method_selector_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, data['label_key'],
            ),
        )
        self.method_selector.blockSignals(True)
        self.method_selector.clear()
        self.method_selector.addItems(data['titles'])
        self.method_selector.blockSignals(False)
        self._on_method_selector_index_changed(0)
        self.handle_button_enable()

    def _on_method_selector_index_changed(self, idx: int) -> None:
        items = self._psbt_signed_items if self.priv.can_broadcast_psbt else self._psbt_items
        if idx < 0 or idx >= len(items):
            return
        self._programmatic_psbt_set = True
        self.broadcast_transaction_input.setPlainText(items[idx].psbt)
        self.broadcast_transaction_input.setReadOnly(True)
        self.handle_button_enable()

    def handle_button_enable(self):
        """
        Enable or disable the action buttons based on logic moved to service.
        """
        psbt_text = self.broadcast_transaction_input.toPlainText()
        is_offline_mode = (
            SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY or
            SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET
        )

        can_primary = BroadcastTransactionService.can_enable_primary_action(
            psbt_text=psbt_text,
            can_broadcast=self.priv.can_broadcast_psbt,
            is_multisig=self.is_multisig,
            is_psbt_validated=self.is_psbt_validated,
            pending_operation_present=self.pending_operation is not None,
            is_watch_only=self.is_watch_only,
            selector_index=self.method_selector.currentIndex(),
            selector_visible=self.method_selector.isVisible(),
            is_offline_mode=is_offline_mode,
            min_psbt_len=self.min_psbt_len,
        )
        self.inspection_details.set_primary_enabled(can_primary)

        can_reject = BroadcastTransactionService.can_enable_reject_action(
            can_broadcast=self.priv.can_broadcast_psbt,
            is_multisig=self.is_multisig,
            is_psbt_validated=self.is_psbt_validated,
            pending_operation_present=self.pending_operation is not None,
            is_watch_only=self.is_watch_only,
        )
        self.inspection_details.set_reject_enabled(can_reject)

    def _on_finalized_psbt_ready(self):
        """Our wallet has signed successfully; allow exporting the signed PSBT."""
        if self.is_multisig:
            # Keep export hidden/disabled as per current requirement
            self.inspection_details.btn_export.hide()
            self.inspection_details.btn_export.setEnabled(False)
            self.inspection_details.btn_import.setEnabled(False)
            self.inspection_details.set_primary_enabled(False)

    def _on_sign_and_post_multisig(self):
        """Sign the PSBT and post back to the multisig bridge."""
        psbt_text = self.broadcast_transaction_input.toPlainText().strip()
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        psbt = parsed.psbt
        if not psbt:
            ToastManager.error(description='No PSBT to sign')
            return

        purpose = BroadcastTransactionService.resolve_purpose_for_signing(
            parsed.purpose, self._current_operation, psbt,
        )

        # Set RGB mode explicitly before signing
        if purpose:
            BroadcastTransactionService.set_rgb_mode_for_purpose(purpose)
            if BroadcastTransactionService.is_rgb_purpose(purpose):
                self._rgb_expected = True

        # Get the operation index for posting back
        operation_idx = self.pending_operation.operation_idx if self.pending_operation else None

        # Call the viewmodel to sign and post
        self.view_model.broadcast_transaction_view_model.sign_and_post_multisig(
            psbt, operation_idx, purpose=purpose,
        )

    def _on_respond_multisig(self):
        """Watch-only multisig: respond to pending op."""
        psbt_text = self.broadcast_transaction_input.toPlainText().strip()
        if not psbt_text:
            ToastManager.error(description='No PSBT')
            return

        if self.pending_operation is not None:
            operation_idx = self.pending_operation.operation_idx
            # Use raw PSBT text (base64) for response, stripping prefix if any
            parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
            psbt_only = parsed.psbt
            self.view_model.broadcast_transaction_view_model.respond_psbt_to_operation(
                psbt_only,
                operation_idx,
            )
            return

        ToastManager.error(
            description='Pending operation not found to respond to',
        )

    def _on_reject_operation(self):
        """Reject the pending operation (NACK) without signing."""
        operation_idx = None
        if self.pending_operation:
            operation_idx = self.pending_operation.operation_idx
        elif self._current_operation:
            pass
        if operation_idx is None:
            ToastManager.error(description=ERROR_OPERATION_NOT_FOUND_TO_REJECT)
            return
        self.view_model.broadcast_transaction_view_model.respond_nack(
            operation_idx,
        )

    def _refresh_multisig_state_and_sync(self):
        """Update signature progress and trigger bridge sync."""
        if self.is_multisig and self._current_operation:
            if self._current_operation.status is not None and self._current_operation.status.acked_by is not None and self._current_operation.status.threshold is not None:
                ack_count = len(self._current_operation.status.acked_by)
                self._on_signature_count_ready(
                    ack_count, self._current_operation.status.threshold,
                )
        if self.is_multisig:
            self.view_model.broadcast_transaction_view_model.fetch_pending_operation()

    def _handle_psbt_inspection_result(self, details):
        """
        Handle the async PSBT inspection result from the signal.
        """
        if details is None:
            self.inspection_details.show_inspection_details(False)
            self.is_psbt_validated = False
            self.handle_button_enable()
            if self.is_multisig:
                self.sign_status_label.hide()
            return

        self._psbt_details = details
        self.is_psbt_validated = True  # Mark as validated when we get details

        # Resolve pending key for transfer type via service
        current_text = self.broadcast_transaction_input.toPlainText().strip()
        pending_key = BroadcastTransactionService.resolve_transfer_type(
            psbt_text=current_text,
            is_multisig=self.is_multisig,
            explicit_type=self._pending_transfer_type,
            is_inflation=self._is_inflation_context,
        )

        self.inspection_details.update_psbt_details(
            details, self._is_inflation_context, self._rgb_expected, pending_key,
        )
        self._render_inspection_if_ready()
        self._refresh_multisig_state_and_sync()

    def _handle_rgb_transfer_inspection_result(self, rgb_details):
        """
        Handle the async RGB transfer inspection result.
        """
        self._rgb_details = rgb_details
        summary = BroadcastTransactionService.rgb_transfer_inspection_summary(
            rgb_details, self._pending_transfer_type,
        )

        # Retrieve min_conf from operation or stored context (offline)
        min_conf = None
        if self._current_operation and self._current_operation.details:
            min_conf = self._current_operation.details.min_confirmations
        elif self._stored_context:
            min_conf = self._stored_context.get('min_confirmations')

        self.inspection_details.update_rgb_details(
            asset_id=summary.asset_id,
            amount=summary.amount,
            transfer_type_label=BroadcastTransactionService.get_transfer_type_label(
                summary.transfer_type_key,
            ),
            min_conf=min_conf,
            result=rgb_details,
        )
        self._render_inspection_if_ready()
        self._refresh_multisig_state_and_sync()

    def _on_pending_operation_ready(self, op_info):
        """
        Callback when bridge sync returns a pending operation (or None).
        We check if this operation matches the PSBT we are currently inspecting.
        """
        if not self.is_multisig or not op_info:
            return

        current_text = self.broadcast_transaction_input.toPlainText().strip()
        current_psbt = BroadcastTransactionService.parse_psbt_input(
            current_text,
        ).psbt
        if not current_psbt:
            return

        pending = BroadcastTransactionService.match_pending_operation(
            op_info, current_psbt,
        )

        # Extended Logic: If string match fails, try fuzzy TXID match
        if pending is None and self._psbt_details:
            pending_txid = self.view_model.broadcast_transaction_view_model.get_pending_psbt_txid()
            if pending_txid and pending_txid == self._psbt_details.txid:
                pending = BroadcastTransactionService.match_pending_operation_by_txid(
                    op_info, pending_txid,
                )

        match_result = BroadcastTransactionService.process_pending_operation_match(
            pending, op_info, self.is_watch_only,
        )
        if not match_result:
            return

        self._current_operation = match_result.operation
        self.pending_operation = match_result.pending_operation
        self._pending_transfer_type = match_result.transfer_type
        self._is_inflation_context = match_result.is_inflation

        if self._psbt_details is not None:
            new_label = BroadcastTransactionService.get_transfer_type_label(
                self._pending_transfer_type,
            )
            self.inspection_details.update_transfer_type_label(new_label)

        if match_result.should_trigger_rgb_inspection:
            self._rgb_expected = True
            self._rgb_details = None
            self.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                match_result.fascia_path, current_psbt, match_result.entropy,
            )

        self.is_initiator_of_pending = match_result.is_initiator
        self._on_signature_count_ready(
            match_result.ack_count, match_result.threshold,
        )
        self.handle_button_enable()

    def _on_signature_count_ready(self, count: int, threshold: int):
        total_disp = threshold if threshold is not None else '?'
        self.sign_status_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'signature_count',
            ).format(count, total_disp),
        )
        self.sign_status_label.show()
        if self.is_multisig:
            # Watch-only multisig uses post-to-bridge as primary action.
            # Signers keep 'Sign PSBT' as primary action.
            self.inspection_details.btn_primary.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'post_to_multisig' if self.is_watch_only else 'sign_psbt',
                ),
            )
            if self.is_initiator_of_pending:
                self.inspection_details.btn_primary.hide()
                self.inspection_details.btn_reject.hide()
            else:
                self.inspection_details.btn_primary.show()
                self.inspection_details.btn_reject.show()

        # Re-evaluate button state after signature count is ready
        self.handle_button_enable()

    def _update_signature_progress(self):
        """Update the signature progress label for multisig (e.g., 1 of 3)."""
        # Reset validation state whenever text changes
        self.is_psbt_validated = False
        self.handle_button_enable()

        current_text = self.broadcast_transaction_input.toPlainText().strip()
        parsed = BroadcastTransactionService.parse_psbt_input(current_text)
        current_psbt = parsed.psbt

        progress_ctx = BroadcastTransactionService.prepare_signature_progress_ui_state(
            current_psbt, self.min_psbt_len, self._current_operation,
        )

        if not progress_ctx.has_valid_psbt:
            self.sign_status_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'signature_count',
                ).format(0, '?'),
            )
            # Toggle buttons
            self.inspection_details.btn_import.setEnabled(True)
            self.inspection_details.btn_import.show()
            self.inspection_details.btn_clear.setEnabled(False)
            self.inspection_details.btn_clear.hide()
            # Allow editing when no valid PSBT present
            self.broadcast_transaction_input.setReadOnly(False)
            self.inspection_details.show_inspection_details(False)
            return

        # Has PSBT content: Hide Import, Show Clear
        if self.is_multisig:
            self.inspection_details.btn_import.hide()
            self.inspection_details.btn_clear.show()
            self.inspection_details.btn_clear.setEnabled(True)
            # Lock input once content is present until user clears
            self.broadcast_transaction_input.setReadOnly(True)

        if self.is_multisig:
            if progress_ctx.should_trigger_direct:
                self._trigger_inspection(self._current_operation, current_psbt)
                return

            offline_mode = (
                SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET
                or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
            )
            if offline_mode and current_psbt:
                stored_purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(
                    current_psbt,
                )
                if parsed.purpose or stored_purpose or len(current_psbt) >= self.min_psbt_len:
                    self._trigger_inspection(None, current_psbt)
                    return

    def _trigger_inspection(self, operation: Operation | None, psbt_text: str):
        """
        Helper to trigger the transaction inspection (BTC and RGB).
        """
        parsed = BroadcastTransactionService.parse_psbt_input(psbt_text)
        psbt_body = parsed.psbt
        if not psbt_body:
            return

        # Always trigger PSBT inspection for standard Bitcoin details (TXID, Fee)
        self.view_model.broadcast_transaction_view_model.inspect_psbt(
            psbt_body,
        )

        ctx = BroadcastTransactionService.resolve_inspection_context(
            operation, parsed.purpose, psbt_body, self._rgb_expected,
        )

        # Offline wallets can get fascia_path from storage if it was saved during creation/import
        is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET
        self._stored_context = None
        if is_offline_wallet:
            self._stored_context = BroadcastTransactionService.get_psbt_rgb_context(
                psbt_body,
            )

        rgb_expected = ctx.rgb_expected
        if is_offline_wallet:
            rgb_expected = bool(
                self._stored_context and self._stored_context.get(
                    'fascia_path'),
            )

        self.inspection_details.show_inspection_details(True)
        self._rgb_expected = rgb_expected
        self._is_inflation_context = ctx.is_inflation

        # Trigger RGB inspection if expected
        if rgb_expected:
            if operation:
                op_ctx = operation.details
                if op_ctx and bool(op_ctx.fascia_path):
                    entropy = op_ctx.entropy if op_ctx.entropy is not None else 0
                    self.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                        op_ctx.fascia_path,
                        psbt_body,
                        entropy,
                    )
            elif self._stored_context:
                self.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                    self._stored_context['fascia_path'],
                    psbt_body,
                    self._stored_context.get('entropy') or 0,
                )

    def _on_import_psbt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import PSBT', '', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            with open(file_path, encoding='utf-8') as f:
                text = (f.read() or '').strip()

            # Accept purpose-prefixed format: psbt:<purpose>:<base64>
            parsed = BroadcastTransactionService.parse_psbt_input(text)
            psbt_only = parsed.psbt
            if not psbt_only:
                ToastManager.error(description='Invalid PSBT file content')
                return

            self._programmatic_psbt_set = True
            self.broadcast_transaction_input.setPlainText(psbt_only)

            if self.is_multisig:
                self._update_signature_progress()
            self.handle_button_enable()
        except Exception as e:
            ToastManager.show_toast(
                parent=self,
                preset=ToastPreset.ERROR,
                description=f'Failed to read PSBT file: {e}',
            )

    def _on_export_psbt(self):
        current_text = self.broadcast_transaction_input.toPlainText().strip()
        parsed = BroadcastTransactionService.parse_psbt_input(current_text)
        purpose = parsed.purpose
        current_psbt = parsed.psbt
        if not current_psbt:
            ToastManager.error(description='No PSBT to export')
            return

        # Prefer exporting with purpose prefix when possible (watch-only/offline UX)
        if purpose is None:
            purpose = BroadcastTransactionService.get_psbt_purpose_from_storage(
                current_psbt,
            )
        export_text = current_psbt
        if purpose:
            export_text = f"psbt:{purpose}:{current_psbt}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export PSBT', 'transaction.psbt', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(export_text)
            ToastManager.success(description='PSBT exported successfully')
        except Exception as e:
            ToastManager.error(
                description=f'Failed to write PSBT file: {e}',
            )

    def _on_clear_psbt(self):
        """Clear the current PSBT and reset UI state."""
        self.broadcast_transaction_input.clear()
        self.broadcast_transaction_input.setReadOnly(False)
        self._current_operation = None
        self.pending_operation = None
        self._psbt_details = None
        self._rgb_details = None
        self.is_psbt_validated = False
        self.inspection_details.hide()
        if self.is_multisig:
            try:
                self.sign_status_label.hide()
            except Exception:
                pass
        self.handle_button_enable()

    def update_loading_state(self, is_loading: bool):
        """
        Updates the loading state of the broadcast/sign button.
        """
        if is_loading:
            self.render_timer.start()
            self.broadcast_button.start_loading()
            self.broadcast_button.setEnabled(False)
            # Disable reject and clear buttons during loading
            self.inspection_details.btn_reject.setEnabled(False)
            self.inspection_details.btn_clear.setEnabled(False)
        else:
            self.render_timer.stop()
            self.broadcast_button.stop_loading()
            # Re-enable reject and clear buttons
            self.inspection_details.btn_reject.setEnabled(True)
            self.inspection_details.btn_clear.setEnabled(True)
        self.handle_button_enable()

    def update_primary_button_state(self, is_loading):
        """Update the primary action button loading/enabled state."""
        self.inspection_details.set_primary_loading(is_loading)
        self.handle_button_enable()

    def update_reject_button_state(self, is_loading):
        """Update the reject button loading/enabled state."""
        self.inspection_details.set_reject_loading(is_loading)
        self.handle_button_enable()

    def _load_psbts_for_signing(self) -> None:
        """Populate the PSBT input from stored unsigned drafts or passed operation."""
        if self.is_multisig:
            data = BroadcastTransactionService.multisig_sign_loading_data(
                self.pending_operation,
            )
            if data['has_pending']:
                self.is_initiator_of_pending = data['is_initiator']
                self.method_selector_label.hide()
                self.method_selector.hide()
                self._programmatic_psbt_set = True
                self.broadcast_transaction_input.setPlainText(data['psbt'])
                self.broadcast_transaction_input.setReadOnly(True)
                self._current_operation = data['operation']
                self._on_psbt_text_changed()  # Trigger inspection via standard path
                if not self.is_initiator_of_pending:
                    self.inspection_details.btn_reject.show()
                self.handle_button_enable()
                return

            self.method_selector_label.hide()
            self.method_selector.hide()
            self.broadcast_transaction_input.clear()
            self.inspection_details.set_primary_enabled(False)

        self.view_model.broadcast_transaction_view_model.load_psbts(
            is_signed=False,
        )

    def handle_nia_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        if not self.isVisible():
            return
        # Stop button loading when showing hardware dialog
        self.broadcast_button.stop_loading()
        self.broadcast_button.setEnabled(True)
        self.hw_dialog.update_dialog(message, dialog_type)
        self.hw_dialog.cancel_button.clicked.connect(self._reset_button_states)
        if not self.hw_dialog.isVisible():
            self.hw_dialog.show()

    def _reset_button_states(self):
        """Reset all button states after HW dialog is cancelled."""
        hardware_client_store.stop_client()
        self.broadcast_button.stop_loading()
        self.broadcast_button.setEnabled(True)
        self.inspection_details.btn_reject.setEnabled(True)
        self.inspection_details.btn_clear.setEnabled(True)
        self.handle_button_enable()

    def show_signed_psbt_page(self, psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        if not (psbt and self.isVisible()):
            return

        if self.hw_dialog.isVisible():
            self.hw_dialog.accept()

        if self.is_multisig:
            ToastManager.success(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_signed_successfully',
                ),
            )
            close_button_navigation(self)
        else:
            model = BroadcastTransactionService.receive_asset_model_for_signed_psbt(
                psbt,
            )
            self.view_model.page_navigation.receive_asset_page(model)

    def _load_psbts_for_broadcast(self) -> None:
        """Populate the PSBT input from stored signed drafts for broadcasting.
        Reuse the same selector as a PSBT selector (no separate widget).
        """
        self.view_model.broadcast_transaction_view_model.load_psbts(
            is_signed=True,
        )

    def closeEvent(self, event):  # pylint:disable=invalid-name
        """Ensure loading is stopped when widget is closed."""
        try:
            if hasattr(self, 'inspection_details') and self.inspection_details:
                self.inspection_details.inspect_loading.hide()
        except Exception:
            pass
        if hasattr(super(), 'closeEvent'):
            super().closeEvent(event)
