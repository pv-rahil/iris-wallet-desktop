"""
Widget for displaying PSBT and RGB inspection details and actions in the broadcast flow.
"""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import set_widgets_visible
from src.views.components.buttons import PrimaryButton


class BroadcastInspectionDetails(QFrame):
    """
    Component for transaction inspection details (BTC and RGB) and action buttons.
    """

    def __init__(self, parent=None):

        super().__init__(parent)
        self._is_multisig = False
        self._is_watch_only = False
        self._can_broadcast = False
        self._rgb_expected = False
        self._is_inflation_context = False
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName('inspection_frame')
        self.setFrameShape(QFrame.NoFrame)
        self.setFrameShadow(QFrame.Plain)
        self.setContentsMargins(5, 0, 0, 0)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum,
        )

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)

        # Lightweight loading label shown while PSBT inspection runs
        self.inspect_loading = QLabel(self)
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
        self.outer_layout.addWidget(self.inspect_loading)

        # Section title
        self.details_title = QLabel(self)
        self.details_title.setObjectName('details_title')
        self.details_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_details_title',
            ),
        )
        self.details_title.setStyleSheet('padding: 10px 0px;')
        self.outer_layout.addWidget(self.details_title)

        self.details_card = QFrame(self)
        self.details_card.setObjectName('inspection_card')
        self.details_card.setStyleSheet(
            'QFrame#inspection_card { border: none; border-radius: 12px; background-color: rgba(255,255,255,0.06); }',
        )
        self.details_card.setFrameShape(QFrame.NoFrame)
        self.details_card.setFrameShadow(QFrame.Plain)

        self.grid = QGridLayout(self.details_card)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setHorizontalSpacing(5)
        self.grid.setVerticalSpacing(5)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnMinimumWidth(0, 200)
        self.grid.setColumnMinimumWidth(1, 200)

        self.outer_layout.addWidget(self.details_card)

        # Init tiles
        self.tile_txid, self.lbl_txid, self.val_txid = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id_label',
            ), 'val_txid',
        )
        self.tile_asset, self.lbl_asset_id, self.val_asset_id = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_id_label',
            ), 'val_asset_id',
        )
        self.tile_amount, self.lbl_amount, self.val_amount = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_field_label',
            ), 'val_amount',
        )
        self.tile_ttype, self.lbl_transfer_type, self.val_transfer_type = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transfer_type_label',
            ), 'val_transfer_type',
        )
        self.tile_minconf, self.lbl_min_conf, self.val_min_conf = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'min_confirmations',
            ), 'val_min_conf',
        )
        self.tile_destination, self.lbl_destination, self.val_destination = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'destination_label',
            ), 'val_destination',
        )
        self.tile_fee, self.lbl_fee, self.val_fee = self._create_detail_row(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'fee_sats_label',
            ), 'val_fee',
        )

        # Initial layout positioning
        self.grid.addWidget(self.tile_txid, 0, 0, 1, 1)
        self.grid.addWidget(self.tile_asset, 0, 1, 1, 1)
        self.grid.addWidget(self.tile_amount, 1, 0)
        self.grid.addWidget(self.tile_fee, 1, 1)
        self.grid.addWidget(self.tile_destination, 0, 1, 1, 1)
        self.grid.addWidget(self.tile_ttype, 3, 0)
        self.grid.addWidget(self.tile_minconf, 3, 1)

        # Default hide details section
        self.details_title.hide()
        self.details_card.hide()

        set_widgets_visible(
            [
                self.tile_asset, self.tile_amount, self.tile_ttype,
                self.tile_minconf, self.tile_destination, self.tile_fee,
            ], False,
        )
        # --- Action Buttons Setup ---
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0, 14, 0, 8)
        self.actions_layout.setSpacing(16)

        # Standard primary button for single-sig or broadcast
        self.btn_primary = PrimaryButton()
        self.btn_primary.setMinimumHeight(40)

        # Multisig-specific buttons
        self.btn_import = PrimaryButton()
        self.btn_import.setFixedWidth(160)
        self.btn_import.setMinimumHeight(40)
        self.btn_import.hide()

        self.btn_export = PrimaryButton()
        self.btn_export.setFixedWidth(160)
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setEnabled(False)
        self.btn_export.hide()

        self.btn_clear = PrimaryButton()
        self.btn_clear.setFixedWidth(160)
        self.btn_clear.setMinimumHeight(40)
        self.btn_clear.setEnabled(False)
        self.btn_clear.hide()

        self.btn_reject = PrimaryButton()
        self.btn_reject.setFixedWidth(160)
        self.btn_reject.setMinimumHeight(40)
        self.btn_reject.hide()

        self.outer_layout.addLayout(self.actions_layout)

    def show_inspection_details(self, visible: bool):
        """Show or hide the transaction details section specifically."""
        self.details_title.setVisible(visible)
        self.details_card.setVisible(visible)

    def _create_detail_row(self, label_text, value_id):
        tile = QFrame(self.details_card)
        tile.setObjectName('tile_frame')
        tile.setStyleSheet(
            'QFrame#tile_frame { border: none; border-radius: 0px; background-color: transparent; }',
        )
        tile.setFixedHeight(80)
        tile.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        tile_layout = QVBoxLayout(tile)
        tile_layout.setContentsMargins(10, 10, 10, 10)
        tile_layout.setSpacing(0)
        lbl = QLabel(label_text, tile)
        lbl.setStyleSheet(
            'color: rgba(255,255,255,0.72); font-size: 14px;font-weight: 600;',
        )
        val = QLabel(tile)
        val.setObjectName(value_id)
        val.setWordWrap(True)
        val.setStyleSheet('font-size: 14px; color: #FFFFFF; font-family: "JetBrains Mono", monospace;')
        lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter,
        )
        val.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter,
        )
        lbl.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Preferred,
        )
        val.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        val.setMinimumWidth(0)
        tile_layout.addWidget(lbl)
        tile_layout.addWidget(val)
        return tile, lbl, val

    def set_config(self, is_multisig: bool, is_watch_only: bool, can_broadcast: bool):
        """Configure both multisig state and broadcast capabilities."""
        self._is_multisig = is_multisig
        self._is_watch_only = is_watch_only
        self._can_broadcast = can_broadcast

        # Clear actions layout first
        for i in reversed(range(self.actions_layout.count())):
            item = self.actions_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
            else:
                self.actions_layout.removeItem(item)

        if not is_multisig:
            self.actions_layout.addWidget(self.btn_primary)
            self.btn_primary.setMaximumSize(QSize(270, 16777215))
        else:
            self.actions_layout.addStretch(1)
            self.btn_primary.setFixedWidth(160)
            self.actions_layout.addWidget(self.btn_import)
            self.actions_layout.addWidget(self.btn_export)
            self.actions_layout.addWidget(self.btn_clear)
            self.actions_layout.addWidget(self.btn_reject)
            self.actions_layout.addWidget(self.btn_primary)
            self.actions_layout.addStretch(1)

            self.btn_import.show()
            self.btn_reject.show()

        self.retranslate_ui()

    def set_multisig(self, is_multisig: bool):
        """Legacy setter for multisig mode."""
        self._is_multisig = is_multisig

    @staticmethod
    def _wrap_to_two_lines(text: str, first_line_chars: int = 34) -> str:
        if not isinstance(text, str):
            return str(text)
        if len(text) <= first_line_chars:
            return text
        return text[:first_line_chars] + '\n' + text[first_line_chars:]

    def update_psbt_details(self, details, is_inflation_context: bool, rgb_expected: bool, pending_key: str | None):
        """Update BTC-level details from PsbtInspection."""
        self._rgb_expected = rgb_expected
        self._is_inflation_context = is_inflation_context

        self.val_txid.setText(self._wrap_to_two_lines(details.txid))

        # BTC-only vs RGB layout shifts
        is_btc_only = (not rgb_expected) and (not is_inflation_context)
        if is_btc_only:
            # TXID spans full width in first row
            self.grid.addWidget(self.tile_txid, 0, 0, 1, 2)
            self.val_txid.setText(details.txid)
            # Type (left) and Fee (right) on second row
            self.grid.addWidget(self.tile_ttype, 1, 0, 1, 1)
            self.grid.addWidget(self.tile_fee, 1, 1, 1, 1)
            set_widgets_visible(
                [
                    self.tile_destination, self.lbl_destination,
                    self.val_destination,
                ], False,
            )
        else:
            # Restore to original positions for RGB layout
            self.grid.addWidget(self.tile_txid, 0, 0, 1, 1)
            self.grid.addWidget(self.tile_fee, 1, 1)
            self.grid.addWidget(self.tile_ttype, 3, 0)
            set_widgets_visible(
                [
                    self.lbl_destination, self.val_destination,
                    self.tile_destination,
                ], False,
            )

        # Fee
        fee_sat = details.fee_sat
        if isinstance(fee_sat, int) and fee_sat >= 0:
            self.lbl_fee.setVisible(True)
            self.val_fee.setVisible(True)
            self.val_fee.setText(f"{fee_sat:,} sats")
            self.val_fee.setStyleSheet('font-weight: 700;')
            self.tile_fee.show()
        else:
            self.tile_fee.hide()

        if pending_key:
            from src.data.service.broadcast_transaction_service import BroadcastTransactionService
            label = BroadcastTransactionService.get_transfer_type_label(
                pending_key,
            )
            self.val_transfer_type.setText(label)
            self.lbl_transfer_type.setVisible(True)
            self.val_transfer_type.setVisible(True)
            self.tile_ttype.show()

    def update_rgb_details(self, asset_id, amount, transfer_type_label, min_conf=None):
        """Update RGB-level details."""
        if asset_id:
            self.lbl_asset_id.setVisible(True)
            self.val_asset_id.setVisible(True)
            self.val_asset_id.setText(self._wrap_to_two_lines(str(asset_id)))
            self.val_asset_id.setToolTip(str(asset_id))
            self.tile_asset.show()
        else:
            self.tile_asset.hide()

        if amount > 0:
            self.lbl_amount.setVisible(True)
            self.val_amount.setVisible(True)
            self.val_amount.setText(str(amount))
            self.val_amount.setStyleSheet('color: #10B981; font-weight: 700;')
            self.tile_amount.show()
        elif not (self._rgb_expected or self._is_inflation_context):
            set_widgets_visible(
                [self.tile_amount, self.lbl_amount, self.val_amount], False,
            )

        if transfer_type_label:
            self.val_transfer_type.setText(transfer_type_label)
            self.lbl_transfer_type.setVisible(True)
            self.val_transfer_type.setVisible(True)
            self.tile_ttype.show()

        if min_conf is not None:
            self.lbl_min_conf.setVisible(True)
            self.val_min_conf.setVisible(True)
            self.val_min_conf.setText(str(min_conf))
            self.tile_minconf.show()
        else:
            self.tile_minconf.hide()

    def update_transfer_type_label(self, label: str):
        """Update the transfer type label directly."""
        if label:
            self.val_transfer_type.setText(label)
            self.lbl_transfer_type.setVisible(True)
            self.val_transfer_type.setVisible(True)
            self.tile_ttype.show()
        else:
            self.tile_ttype.hide()

    def retranslate_ui(self):
        """Retranslate both inspection labels and action buttons."""
        if self._can_broadcast:
            self.btn_primary.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'broadcast_transaction',
                ),
            )
        else:
            self.btn_primary.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'sign_psbt',
                ),
            )

        if self._is_multisig:
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
            if self._is_watch_only:
                self.btn_primary.setText(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'post_to_multisig',
                    ),
                )

        # Retranslate inspection static labels
        self.inspect_loading.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'loading',
            ),
        )
        self.details_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_details_title',
            ),
        )
        self.lbl_txid.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transaction_id_label',
            ),
        )
        self.lbl_asset_id.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_id_label',
            ),
        )
        self.lbl_amount.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'amount_field_label',
            ),
        )
        self.lbl_transfer_type.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'transfer_type_label',
            ),
        )
        self.lbl_min_conf.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'min_confirmations',
            ),
        )
        self.lbl_destination.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'destination_label',
            ),
        )
        self.lbl_fee.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'fee_sats_label',
            ),
        )

    def set_primary_loading(self, loading: bool):
        if loading:
            self.btn_primary.start_loading()
        else:
            self.btn_primary.stop_loading()

    def set_reject_loading(self, loading: bool):
        if loading:
            self.btn_reject.start_loading()
        else:
            self.btn_reject.stop_loading()

    def set_primary_enabled(self, enabled: bool):
        self.btn_primary.setEnabled(enabled)

    def set_reject_enabled(self, enabled: bool):
        self.btn_reject.setEnabled(enabled)
