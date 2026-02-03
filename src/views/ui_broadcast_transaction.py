# pylint: disable=too-many-instance-attributes, too-many-statements, too-many-branches, too-many-lines
"""
Widget for broadcasting signed transactions (PSBTs) in the application.
"""
from __future__ import annotations

import base64
from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
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

from accessible_constant import BROADCAST_TRANSACTION_METHOD_SELECTOR
from accessible_constant import BROADCAST_TRANSACTION_PAGE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON
from accessible_constant import BROADCAST_TRANSACTION_PSBT_INPUT
from accessible_constant import SIGN_PSBT_PAGE_BUTTON
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import ToastPreset
from src.model.enums.enums_model import WalletSignatureType
from src.utils.common_utils import close_button_navigation
from src.utils.common_utils import get_current_wallet_mode_config
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_XPUB
from src.utils.hardware_client_store import hardware_client_store
from src.utils.helpers import load_stylesheet
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.views.components.loading_screen import LoadingTranslucentScreen


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
        self._op_details_ready = False
        self._inspection_epoch = 0
        self.is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        # Minimum characters to consider PSBT input valid for enabling Sign button
        self.min_psbt_len = 80
        self.is_initiator_of_pending = False
        self.is_psbt_validated = False  # Strict validation flag
        self._current_operation = None
        # Avoid repeated inspections on the same PSBT
        self._last_inspected_psbt: str | None = None
        self._rgb_expected: bool = False
        self._is_inflation_context: bool = False
        self._signals_connected: bool = False
        self._programmatic_psbt_set: bool = False
        self._pending_transfer_type: str | None = None

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setObjectName('grid_layout')
        # Center main widget horizontally with equal side columns
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)
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


        # Apply initial/base dimensions
        if self.is_multisig:
            self.broadcast_transaction_widget.setMinimumSize(QSize(800, 450))
            self.broadcast_transaction_widget.setMaximumSize(QSize(800, 450))
        else:
            self.broadcast_transaction_widget.setMinimumSize(QSize(630, 450))
            self.broadcast_transaction_widget.setMaximumSize(QSize(630, 450))
        self.vertical_layout = QVBoxLayout(self.broadcast_transaction_widget)
        self.vertical_layout.setObjectName('verticalLayout')
        # Multisig: tighten and equalize inner paddings similar to reference
        if self.is_multisig:
            self.vertical_layout.setContentsMargins(22, 8, 22, 10)
        self.vertical_layout.addSpacing(4)

        # Loading overlay (matches other pages): covers the card while inspections run
        self._loading_overlay = LoadingTranslucentScreen(parent=self, description_text='Loading')
        self._loading_overlay.stop()

        self.broadcast_transaction_title_layout = QHBoxLayout()
        self.broadcast_transaction_title_layout.setObjectName(
            'broadcast_transaction_title_layout',
        )
        self.broadcast_transaction_title_layout.setContentsMargins(
            22, -1, 22, -1,
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
            self.close_btn_broadcast_transaction_page,
        )
        # Multisig: ensure close button is vertically centered next to the title
        if self.is_multisig:
            self.broadcast_transaction_title_layout.setContentsMargins(
                0, 0, 0, 0,
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
        self.horizontal_layout_2 = QHBoxLayout()
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
        if self.is_multisig:
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
            self.broadcast_transaction_input.setMinimumHeight(50)
            self.broadcast_transaction_input.setMaximumHeight(155)
        # Base styling (no font override). We will apply compact monospace font
        # only when multisig PSBT is validated and details are showing.
        self._psbt_input_base_style = (
            load_stylesheet('views/qss/scrollbar.qss') +
            '\nQPlainTextEdit#broadcast_transaction_input { border: none; border-radius: 12px; padding: 12px; background-color: rgba(255,255,255,0.06); }'
        )
        self.broadcast_transaction_input.setStyleSheet(self._psbt_input_base_style)
        self.horizontal_spacer_1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum,
        )
        self.horizontal_layout_1.addWidget(self.broadcast_transaction_input)
        # self.horizontal_layout_1.addSpacerItem(self.horizontal_spacer_1)
        self.vertical_layout.addLayout(
            self.horizontal_layout_1,
        )

        # Inspection Details Frame (Multisig only): Show only TXID and Amount
        if self.is_multisig:
            self.inspection_frame = QFrame(self.broadcast_transaction_widget)
            self.inspection_frame.setObjectName('inspection_frame')
            self.inspection_frame.setFrameShape(QFrame.NoFrame)
            self.inspection_frame.setFrameShadow(QFrame.Plain)
            self.inspection_frame.setContentsMargins(5,0,0,0)
            self.inspection_frame.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
            )
            self.inspection_frame.hide()

            self.inspect_outer_layout = QVBoxLayout(self.inspection_frame)
            # Revert to original margins for classic (no-scroll) design
            self.inspect_outer_layout.setContentsMargins(0, 0, 0, 0)
            self.inspect_outer_layout.setSpacing(0)

            # Lightweight loading label shown while PSBT inspection runs
            self.inspect_loading = QLabel(self.inspection_frame)
            self.inspect_loading.setObjectName('inspect_loading')
            self.inspect_loading.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'loading',
                ),
            )
            self.inspect_loading.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            )
            self.inspect_loading.hide()
            self.inspect_outer_layout.addWidget(self.inspect_loading)

            # Section title
            self.details_title = QLabel(self.inspection_frame)
            self.details_title.setObjectName('details_title')
            self.details_title.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_details_title',
                ),
            )
            # Let global theme control colors; add spacing and slight emphasis
            self.details_title.setStyleSheet('padding: 10px 0px;')
            self.inspect_outer_layout.addWidget(self.details_title)

            self.details_card = QFrame(self.inspection_frame)
            self.details_card.setObjectName('inspection_card')
            # Bring back a subtle container background (no backgrounds on inner tiles)
            self.details_card.setStyleSheet(
                'QFrame#inspection_card { border: none; border-radius: 12px; background-color: rgba(255,255,255,0.06); }'
            )
            # Ensure absolutely no native frame border is drawn
            self.details_card.setFrameShape(QFrame.NoFrame)
            self.details_card.setFrameShadow(QFrame.Plain)
            self.details_card.setFixedWidth(747)

            # Grid layout with 2 columns to mimic the shared mock
            self.inspect_grid = QGridLayout(self.details_card)
            # Normalized margins and spacing: equal padding on all sides and equal gaps
            self.inspect_grid.setContentsMargins(10, 10, 10, 10)
            self.inspect_grid.setHorizontalSpacing(5)
            self.inspect_grid.setVerticalSpacing(5)
            # Enforce half/half column widths
            self.inspect_grid.setColumnStretch(0, 1)
            self.inspect_grid.setColumnStretch(1, 1)
            self.inspect_grid.setColumnMinimumWidth(0, 200)
            self.inspect_grid.setColumnMinimumWidth(1, 200)

            # Revert to classic (no-scroll) details card
            self.inspect_outer_layout.addWidget(self.details_card)

            def create_detail_row(label_text, value_id):
                tile = QFrame(self.details_card)
                tile.setObjectName('tile_frame')
                # Plain background: no tile background, no rounded corners
                tile.setStyleSheet(
                    'QFrame#tile_frame { border: none; border-radius: 0px; background-color: transparent; }'
                )
                tile.setFixedHeight(80)
                tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                tile_layout = QVBoxLayout(tile)
                tile_layout.setContentsMargins(10, 10, 10, 10)
                tile_layout.setSpacing(0)
                lbl = QLabel(label_text, tile)
                lbl.setStyleSheet('color: rgba(255,255,255,0.72); font-size: 14px;font-weight: 600;')
                val = QLabel(tile)
                val.setObjectName(value_id)
                val.setWordWrap(True)
                val.setStyleSheet('font-size: 14px;')
                lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                val.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                lbl.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
                val.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                val.setMinimumWidth(0)
                tile_layout.addWidget(lbl)
                tile_layout.addWidget(val)
                return tile, lbl, val

            self.tile_txid, self.lbl_txid, self.val_txid = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id_label',
                ), 'val_txid',
            )
            # TXID now uses half width (left column)
            self.inspect_grid.addWidget(self.tile_txid, 0, 0, 1, 1)
            self.val_txid.setWordWrap(True)
            try:
                self.val_txid.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                self.val_txid.setMinimumWidth(0)
            except Exception:
                pass

            # Asset ID (for multisig RGB operations like inflation)
            self.tile_asset, self.lbl_asset_id, self.val_asset_id = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_id_label',
                ), 'val_asset_id',
            )
            # Asset ID now uses half width (right column of first row)
            self.inspect_grid.addWidget(self.tile_asset, 0, 1, 1, 1)
            self.val_asset_id.setWordWrap(True)
            try:
                self.val_asset_id.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                self.val_asset_id.setMinimumWidth(0)
            except Exception:
                pass

            # Hide until we have RGB details
            self.tile_asset.hide()

            self.tile_amount, self.lbl_amount, self.val_amount = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_field_label',
                ), 'val_amount',
            )
            # Amount in row 1, column 0
            self.inspect_grid.addWidget(self.tile_amount, 1, 0)

            # Transfer Type (RGB send vs inflation)
            self.tile_ttype, self.lbl_transfer_type, self.val_transfer_type = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transfer_type_label',
                ), 'val_transfer_type',
            )
            # Place Transfer Type on row 3, column 0 (pairs with Confirmations on 3,1)
            self.inspect_grid.addWidget(self.tile_ttype, 3, 0)
            # Hide initially; shown when RGB inspection is available
            self.tile_ttype.hide()

            # Min Confirmations (RGB send/inflation context)
            self.tile_minconf, self.lbl_min_conf, self.val_min_conf = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'min_confirmations',
                ), 'val_min_conf',
            )
            # Place Confirmations on row 3, column 1 (pairs with Type)
            self.inspect_grid.addWidget(self.tile_minconf, 3, 1)
            self.tile_minconf.hide()

            # Destination
            self.tile_destination, self.lbl_destination, self.val_destination = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'destination_label',
                ), 'val_destination',
            )
            self.inspect_grid.addWidget(self.tile_destination, 0, 1, 1, 1)
            self.val_destination.setWordWrap(True)

            # Fee
            self.tile_fee, self.lbl_fee, self.val_fee = create_detail_row(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'fee_sats_label',
                ), 'val_fee',
            )
            # Fee aligns with Amount in row 1, column 1
            self.inspect_grid.addWidget(self.tile_fee, 1, 1)


            self.vertical_layout.addWidget(self.inspection_frame)

        self.broadcast_button_horizontal_layout = QHBoxLayout()
        self.broadcast_button_horizontal_layout.setObjectName(
            'broadcast_button_horizontal_layout',
        )
        self.broadcast_button_horizontal_layout.setContentsMargins(
            -1, 6, -1, 14,
        )
        self.broadcast_button = PrimaryButton()
        self.broadcast_button.setMinimumSize(QSize(0, 40))
        if self.priv.can_broadcast_psbt:
            self.broadcast_button.setMaximumSize(QSize(270, 16777215))
            self.broadcast_button.setAccessibleName(
                BROADCAST_TRANSACTION_PAGE_BUTTON,
            )
        else:
            self.broadcast_button.setMaximumSize(QSize(270, 16777215))
            self.broadcast_button.setAccessibleName(SIGN_PSBT_PAGE_BUTTON)
        if not self.is_multisig:
            self.broadcast_button_horizontal_layout.addWidget(
                self.broadcast_button,
            )
            self.vertical_layout.addLayout(
                self.broadcast_button_horizontal_layout,
            )

        # Centered actions row (multisig only)
        if self.is_multisig:
            self.actions_center_row = QHBoxLayout()
            self.actions_center_row.setContentsMargins(0, 14, 0, 8)
            self.actions_center_row.setSpacing(16)
            self.actions_center_row.addStretch(1)
            self.btn_import = PrimaryButton()
            self.btn_import.setFixedWidth(160)
            self.btn_import.setMinimumHeight(40)

            self.btn_export = PrimaryButton()
            self.btn_export.setFixedWidth(160)
            self.btn_export.setMinimumHeight(40)
            self.btn_export.setEnabled(False)

            self.btn_clear = PrimaryButton()
            self.btn_clear.setFixedWidth(160)
            self.btn_clear.setMinimumHeight(40)
            self.btn_clear.setEnabled(False)
            self.btn_clear.hide()

            # Reject/NACK button for multisig reviewers
            self.btn_reject = PrimaryButton()
            self.btn_reject.setFixedWidth(160)
            self.btn_reject.setMinimumHeight(40)

            self.broadcast_button.setFixedWidth(160)
            self.broadcast_button.setMinimumHeight(40)

            self.actions_center_row.addWidget(self.btn_import)
            self.actions_center_row.addWidget(self.btn_export)
            self.actions_center_row.addWidget(self.btn_clear)
            self.actions_center_row.addWidget(self.btn_reject)
            self.actions_center_row.addWidget(self.broadcast_button)
            self.actions_center_row.addStretch(1)
            self.vertical_layout.addLayout(self.actions_center_row)

        # Prepare PSBT storage for optional signing flow
        if self.is_multisig:
            self._psbt_items: list[dict] = []
        # Prepare PSBT storage for broadcast flow
        if self.priv.can_broadcast_psbt:
            self._psbt_signed_items: list[dict] = []

        # Always hide Export in this flow (not needed now)
        if hasattr(self, 'btn_export'):
            try:
                self.btn_export.hide()
                self.btn_export.setEnabled(False)
            except Exception:
                pass

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
        """
        Set up connections for UI elements.
        """
        # Prevent duplicate connections if setup is called more than once
        if self._signals_connected:
            return
        self.broadcast_transaction_input.textChanged.connect(
            self.handle_button_enable,
        )
        if self.is_multisig:
            self.broadcast_transaction_input.textChanged.connect(
                self._update_signature_progress,
            )
        if not self.is_multisig:
            self.broadcast_button.clicked.connect(self.send_asset)
        self.close_btn_broadcast_transaction_page.clicked.connect(
            lambda: close_button_navigation(self),
        )
        self.view_model.broadcast_transaction_view_model.is_loading.connect(
            self.update_loading_state,
        )
        self.view_model.broadcast_transaction_view_model.tx_broadcasted.connect(
            lambda: close_button_navigation(self),
        )
        self.view_model.broadcast_transaction_view_model.finalized_psbt.connect(
            self.show_signed_psbt_page,
        )
        self.view_model.broadcast_transaction_view_model.hw_dialog_update.connect(
            self.handle_nia_hw_dialog,
        )
        if self.is_multisig:
            self.btn_import.clicked.connect(self._on_import_psbt)
            self.btn_export.clicked.connect(self._on_export_psbt)
            self.btn_clear.clicked.connect(self._on_clear_psbt)
            self.btn_reject.clicked.connect(self._on_reject_operation)
            # For multisig signer: sign and post back to bridge
            self.broadcast_button.clicked.connect(
                self._on_sign_and_post_multisig,
            )
            # Keep export disabled/hidden for now even after signing
            self.view_model.broadcast_transaction_view_model.finalized_psbt.connect(
                self._on_finalized_psbt_ready,
            )
        # Connect inspection result signal
        self.view_model.broadcast_transaction_view_model.psbt_inspection_ready.connect(
            self._handle_psbt_inspection_result,
        )
        # RGB transfer inspection result
        self.view_model.broadcast_transaction_view_model.rgb_transfer_inspection_ready.connect(
            self._handle_rgb_transfer_inspection_result,
        )
        # Connect pending operation result
        self.view_model.broadcast_transaction_view_model.pending_operation_ready.connect(
            self._on_pending_operation_ready,
        )
        # Trigger inspection when user pastes/types a PSBT (sidebar or not)
        self.broadcast_transaction_input.textChanged.connect(self._on_psbt_text_changed)
        self.view_model.broadcast_transaction_view_model.is_reject_loading.connect(
            self.update_reject_button_state,
        )
        self._signals_connected = True

    @staticmethod
    def _wrap_to_two_lines(text: str, first_line_chars: int = 34) -> str:
        """Force a two-line display by inserting a newline near the middle.
        Ensures long continuous strings (no spaces) wrap within half-width tiles.
        """
        if not isinstance(text, str):
            return str(text)
        if len(text) <= first_line_chars:
            return text
        return text[:first_line_chars] + "\n" + text[first_line_chars:]

    def _apply_base_sizes(self):
        """Apply base card/input sizes for multisig."""
        if not self.is_multisig:
            return
        try:
            self.broadcast_transaction_widget.setMinimumSize(QSize(800, 450))
            self.broadcast_transaction_widget.setMaximumSize(QSize(800, 450))
            self.broadcast_transaction_input.setFixedWidth(747)
            self.broadcast_transaction_input.setMaximumHeight(200)
            # Revert to base styling (no compact monospace) when collapsing
            self.broadcast_transaction_input.setStyleSheet(self._psbt_input_base_style)
        except Exception:
            pass

    def _apply_expanded_sizes(self):
        """Apply expanded card/input sizes for multisig when PSBT details exist."""
        if not self.is_multisig:
            return
        try:
            self.broadcast_transaction_widget.setMinimumSize(QSize(800, 780))
            self.broadcast_transaction_widget.setMaximumSize(QSize(800, 780))
            # Fill width; keep compact fixed height so it doesn't feel bulky
            self.broadcast_transaction_input.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed,
            )
        except Exception:
            pass

    def _on_psbt_text_changed(self):
        """Auto-trigger inspection and sizing when the user pastes/types a PSBT."""
        if self._programmatic_psbt_set:
            # Ignore textChanged events caused by our own setPlainText
            self._programmatic_psbt_set = False
            return
        psbt_text = self.broadcast_transaction_input.toPlainText().strip()
        if not self.is_multisig:
            return
        if psbt_text and len(psbt_text) >= self.min_psbt_len:
            # Do NOT expand yet; keep base size while loading
            if self.is_multisig:
                self.inspection_frame.hide()
                self.details_title.hide()
                self.sign_status_label.hide()
                self._loading_overlay.start()
                self._loading_overlay.make_parent_disabled_during_loading(True)

            # New epoch for this paste
            self._inspection_epoch += 1
            self._psbt_details = None
            self._rgb_details = None
            # Default: do not expect RGB unless a pending operation later sets it
            self._rgb_expected = False
            self._op_details_ready = False
            # Try to kick off an inspection if available
            if hasattr(self.view_model.broadcast_transaction_view_model, 'inspect_psbt'):
                self.view_model.broadcast_transaction_view_model.inspect_psbt(psbt_text)
        else:
            # Collapse when cleared
            self._apply_base_sizes()
            self.inspection_frame.hide()
            self.details_title.hide()
            self.inspect_loading.hide()
            self.sign_status_label.hide()
            self._loading_overlay.stop()
            self._loading_overlay.make_parent_disabled_during_loading(False)

    def _render_inspection_if_ready(self):
        """Show Transaction Details only when required data is ready."""
        if self._psbt_details is None:
            return
        # In multisig, only wait for RGB if it is actually expected for this PSBT
        if self.is_multisig and self._rgb_expected and self._rgb_details is None:
            return
        # Ignore if user cleared/changed PSBT meanwhile
        current_psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not current_psbt or len(current_psbt) < self.min_psbt_len:
            return
        self.inspection_frame.show()
        self.details_title.show()
        self.details_card.show()
        self.is_psbt_validated = True
        self.handle_button_enable()
        if self.is_multisig:
            self.sign_status_label.show()
            self._apply_expanded_sizes()
            # Now that info frame is visible, apply compact input font
            self.broadcast_transaction_input.setStyleSheet(
                self._psbt_input_base_style +
                '\nQPlainTextEdit#broadcast_transaction_input { font: 12px "JetBrains Mono", monospace; }'
            )
        # Hide loader once details are visible
        self._loading_overlay.stop()
        self._loading_overlay.make_parent_disabled_during_loading(False)

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

        # Multisig: set subtitle and actions row texts/tooltips via i18n
        if self.is_multisig:
            self.broadcast_subtitle_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'paste_or_import_psbt',
                ),
            )
            # Buttons
            self.btn_import.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'import',
                ),
            )
            self.btn_export.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'export',
                ),
            )
            self.btn_clear.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'clear_all',
                ),
            )
            self.btn_reject.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'reject',
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
                'send_btc': self.view_model.broadcast_transaction_view_model.send_btc_end,
                'send_asset': self.view_model.broadcast_transaction_view_model.send_end,
                'inflate_asset': self.view_model.broadcast_transaction_view_model.inflate_end,
            }

            handler = purpose_map.get(
                purpose, self.view_model.broadcast_transaction_view_model.create_utxos_end,
            )
            handler(signed_psbt)

        else:
            # Determine purpose similarly for sign-only mode to set RGB mode
            if purpose is None and self._psbt_items:
                idx = self.method_selector.currentIndex() if self.method_selector.isVisible() else 0
                if 0 <= idx < len(self._psbt_items):
                    purpose = self._psbt_items[idx].get('purpose')

            # Enable RGB mode only for RGB asset signing; BTC/UTXO default to False
            hardware_client_store.set_rgb_mode(
                purpose in ('send_asset', 'inflate_asset'),
            )

            self.view_model.broadcast_transaction_view_model.sign_and_finalize_psbt(
                signed_psbt,
            )

    def on_success_sent_navigation(self):
        """
        Navigate to collectibles or fungibles page when the originating page is create ln invoice.
        """
        self.view_model.page_navigation.fungibles_asset_page()

    def _cleanup_secondary_draft_if_any(self, *_):
        """Delete the latest active IFA secondary draft (watch-only/offline)."""
        try:
            svc = WalletDataService.get_session()
            if svc is None:
                return
            # Prefer precise cleanup by PSBT content if available, and guard by purpose
            psbt_text = self.broadcast_transaction_input.toPlainText().strip()
            purpose = None
            if psbt_text.startswith('psbt:'):
                parts = psbt_text.split(':', 2)
                if len(parts) == 3:
                    purpose, _psbt_only = parts[1], parts[2]
                elif len(parts) == 2:
                    _psbt_only = parts[1]
                else:
                    _psbt_only = psbt_text
            else:
                _psbt_only = psbt_text

            # If purpose is known and not inflate, do nothing
            if purpose is not None and purpose != 'inflate_asset':
                return

            # First, try exact delete by PSBT content
            if _psbt_only:
                try:
                    if svc.delete_secondary_draft_by_psbt(_psbt_only):
                        return
                except Exception:
                    pass

            # If purpose explicitly 'inflate_asset', fallback to deleting latest active draft
            if purpose == 'inflate_asset':
                latest = svc.get_latest_active_secondary_draft()
                if isinstance(latest, dict) and latest.get('id') is not None:
                    svc.delete_ifa_secondary_draft(int(latest['id']))
        except Exception:
            # Silent best-effort cleanup
            pass

    def handle_button_enable(self):
        """
        Enable or disable the broadcast button based on input and method selection.
        """
        text = self.broadcast_transaction_input.toPlainText()
        has_input = bool(text) and (len(text.strip()) >= self.min_psbt_len)
        if self.priv.can_broadcast_psbt:
            selector_visible = self.method_selector.isVisible()
            method_ok = (not selector_visible) or (
                self.method_selector.currentIndex() >= 0
            )
            self.broadcast_button.setEnabled(has_input and method_ok)
        else:
            # Signer flow
            if self.is_multisig:
                # Strict validation: must have input AND be validated by inspection
                # Additionally require a pending operation (operation_idx) to be present
                can_act = has_input and self.is_psbt_validated and (self.pending_operation is not None)
                self.broadcast_button.setEnabled(can_act)
                self.btn_reject.setEnabled(can_act)
            else:
                self.broadcast_button.setEnabled(has_input)

    def _on_finalized_psbt_ready(self):
        """Our wallet has signed successfully; allow exporting the signed PSBT."""
        if self.is_multisig:
            # Keep export hidden/disabled as per current requirement
            try:
                self.btn_export.hide()
                self.btn_export.setEnabled(False)
            except Exception:
                pass
            self.btn_import.setEnabled(False)
            self.broadcast_button.setEnabled(False)

    def _on_sign_and_post_multisig(self):
        """Sign the PSBT and post back to the multisig bridge."""
        psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not psbt:
            ToastManager.error(description='No PSBT to sign')
            return

        # Get the operation index for posting back
        operation_idx = self.pending_operation.operation_idx if self.pending_operation else None
        print('operation_idx:', operation_idx,self.pending_operation)

        # Call the viewmodel to sign and post
        self.view_model.broadcast_transaction_view_model.sign_and_post_multisig(
            psbt, operation_idx,
        )

    def _on_reject_operation(self):
        """Reject the pending operation (NACK) without signing."""
        operation_idx = None
        if self.pending_operation:
            operation_idx = self.pending_operation.operation_idx
        elif self._current_operation:
            # _current_operation is the inner Operation (no operation_idx)
            # Fall back to pending_operation if available
            pass
        if operation_idx is None:
            ToastManager.error(description='Operation not found to reject')
            return
        self.view_model.broadcast_transaction_view_model.respond_nack(
            operation_idx,
        )

    # ----- Multisig helpers -----
    def _update_signature_progress(self):
        """Update the signature progress label for multisig (e.g., 1 of 3)."""
        # Reset validation state whenever text changes
        self.is_psbt_validated = False
        self.handle_button_enable()

        _, total = SettingRepository.get_multisig_config()
        current_psbt = self.broadcast_transaction_input.toPlainText().strip()

        if not current_psbt or len(current_psbt) < self.min_psbt_len:
            total_disp = total if total is not None else '?'
            self.sign_status_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'signature_count',
                ).format(0, total_disp),
            )
            self.btn_export.setEnabled(False)
            # Enable import if cleared
            self.btn_import.setEnabled(True)
            self.btn_import.show()
            self.btn_clear.setEnabled(False)
            self.btn_clear.hide()
            # Allow editing when no valid PSBT present
            self.broadcast_transaction_input.setReadOnly(False)

            self.inspection_frame.hide()
            return

        # Has PSBT content: Hide Import, Show Clear
        if self.is_multisig:
            self.btn_import.hide()
            self.btn_clear.show()
            self.btn_clear.setEnabled(True)
            # Lock input once content is present until user clears
            self.broadcast_transaction_input.setReadOnly(True)

        if self.is_multisig:
            # Check for a matching pending operation context
            if self._current_operation:
                # _current_operation is the inner Operation object (extracted from OperationInfo)
                # We verify if the PSBT text matches strictly
                if self._current_operation.psbt == current_psbt:
                    self._trigger_inspection(self._current_operation, current_psbt)
                    return

    def _trigger_inspection(self, operation, psbt_text: str):
        """
        Helper to trigger the inspection.
        We always use inspect_psbt to get the standard Bitcoin details (TXID, Fee, etc.).
        RGB details are populated directly from the operation context via _update_ui_with_operation_details.
        """
        # Debounce repeated inspections for the same PSBT
        if isinstance(self._last_inspected_psbt, str) and self._last_inspected_psbt == psbt_text:
            return
        self._last_inspected_psbt = psbt_text
        # Always inspect PSBT for BTC details
        self.view_model.broadcast_transaction_view_model.inspect_psbt(
            psbt_text,
        )
        op = getattr(operation, "details", None)

        # If we have consignment paths, inspect RGB strictly for Asset ID/Amount
        consignment_paths = getattr(op, 'consignment_paths', None) if op is not None else None
        self._rgb_expected = bool(consignment_paths)
        if self._rgb_expected:
            self.view_model.broadcast_transaction_view_model.inspect_rgb_transfer(
                consignment_paths, psbt_text, op.entropy,
            )
        else:
            # No RGB consignment (e.g., InflationDetails). If inflation fields exist, populate directly.
            asset_id = getattr(op, 'asset_id', None) if op is not None else None
            amount = getattr(op, 'amount', None) if op is not None else None
            min_conf = getattr(op, 'min_confirmations', None) if op is not None else None
            self._is_inflation_context = bool(asset_id is not None or amount is not None or min_conf is not None)
            if self._is_inflation_context:
                try:
                    if asset_id is not None:
                        self.lbl_asset_id.setVisible(True)
                        self.val_asset_id.setVisible(True)
                        self.val_asset_id.setText(self._wrap_to_two_lines(str(asset_id)))
                        if hasattr(self, 'tile_asset'):
                            self.tile_asset.show()
                    if isinstance(amount, int) and amount > 0:
                        self.lbl_amount.setVisible(True)
                        self.val_amount.setVisible(True)
                        self.val_amount.setText(f"{amount:,}")
                        try:
                            self.val_amount.setStyleSheet('color: #10B981; font-weight: 700;')
                        except Exception:
                            pass
                        if hasattr(self, 'tile_amount'):
                            self.tile_amount.show()
                    if isinstance(min_conf, int):
                        self.lbl_min_conf.setVisible(True)
                        self.val_min_conf.setVisible(True)
                        self.val_min_conf.setText(str(min_conf))
                        if hasattr(self, 'tile_minconf'):
                            self.tile_minconf.show()
                    # Explicitly show transfer type for inflation path
                    if hasattr(self, 'tile_ttype'):
                        self.tile_ttype.show()
                        self.lbl_transfer_type.setVisible(True)
                        self.val_transfer_type.setVisible(True)
                        t_text = QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'inflation',
                        )
                        self.val_transfer_type.setText(t_text if t_text else 'inflation')
                except Exception:
                    pass
            # Render immediately without waiting for RGB
            self._render_inspection_if_ready()

    def _handle_psbt_inspection_result(self, details):
        """
        Handle the async PSBT inspection result from the signal.
        Populates TXID, Amount, Destination, Fee, Size from PsbtInspection.
        """
        if not details:
            self.inspection_frame.hide()
            if hasattr(self, 'details_title'):
                self.details_title.hide()
            self.is_psbt_validated = False
            self.handle_button_enable()
            if self.is_multisig:
                self.sign_status_label.hide()
                self._apply_base_sizes()
            return

        self._psbt_details = details
        self._render_inspection_if_ready()
        # Now that details are visible, apply compact monospace font to input
        if self.is_multisig:
            self.broadcast_transaction_input.setStyleSheet(
                self._psbt_input_base_style +
                '\nQPlainTextEdit#broadcast_transaction_input { font: 12px "JetBrains Mono", monospace; }'
            )

        # TXID
        self.val_txid.setText(self._wrap_to_two_lines(details.txid))

        # In inflation context, do not recompute Amount/Destination using BTC-only heuristics.
        # Keep prefilled RGB inflation amount and hide Destination.
        if getattr(self, '_is_inflation_context', False):
            # Hide destination tile explicitly
            self.lbl_destination.setVisible(False)
            self.val_destination.setVisible(False)
            if hasattr(self, 'tile_destination'):
                self.tile_destination.hide()
            # Also ensure Asset/Amount/MinConf are present from operation details
            try:
                op = getattr(self._current_operation, 'details', None)
                if op is not None:
                    asset_id = getattr(op, 'asset_id', None)
                    amount = getattr(op, 'amount', None)
                    min_conf = getattr(op, 'min_confirmations', None)
                    if asset_id is not None:
                        self.lbl_asset_id.setVisible(True)
                        self.val_asset_id.setVisible(True)
                        self.val_asset_id.setText(str(asset_id))
                        if hasattr(self, 'tile_asset'):
                            self.tile_asset.show()
                    if isinstance(amount, int) and amount > 0:
                        self.lbl_amount.setVisible(True)
                        self.val_amount.setVisible(True)
                        self.val_amount.setText(f"{amount:,}")
                        if hasattr(self, 'tile_amount'):
                            self.tile_amount.show()
                    if isinstance(min_conf, int):
                        self.lbl_min_conf.setVisible(True)
                        self.val_min_conf.setVisible(True)
                        self.val_min_conf.setText(str(min_conf))
                        if hasattr(self, 'tile_minconf'):
                            self.tile_minconf.show()
            except Exception:
                pass
            # Ensure transfer type is visible as 'Inflation'
            try:
                if hasattr(self, 'tile_ttype'):
                    self.tile_ttype.show()
                    self.lbl_transfer_type.setVisible(True)
                    self.val_transfer_type.setVisible(True)
                    t_text = QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'inflation',
                    )
                    self.val_transfer_type.setText(t_text if t_text else 'Inflation')
            except Exception:
                pass
            # Show/update fee only
            fee_sat = getattr(details, 'fee_sat', None)
            if isinstance(fee_sat, int) and fee_sat >= 0:
                self.lbl_fee.setVisible(True)
                self.val_fee.setVisible(True)
                self.val_fee.setText(f"{fee_sat:,} sats")
                if hasattr(self, 'tile_fee'):
                    self.tile_fee.show()
            else:
                self.lbl_fee.setVisible(False)
                self.val_fee.setVisible(False)
                self.val_fee.clear()
                if hasattr(self, 'tile_fee'):
                    self.tile_fee.hide()
            # Update signature status and exit early
            self._on_signature_count_ready(details.signature_count)
            if self.is_multisig:
                self.view_model.broadcast_transaction_view_model.fetch_pending_operation()
            return

        self.lbl_amount.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_field_label',
            ),
        )

        # BTC-only path: ensure Asset ID tile is hidden and we'll show Destination instead
        try:
            if hasattr(self, 'tile_asset'):
                self.tile_asset.hide()
            if hasattr(self, 'lbl_asset_id'):
                self.lbl_asset_id.setVisible(False)
            if hasattr(self, 'val_asset_id'):
                self.val_asset_id.setVisible(False)
        except Exception:
            pass

        # BTC-only: do not render Amount in this card. Hide amount tile entirely.
        try:
            if hasattr(self, 'tile_amount'):
                self.tile_amount.hide()
            self.lbl_amount.setVisible(False)
            self.val_amount.setVisible(False)
            self.val_amount.clear()
        except Exception:
            pass

        # Transfer Type (BTC-only): show only once pending operation classification arrives
        try:
            if hasattr(self, 'tile_ttype'):
                pending_key = getattr(self, '_pending_transfer_type', None)
                if pending_key in ('internal', 'btc_transfer'):
                    self.tile_ttype.show()
                    self.lbl_transfer_type.setVisible(True)
                    self.val_transfer_type.setVisible(True)
                    t_text = QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, pending_key,
                    )
                    fallback = 'Internal' if pending_key == 'internal' else 'BTC transfer'
                    self.val_transfer_type.setText(t_text if t_text else fallback)
                else:
                    self.tile_ttype.hide()
                    self.lbl_transfer_type.setVisible(False)
                    self.val_transfer_type.setVisible(False)
        except Exception:
            pass

        # BTC-only: hide Destination tile entirely.
        self.lbl_destination.setVisible(False)
        self.val_destination.setVisible(False)
        self.val_destination.clear()
        if hasattr(self, 'tile_destination'):
            self.tile_destination.hide()

        # BTC-only: layout compaction and ordering (do NOT affect RGB send/inflation flows)
        try:
            is_btc_only = not getattr(self, '_rgb_expected', False) and not getattr(self, '_is_inflation_context', False)
            if is_btc_only:
                self.broadcast_transaction_widget.setFixedHeight(660)
                # TXID spans full width in first row
                if hasattr(self, 'tile_txid'):
                    self.inspect_grid.addWidget(self.tile_txid, 0, 0, 1, 2)
                    self.val_txid.setText(details.txid)
                # Type (left) and Fee (right) on second row
                if hasattr(self, 'tile_ttype'):
                    self.inspect_grid.addWidget(self.tile_ttype, 1, 0, 1, 1)
                if hasattr(self, 'tile_fee'):
                    self.inspect_grid.addWidget(self.tile_fee, 1, 1, 1, 1)
        except Exception:
            pass

        # Fee: show if available (>=0)
        fee_sat = details.fee_sat
        if isinstance(fee_sat, int) and fee_sat >= 0:
            self.lbl_fee.setVisible(True)
            self.val_fee.setVisible(True)
            self.val_fee.setText(f"{fee_sat:,} sats")
            try:
                self.val_fee.setStyleSheet('font-weight: 700;')
            except Exception:
                pass

            if hasattr(self, 'tile_fee'):
                self.tile_fee.show()
        else:
            self.lbl_fee.setVisible(False)
            self.val_fee.setVisible(False)
            self.val_fee.clear()
            if hasattr(self, 'tile_fee'):
                self.tile_fee.hide()


        # In BTC-only path, hide confirmations/min-conf row if present
        try:
            if hasattr(self, 'tile_minconf'):
                self.tile_minconf.hide()
            if hasattr(self, 'lbl_min_conf'):
                self.lbl_min_conf.setVisible(False)
            if hasattr(self, 'val_min_conf'):
                self.val_min_conf.setVisible(False)
                self.val_min_conf.clear()
        except Exception:
            pass

        # Update signature progress
        self._on_signature_count_ready(details.signature_count)

        # Trigger bridge sync to get rich details (Entropy, Min Conf, Voting)
        if self.is_multisig:
            self.view_model.broadcast_transaction_view_model.fetch_pending_operation()

    def _on_pending_operation_ready(self, op_info):
        """
        Callback when bridge sync returns a pending operation (or None).
        We check if this operation matches the PSBT we are currently inspecting.
        """
        if not op_info:
            return

        current_psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not current_psbt:
            return

        operation = op_info.operation
        if not operation:
            return

        op_psbt = operation.psbt

        # If strings match, we found our operation!
        if op_psbt and op_psbt == current_psbt:
            # Store the inner Operation object
            self._current_operation = operation
            # Also set pending_operation so operation_idx is available for signing
            try:
                self.pending_operation = op_info
            except Exception:
                pass
            # Classify transfer type by details class name if available
            try:
                details_obj = getattr(operation, 'details', None)
                self._pending_transfer_type = None
                names = []
                if details_obj is not None:
                    names.append(type(details_obj).__name__)
                # Always include the enum variant name as a fallback, e.g. CREATE_UTXOS_TO_REVIEW
                try:
                    names.append(type(operation).__name__)
                except Exception:
                    pass

                for n in names:
                    if not isinstance(n, str):
                        continue
                    if 'CreateUtxo' in n or 'CreateUtxos' in n or 'CREATE_UTXOS' in n:
                        self._pending_transfer_type = 'internal'
                        break
                    if 'SendBtc' in n or 'SEND_BTC' in n:
                        self._pending_transfer_type = 'btc_transfer'
                        break
                    if 'Inflation' in n or 'INFLATION' in n or 'Issue' in n or 'ISSUE' in n:
                        self._pending_transfer_type = 'inflation'
                        break
                    if 'Send' in n and 'Btc' not in n and 'SEND_' in n:
                        self._pending_transfer_type = 'asset_transfer'
                        break
            except Exception:
                pass

            # If PSBT details are already on screen, update transfer type label immediately
            try:
                if self._psbt_details is not None and hasattr(self, 'val_transfer_type'):
                    key = self._pending_transfer_type
                    remap = key if key in ('internal', 'btc_transfer', 'inflation', 'asset_transfer') else None
                    if remap is not None:
                        t_text = QCoreApplication.translate(
                            IRIS_WALLET_TRANSLATIONS_CONTEXT, remap,
                        )
                        fallback = {
                            'internal': 'Internal',
                            'btc_transfer': 'BTC transfer',
                            'inflation': 'Inflation',
                            'asset_transfer': 'Asset transfer',
                        }.get(remap, remap)
                        self.val_transfer_type.setText(fallback)
                        if hasattr(self, 'tile_ttype'):
                            self.tile_ttype.show()
                        self.lbl_transfer_type.setVisible(True)
                        self.val_transfer_type.setVisible(True)
            except Exception:
                pass
            # Avoid stacking multiple inspections for the same PSBT
            if not (isinstance(self._last_inspected_psbt, str) and self._last_inspected_psbt == current_psbt and self._psbt_details is not None):
                # Trigger inspection explicitly now that we have the context
                self._trigger_inspection(operation, current_psbt)
            # Re-evaluate button enablement now that pending_operation is available
            self.handle_button_enable()

    def _handle_rgb_transfer_inspection_result(self, rgb_details):
        """
        Handle the async RGB transfer inspection result from the signal.
        Populates Asset ID and Amount from RgbInspection.
        """
        if not rgb_details:
            return

        self._rgb_details = rgb_details
        # Always hide Destination in RGB contexts (send/inflation) to avoid row conflicts
        try:
            if hasattr(self, 'tile_destination'):
                self.tile_destination.hide()
            if hasattr(self, 'lbl_destination'):
                self.lbl_destination.setVisible(False)
            if hasattr(self, 'val_destination'):
                self.val_destination.setVisible(False)
        except Exception:
            pass
        operations = rgb_details.operations
        if not operations:
            # Still trigger a render attempt; card stays hidden until both ready
            self._render_inspection_if_ready()
            return

        # Take the first operation (usually one per transfer)
        op_info = operations[0]
        asset_id = op_info.asset_id

        # Calculate amounts from fungible assignments
        send_amount = 0
        total_inflation_amount = 0
        for transition in op_info.transitions:
            for output in transition.outputs:
                assignment = output.assignment
                if assignment and assignment.is_FUNGIBLE():
                    amt = assignment.amount
                    total_inflation_amount += amt
                    if not output.is_ours:
                        send_amount += amt

        # Update Asset ID label
        if asset_id:
            self.lbl_asset_id.setVisible(True)
            self.val_asset_id.setVisible(True)
            self.val_asset_id.setText(self._wrap_to_two_lines(str(asset_id)))
            self.val_asset_id.setToolTip(str(asset_id))
            if hasattr(self, 'tile_asset'):
                self.tile_asset.show()
            # In RGB context, ensure Destination stays hidden so Asset ID occupies full row
            if hasattr(self, 'tile_destination'):
                self.tile_destination.hide()
            # Also hide inner widgets to avoid flicker
            if hasattr(self, 'lbl_destination'):
                self.lbl_destination.setVisible(False)
            if hasattr(self, 'val_destination'):
                self.val_destination.setVisible(False)
        else:
            if hasattr(self, 'tile_asset'):
                self.tile_asset.hide()


        # Update Amount label (single label for both send and inflation)
        amount_value = 0
        if send_amount > 0:
            amount_value = send_amount
        elif total_inflation_amount > 0:
            amount_value = total_inflation_amount

        if amount_value > 0:
            self.lbl_amount.setVisible(True)
            self.lbl_amount.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_field_label',
                ),
            )
            self.val_amount.setVisible(True)
            self.val_amount.setText(f"{amount_value:,}")
            self.val_amount.setStyleSheet('color: #10B981; font-weight: 700;')
            if hasattr(self, 'tile_amount'):
                self.tile_amount.show()

        # Update Transfer Type value (prefer pending operation mapping if available)
        transfer_value_key = getattr(self, '_pending_transfer_type', None)
        if transfer_value_key is None:
            if send_amount > 0:
                transfer_value_key = 'asset_transfer'
            elif total_inflation_amount > 0:
                transfer_value_key = 'inflation'

        if transfer_value_key is not None:
            self.lbl_transfer_type.setVisible(True)
            self.val_transfer_type.setVisible(True)
            t_text = QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, transfer_value_key,
            )
            # Fallbacks for unmapped translations
            fallback_map = {
                'asset_transfer': 'Asset transfer',
                'inflation': 'Inflation',
                'btc_transfer': 'BTC transfer',
                'internal': 'Internal',
            }
            self.val_transfer_type.setText(fallback_map.get(transfer_value_key, transfer_value_key))
            if hasattr(self, 'tile_ttype'):
                self.tile_ttype.show()
        else:
            if hasattr(self, 'tile_ttype'):
                self.tile_ttype.hide()

        # Min confirmations: dedicated row from pending operation details if available
        op_details = self._current_operation.details if self._current_operation is not None else None
        if op_details is not None:
            min_confirmations = op_details.min_confirmations
            if min_confirmations is not None and hasattr(self, 'lbl_min_conf'):
                self.lbl_min_conf.setVisible(True)
                self.val_min_conf.setVisible(True)
                self.val_min_conf.setText(str(min_confirmations))
                if hasattr(self, 'tile_minconf'):
                    self.tile_minconf.show()
            else:
                if hasattr(self, 'tile_minconf'):
                    self.tile_minconf.hide()

        # After RGB processing, try to render if PSBT is also ready
        self._render_inspection_if_ready()


    def _on_signature_count_ready(self, count: int):
        _, total = SettingRepository.get_multisig_config()
        total_disp = total if total is not None else '?'
        self.sign_status_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'signature_count',
            ).format(count, total_disp),
        )
        # Multisig: always keep the primary action as 'Sign PSBT' (never flip to Broadcast)
        if self.is_multisig:
            self.broadcast_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'sign_psbt',
                ),
            )
            if self.is_initiator_of_pending:
                self.broadcast_button.hide()
                self.btn_reject.hide()
            else:
                self.broadcast_button.show()
                self.btn_reject.show()

    def _on_import_psbt(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import PSBT', '', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()
            text = base64.b64encode(raw).decode('ascii').strip()
            self.broadcast_transaction_input.setPlainText(text)
            # Refresh UI state
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
        current_psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not current_psbt:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export PSBT', 'transaction.psbt', 'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return
        try:
            psbt_bytes = base64.b64decode(current_psbt, validate=True)
            with open(file_path, 'wb') as f:
                f.write(psbt_bytes)
        except Exception as e:
            ToastManager.show_toast(
                parent=self,
                preset=ToastPreset.ERROR,
                description=f'Failed to write PSBT file: {e}',
            )

    def _on_clear_psbt(self):
        """Clear the current PSBT and reset UI state."""
        self.broadcast_transaction_input.clear()
        self.broadcast_transaction_input.setReadOnly(False)
        self.inspection_frame.hide()
        if hasattr(self, 'details_title'):
            self.details_title.hide()
        if self.is_multisig:
            self.sign_status_label.hide()
            self._apply_base_sizes()

        # Reset labels
        _, total = SettingRepository.get_multisig_config()
        total_disp = total if total is not None else '?'
        self.sign_status_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'signature_count',
            ).format(0, total_disp),
        )

        # Update buttons
        self.btn_import.setEnabled(True)
        self.btn_import.show()
        self.btn_clear.setEnabled(False)
        self.btn_clear.hide()
        self.btn_export.setEnabled(False)
        self.broadcast_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'sign_psbt',
            ),
        )
        # Re-show sign button if hidden
        self.broadcast_button.show()

    def _on_combine_psbts(self):
        # Get the base PSBT from the text area
        base_psbt = self.broadcast_transaction_input.toPlainText().strip()
        if not base_psbt:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select PSBT to Combine',
            '',
            'PSBT Files (*.psbt *.txt);;All Files (*)',
        )
        if not file_path:
            return

        try:
            # Read file in binary mode
            with open(file_path, 'rb') as f:
                raw = f.read()
                _ = base64.b64encode(raw).decode('ascii').strip()

        except Exception as e:
            ToastManager.show_toast(
                parent=self,
                preset=ToastPreset.ERROR,
                description=f'Failed to read PSBT file: {e}',
            )

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

    def update_reject_button_state(self, is_reject_loading: bool):
        """
        Updates the loading state of the reject button.
        """
        if is_reject_loading:
            self.btn_reject.start_loading()
            self.btn_reject.setEnabled(False)
        else:
            self.btn_reject.stop_loading()
            # Re-evaluate enabled state to mirror Sign PSBT conditions
            self.handle_button_enable()

    def _load_psbts_for_signing(self) -> None:
        """Populate the PSBT input from stored unsigned drafts or passed operation."""
        # For multisig, use the pending operation passed from navigation
        if self.is_multisig:
            if self.pending_operation:
                # Extract PSBT from the pending operation
                op = self.pending_operation
                # OperationInfo has operation field which contains the PSBT
                operation = op.operation
                initiator_xpub = op.initiator_xpub
                local_xpub = local_store.get_value(MASTER_XPUB)
                if initiator_xpub and local_xpub and initiator_xpub == local_xpub:
                    self.is_initiator_of_pending = True

                if operation is not None:
                    psbt = operation.psbt

                    if psbt:
                        self.method_selector_label.hide()
                        self.method_selector.hide()
                        self._programmatic_psbt_set = True
                        self.broadcast_transaction_input.setPlainText(psbt)
                        self.broadcast_transaction_input.setReadOnly(True)
                        # Store operation info for later use (sign + post)
                        # We store the inner Operation object for consistency
                        self._current_operation = operation

                        # Trigger inspection immediately (Load Flow)
                        self._trigger_inspection(operation, psbt)

                        # Show Reject for non-initiators reviewing
                        if not self.is_initiator_of_pending:
                            self.btn_reject.show()
                        self.handle_button_enable()
                        return

            # No pending operations passed
            self.method_selector_label.hide()
            self.method_selector.hide()
            self.broadcast_transaction_input.clear()
            self.broadcast_button.setEnabled(False)
            return

        # Standard offline wallet flow - load from local DB
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
            self.method_selector_label.hide()
            self.method_selector.hide()
            self.broadcast_transaction_input.clear()
            self.broadcast_button.setEnabled(False)
            return

        # 1 PSBT: hide selector, set text, enable button
        if count == 1:
            self.method_selector_label.hide()
            self.method_selector.hide()
            self._programmatic_psbt_set = True
            self.broadcast_transaction_input.setPlainText(
                self._psbt_items[0].get('psbt', ''),
            )
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()
            return

        # >1 PSBTs: show and populate selector
        self.horizontal_layout_2.setContentsMargins(10, 15, 0, 15)
        self.method_selector_label.show()
        self.method_selector.show()
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
            self._programmatic_psbt_set = True
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
                # Determine purpose from signed PSBT storage to select the page name
            page_name = 'NIA page'
            svc = WalletDataService.get_session()
            if svc is not None:
                signed = svc.list_psbt(True) or []
                match = next(
                    (p for p in signed if p.get('psbt') == psbt), None,
                )
                purpose = match.get('purpose') if isinstance(
                    match, dict,
                ) else None
                if purpose == 'inflate_asset':
                    page_name = 'IFA secondary issuance'
            self.view_model.page_navigation.receive_asset_page(
                ReceiveAssetModel(
                    page_name=page_name,
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
            self.method_selector_label.hide()
            self.method_selector.hide()
            self.handle_button_enable()
            return

        # 1 PSBT: hide selector, set text, enable button
        if count == 1:
            self.method_selector_label.hide()
            self.method_selector.hide()
            self._programmatic_psbt_set = True
            self.broadcast_transaction_input.setPlainText(
                self._psbt_signed_items[0].get('psbt', ''),
            )
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()
            return

        # >1 PSBTs: show and populate selector
        self.horizontal_layout_2.setContentsMargins(10, 15, 0, 15)
        self.method_selector_label.show()
        self.method_selector.show()
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
            self._programmatic_psbt_set = True
            self.broadcast_transaction_input.setPlainText(psbt_text)
            self.broadcast_transaction_input.setReadOnly(True)
            self.handle_button_enable()

        self.method_selector.currentIndexChanged.connect(on_index_changed)
        on_index_changed(0)

