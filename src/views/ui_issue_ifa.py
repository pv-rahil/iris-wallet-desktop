# pylint: disable=too-many-instance-attributes, unused-import
"""This module contains the IssueIFAWidget class,
 which represents the UI for issuing IFA assets.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QWidget

import src.resources_rc
from accessible_constant import ISSUE_IFA_ASSET_CLOSE_BUTTON
from accessible_constant import ISSUE_IFA_BUTTON
from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import IssueAssetDraftModel
from src.model.common_operation_model import PsbtData
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import PsbtStatus
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.rgb_model import RgbAssetPageLoadModel
from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultMinConfirmation
from src.model.success_model import SuccessPageModel
from src.utils.common_utils import enforce_u64_max_input
from src.utils.common_utils import set_placeholder_value
from src.utils.constant import FEE_RATE
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.decorators.check_colorable_available import get_unspent_utxo_count
from src.utils.helpers import load_stylesheet
from src.utils.helpers import register_multisig_button
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.ifa_hw_helpers import delete_active_secondary_draft_on_success
from src.views.components.ifa_hw_helpers import handle_success_dialog
from src.views.components.ifa_hw_helpers import handle_utxo_error
from src.views.components.issue_asset_helpers import compute_needed_utxos_for_ifa
from src.views.components.issue_asset_helpers import show_utxo_confirmation_dialog
from src.views.components.issue_ifa_form import IssueIFAForm
from src.views.components.toast import ToastManager
from src.views.components.ui_helpers import get_wallet_type_flags
from src.views.components.wallet_logo_frame import WalletLogoFrame


class IssueIFAWidget(QWidget):
    """This class represents the UI for issuing IFA assets."""

    def __init__(self, view_model, draft_id=None, from_draft=False, params: RgbAssetPageLoadModel | None = None):
        super().__init__()
        self.render_timer = RenderTimer(task_name='IssueIFAAsset Rendering')
        self._view_model: MainViewModel = view_model
        self.setStyleSheet(load_stylesheet('views/qss/issue_nia_style.qss'))
        self.setObjectName('issue_ifa_page')

        self.params: RgbAssetPageLoadModel | None = params
        self.secondary_issuance: bool = bool(
            self.params and self.params.is_secondary_issuance,
        )
        flags = get_wallet_type_flags()
        self.is_hardware_wallet = flags.is_hardware_wallet
        self.is_offline_wallet = flags.is_offline_wallet
        self.is_watch_only = flags.is_watch_only
        self.is_multisig = flags.is_multisig
        self.asset_transactions: ListTransferAssetWithBalanceResponseModel | None = None
        self.value_of_default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        self._utxo_dialog_active = False
        self._retry_after_utxo_inflate = False
        self.issue_ifa_grid_layout = QGridLayout(self)
        self.issue_ifa_grid_layout.setObjectName('issue_nia_grid_layout')
        self.issue_ifa_wallet_logo = WalletLogoFrame(self)
        self.issue_ifa_grid_layout.addWidget(
            self.issue_ifa_wallet_logo, 0, 0, 1, 2,
        )
        self.draft_id = draft_id
        self.from_draft = from_draft

        # Add spacers
        self.issue_ifa_grid_layout.addItem(
            QSpacerItem(
                265, 20, QSizePolicy.Expanding,
                QSizePolicy.Minimum,
            ), 1, 3, 1, 1,
        )
        self.issue_ifa_grid_layout.addItem(
            QSpacerItem(
                20, 190, QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            ), 3, 1, 1, 1,
        )
        self.issue_ifa_grid_layout.addItem(
            QSpacerItem(
                266, 20, QSizePolicy.Expanding,
                QSizePolicy.Minimum,
            ), 2, 0, 1, 1,
        )
        self.issue_ifa_grid_layout.addItem(
            QSpacerItem(
                20, 190, QSizePolicy.Minimum,
                QSizePolicy.Expanding,
            ), 0, 2, 1, 1,
        )

        # Create form widget using component
        self.ifa_form = IssueIFAForm(
            parent=self, default_fee_rate=self.value_of_default_fee_rate.fee_rate,
        )
        self.issue_ifa_grid_layout.addWidget(self.ifa_form, 1, 1, 2, 2)

        # Title bar
        self._build_title_bar()

        # Issue button
        self.issue_ifa_btn = PrimaryButton()
        self.issue_ifa_btn.setAccessibleName(ISSUE_IFA_BUTTON)
        self.issue_ifa_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.issue_ifa_btn.setMinimumSize(QSize(402, 40))
        self.issue_ifa_btn.setMaximumSize(QSize(402, 40))
        self.ifa_form.inner_layout.addWidget(
            self.issue_ifa_btn, 0, Qt.AlignCenter,
        )

        self.setup_ui_connection()
        self.retranslate_ui()

        # Apply prefill rules for secondary issuance
        if self.params is not None and self.secondary_issuance:
            self.ifa_form.configure_secondary_issuance(
                asset_name=self.params.asset_name or '',
                asset_id=self.params.asset_id or '',
            )

        if self.from_draft and self.draft_id:
            self._load_inflatables_draft_data()
        else:
            if not self.secondary_issuance:
                self.ifa_form.configure_primary_issuance()

    def _build_title_bar(self):
        """Build the title bar with close button."""
        self.title_layout = QHBoxLayout()
        self.title_layout.setObjectName('horizontal_layout_1')
        self.title_layout.setContentsMargins(35, 9, 40, 0)

        self.issue_ifa_title = QLabel(self.ifa_form)
        self.issue_ifa_title.setObjectName('set_wallet_password_label')
        self.issue_ifa_title.setMinimumSize(QSize(415, 63))
        self.title_layout.addWidget(self.issue_ifa_title)

        self.ifa_close_btn = QPushButton(self.ifa_form)
        self.ifa_close_btn.setAccessibleName(ISSUE_IFA_ASSET_CLOSE_BUTTON)
        self.ifa_close_btn.setObjectName('close_btn')
        self.ifa_close_btn.setMinimumSize(QSize(24, 24))
        self.ifa_close_btn.setMaximumSize(QSize(50, 65))
        self.ifa_close_btn.setAutoFillBackground(False)
        self.ifa_close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_icon = QIcon()
        close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(), QIcon.Normal, QIcon.Off,
        )
        self.ifa_close_btn.setIcon(close_icon)
        self.ifa_close_btn.setIconSize(QSize(24, 24))
        self.ifa_close_btn.setCheckable(False)
        self.ifa_close_btn.setChecked(False)
        self.title_layout.addWidget(self.ifa_close_btn, 0, Qt.AlignHCenter)

        self.ifa_form.inner_layout.insertLayout(0, self.title_layout)

        # Header line
        self.header_line = QFrame(self.ifa_form)
        self.header_line.setObjectName('line_3')
        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)
        self.ifa_form.inner_layout.insertWidget(1, self.header_line)

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.ifa_form.name_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.ifa_form.ticker_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.ifa_form.issue_amount_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.ifa_close_btn.clicked.connect(
            self._view_model.page_navigation.inflatable_asset_page,
        )
        self._view_model.issue_ifa_asset_view_model.is_loading.connect(
            self.update_loading_state,
        )
        if self.secondary_issuance:
            if not self.is_multisig:
                self.issue_ifa_btn.clicked.connect(
                    self.on_secondary_issuance_click,
                )
            else:
                register_multisig_button(
                    self._view_model,
                    self.issue_ifa_btn,
                    self.on_secondary_issuance_click,
                )
            self.ifa_form.issue_amount_input.textChanged.connect(
                self.validate_issuance_amount,
            )
            view_model = self._view_model.cfa_view_model
            self.asset_transactions: ListTransferAssetWithBalanceResponseModel = view_model.txn_list
            self.spendable_balance_validation()
            # Re-validate when asset data is loaded/refreshed
            view_model.txn_list_loaded.connect(
                self.spendable_balance_validation,
            )
        else:
            if not self.is_multisig:
                self.issue_ifa_btn.clicked.connect(
                    self.on_issue_ifa_click,
                )
            else:
                register_multisig_button(
                    self._view_model,
                    self.issue_ifa_btn,
                    self.on_issue_ifa_click,
                )

        self._view_model.issue_ifa_asset_view_model.success_page_message.connect(
            self.inflatables_asset_issued,
        )
        # Also handle HW dialog updates from inflate_begin/signing path
        self._view_model.issue_ifa_asset_view_model.hw_dialog_update.connect(
            self.handle_ifa_hw_dialog,
        )
        # Show inflate PSBT (unsigned) for offline/watch-only when emitted by the viewmodel
        self._view_model.issue_ifa_asset_view_model.unsigned_psbt.connect(
            self.show_inflate_psbt_page,
        )
        self.ifa_form.issue_amount_input.textChanged.connect(
            lambda: set_placeholder_value(self.ifa_form.issue_amount_input),
        )
        self.ifa_form.issue_amount_input.textChanged.connect(
            lambda text: enforce_u64_max_input(
                self.ifa_form.issue_amount_input, text,
            ),
        )
        # Validate supply relationships only in primary issuance
        if not self.secondary_issuance:
            self.ifa_form.total_supply_input.textChanged.connect(
                self.validate_supply_fields,
            )
            self.ifa_form.issue_amount_input.textChanged.connect(
                self.validate_supply_fields,
            )
        self._view_model.utxo_creation_view_model.hw_dialog_update.connect(
            self.handle_ifa_hw_dialog,
        )
        self._view_model.utxo_creation_view_model.utxo_created.connect(
            self.handle_ifa_utxo_created,
        )
        self._view_model.utxo_creation_view_model.psbt_posted_to_bridge.connect(
            self.handle_psbt_posted_to_bridge,
        )
        # Show UTXO-creation PSBT for hardware-online, watch-only, and offline wallets
        self._view_model.utxo_creation_view_model.unsigned_psbt.connect(
            self.show_ifa_psbt_page,
        )
        self._view_model.issue_ifa_asset_view_model.utxo_creation_started.connect(
            self.handle_ifa_issue,
        )
        self._view_model.issue_ifa_asset_view_model.secondary_issuance_success.connect(
            self._view_model.page_navigation.inflatable_asset_page,
        )
        # Also ensure any open HW dialog is closed after secondary issuance completes
        self._view_model.issue_ifa_asset_view_model.secondary_issuance_success.connect(
            self._close_hw_dialog_if_open,
        )
        # Delete the active secondary issuance draft after successful broadcast
        self._view_model.issue_ifa_asset_view_model.secondary_issuance_success.connect(
            self._delete_active_secondary_draft_on_success,
        )

    def retranslate_ui(self):
        """Retranslate the UI elements."""
        self.issue_ifa_btn.setDisabled(True)
        self.issue_ifa_title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'issue_new_ifa_asset',
                None,
            ),
        )
        if self.secondary_issuance:
            self.ifa_form.ticker_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'asset_id',
                    None,
                ),
            )
            self.issue_ifa_title.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'secondary_issuance',
                    None,
                ),
            )
            self.ifa_form.fee_rate_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'ifa_fee_rate',
                    None,
                ),
            )
            self.ifa_form.issue_supply_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'issue_new_supply',
                    None,
                ),
            )

        else:
            self.ifa_form.ticker_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'asset_ticker',
                    None,
                ),
            )
            self.ifa_form.issue_supply_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'issue_supply',
                    None,
                ),
            )
        self.ifa_form.ticker_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'short_identifier',
                None,
            ),
        )
        self.ifa_form.name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'asset_name',
                None,
            ),
        )
        self.ifa_form.name_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'name_of_the_asset',
                None,
            ),
        )
        self.ifa_form.issue_amount_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'amount_to_issue',
                None,
            ),
        )
        self.ifa_form.total_supply_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        self.ifa_form.total_supply_info_btn.setToolTip(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'ifa_total_supply_help',
                None,
            ),
        )
        self.ifa_form.total_supply_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        # Fee label text via translation (sat/vB)
        self.ifa_form.fee_rate_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'fee_rate_sat_vb',
                None,
            ),
        )
        self.ifa_form.fee_rate_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'fee_rate',
                None,
            ),
        )
        self.issue_ifa_btn.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_asset', None,
            ),
        )

    def update_loading_state(self, is_loading: bool):
        """
            Updates the loading state of the issue_ifa_btn.
            This method prints the loading state and starts or stops the loading animation
            of the proceed_wallet_password object based on the value of is_loading.
        """
        if is_loading:
            self.render_timer.start()
            self.issue_ifa_btn.start_loading()
            self.ifa_close_btn.setDisabled(True)
        else:
            self.render_timer.stop()
            self.issue_ifa_btn.stop_loading()
            self.ifa_close_btn.setDisabled(False)

    def on_issue_ifa_click(self):
        """Handle the click event for issuing a new IFA asset."""
        # Retrieve text values from input fields
        short_identifier = self.ifa_form.get_ticker()
        asset_name = self.ifa_form.get_name()
        amount_to_issue = self.ifa_form.get_issue_amount()
        total_supply = self.ifa_form.get_total_supply()
        # Compute inflation = total - initial, with minimal guards
        try:
            t = int(total_supply)
            a = int(amount_to_issue)
        except ValueError:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_valid_number', None,
                ),
            )
            return
        if t < 0 or a < 0:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'values_must_be_non_negative', None,
                ),
            )
            return
        if a >= t:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'initial_supply_not_exceed_total', None,
                ),
            )
            return
        inflation_amounts = t - a
        if get_unspent_utxo_count() < 3 and not self.from_draft:
            self.create_issue_inflatables_asset_draft(
                short_identifier, asset_name, a,
                inflation_amounts,
            )

        # Call the IFA view model method and pass the text values as arguments
        self._view_model.issue_ifa_asset_view_model.issue_ifa_asset(
            short_identifier,
            asset_name,
            a,
            inflation_amounts,
        )

    def _get_or_create_secondary_draft(self, svc: WalletDataService, amount_to_issue: str) -> bool:
        """Get or create secondary draft, return True if should show existing PSBT."""
        if self.params is None or self.params.asset_id is None:
            return False

        asset_id = self.params.asset_id

        if self.from_draft and self.draft_id is not None:
            svc.set_active_secondary_draft(
                int(self.draft_id), asset_id,
            )
            return False

        amt_text = amount_to_issue or ''
        pref_amt = int(amt_text) if amt_text.strip().isdigit() else None
        active = svc.get_active_secondary_draft_for_asset(asset_id)

        if active is None or active.get('amount') != pref_amt:
            draft_id = svc.add_ifa_secondary_draft_meta(
                asset_id=asset_id,
                asset_name=self.params.asset_name,
                amount=pref_amt,
            )
            if draft_id is not None:
                svc.set_active_secondary_draft(
                    int(draft_id), asset_id,
                )
                self.draft_id = draft_id
                self.from_draft = True
        else:
            active_id = active.get('id')
            if active_id is not None:
                svc.set_active_secondary_draft(
                    int(active_id), asset_id,
                )

        # Check for existing unsigned PSBT
        drafts = svc.list_psbt(False) or []
        for p in drafts:
            if p.get('purpose') == 'inflation' and p.get('psbt'):
                return True
        return False

    def on_secondary_issuance_click(self):
        """Handle the click event for secondary issuance."""
        value_of_default_min_confirmation: DefaultMinConfirmation = SettingCardRepository.get_default_min_confirmation()
        amount_to_issue = self.ifa_form.get_issue_amount()
        fee_text = self.ifa_form.get_fee_rate() or FEE_RATE
        svc = WalletDataService.get_session()
        if svc is not None and self.params is not None:
            has_existing_psbt = self._get_or_create_secondary_draft(
                svc, amount_to_issue,
            )
            if has_existing_psbt:
                existing_unsigned = None
                drafts = svc.list_psbt(False) or []
                for p in drafts:
                    if p.get('purpose') == 'inflation' and p.get('psbt'):
                        existing_unsigned = p.get('psbt')
                        break
                if existing_unsigned:
                    self._view_model.utxo_creation_view_model.current_purpose = 'inflation'
                    self.show_inflate_psbt_page(existing_unsigned)
                    return
        if self.params is None:
            return
        if (self.is_hardware_wallet and not self.is_offline_wallet) or self.is_watch_only or self.is_multisig:
            self._view_model.issue_ifa_asset_view_model.secondary_issuance_begin(
                asset_id=self.params.asset_id,
                amount=int(amount_to_issue),
                fee_rate=int(fee_text),
                min_confirmation=value_of_default_min_confirmation.min_confirmation,
            )
        else:
            self._view_model.issue_ifa_asset_view_model.secondary_issuance(
                asset_id=self.params.asset_id,
                amount=int(amount_to_issue),
                fee_rate=int(fee_text),
                min_confirmation=value_of_default_min_confirmation.min_confirmation,
            )

    def handle_button_enabled(self):
        """Updates the enabled state of the send button."""
        inputs_filled = all([
            self.ifa_form.ticker_input.text(),
            self.ifa_form.issue_amount_input.text(),
            self.ifa_form.name_input.text(),
        ])

        valid_amounts = (
            self.ifa_form.issue_amount_input.text() != '0' and
            self.ifa_form.total_supply_input.text() != '0'
        )

        no_errors = not self.ifa_form.error_label.isVisible()

        if inputs_filled and valid_amounts and no_errors:
            self.issue_ifa_btn.setDisabled(False)
        else:
            self.issue_ifa_btn.setDisabled(True)

    def _show_error(self, msg: str):
        self.ifa_form.show_error(msg)

    def validate_supply_fields(self):
        """Inline validation for total vs initial/new issue supply (primary issuance only)."""
        if self.secondary_issuance:
            # No total supply field in secondary mode
            self.handle_button_enabled()
            return
        total_text = self.ifa_form.get_total_supply()
        issue_text = self.ifa_form.get_issue_amount()
        try:
            total_val = int(total_text) if total_text else 0
            issue_val = int(issue_text) if issue_text else 0
        except ValueError:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'enter_valid_number', None,
                ),
            )
            self.handle_button_enabled()
            return
        if total_val < 0 or issue_val < 0:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'values_must_be_non_negative', None,
                ),
            )
            self.handle_button_enabled()
            return
        if issue_val > total_val:
            self._show_error(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'initial_supply_not_exceed_total', None,
                ),
            )
        else:
            self.ifa_form.hide_error()
        self.handle_button_enabled()

    def _delete_active_secondary_draft_on_success(self):
        delete_active_secondary_draft_on_success(
            self.secondary_issuance, self.params,
        )

    def inflatables_asset_issued(self, asset_name):
        """This method handled after asset issued"""
        # Clean up draft if issuance was started from a draft
        if self.from_draft and self.draft_id:
            inflatables_wallet_service = WalletDataService.get_session()
            if inflatables_wallet_service is not None:
                inflatables_wallet_service.delete_draft_issue_asset(
                    self.draft_id,
                )
        inflatables_header = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'issue_new_ticker',
        )
        inflatables_title = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'you_are_all_set',
        )
        inflatables_description = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'asset_issued',
        ).format(asset_name)
        inflatables_button_text = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, 'home',
        )
        params = SuccessPageModel(
            header=inflatables_header,
            title=inflatables_title,
            description=inflatables_description,
            button_text=inflatables_button_text,
            callback=self._view_model.page_navigation.inflatable_asset_page,
        )
        self.render_timer.stop()
        self._view_model.page_navigation.show_success_page(params)

    def _handle_success_dialog(self, ifa_hw_dialog) -> bool:
        """Handle success dialog case."""
        return handle_success_dialog(ifa_hw_dialog, self.secondary_issuance, self.params)

    def _handle_utxo_error(self, message: str) -> bool:
        """Handle UTXO error case."""
        handled, self._retry_after_utxo_inflate = handle_utxo_error(
            message, self, self._utxo_dialog_active,
            self.secondary_issuance, self._view_model.utxo_creation_view_model,
        )
        return handled

    def handle_ifa_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        if not self.isVisible():
            return
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        # Always close the dialog immediately on SUCCESS
        if dialog_type == PsbtStatus.SUCCESS:
            self._handle_success_dialog(ifa_hw_dialog)
            return
        # Intercept common UTXO errors and route to UTXO creation
        if dialog_type == PsbtStatus.ERROR and message:
            if self._handle_utxo_error(message):
                return
        # Update dialog only when we have a message to show
        if message is not None:
            ifa_hw_dialog.update_dialog(message, dialog_type)
        self.issue_ifa_btn.stop_loading()
        if not ifa_hw_dialog.isVisible():
            ifa_hw_dialog.show()

    def handle_psbt_posted_to_bridge(self):
        """Handle PSBT posted to bridge (multisig initiator)."""
        # Only handle if the current purpose matches IFA issuing
        current_purpose = self._view_model.utxo_creation_view_model.current_purpose
        if current_purpose not in ['issue_asset_ifa', 'inflation', 'inflation_utxo']:
            return
        if not self.isVisible():
            return
        # Close dialog
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        if ifa_hw_dialog.isVisible():
            ifa_hw_dialog.accept()

        # Notify and navigate
        ToastManager.success(INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE)
        self._view_model.page_navigation.inflatable_asset_page()

    def handle_ifa_utxo_created(self, status: bool):
        """Close the hardware wallet dialog after UTXO creation and resume asset issuance if pending."""
        purpose = self._view_model.utxo_creation_view_model.current_purpose
        if purpose not in ('issue_asset_ifa', 'inflation', 'inflation_utxo'):
            return
        if not self.isVisible() or not status:
            return

        if status:
            ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
                parent=self,
            )
            if ifa_hw_dialog.isVisible():
                ifa_hw_dialog.accept()

            # Resume the correct flow depending on purpose
            if purpose == 'issue_asset_ifa':
                self.on_issue_ifa_click()
            elif purpose in ('inflation', 'inflation_utxo'):
                self._retry_after_utxo_inflate = False
                self.on_secondary_issuance_click()

    def _close_hw_dialog_if_open(self):
        """Close the hardware wallet dialog if it is currently visible."""
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        if ifa_hw_dialog.isVisible():
            ifa_hw_dialog.accept()

    def handle_ifa_issue(self):
        """handle ifa issue"""
        if not self.isVisible():
            return
        inflatables_wallet_service = WalletDataService.get_session()
        if inflatables_wallet_service:
            unsigned_psbts = inflatables_wallet_service.list_psbt(
                signed=False,
            )
            # Check for existing PSBT based on purpose
            target_purpose = 'inflation' if self.secondary_issuance else 'issue_asset_ifa'
            # Also check for 'inflation_utxo' if we are in secondary issuance
            purposes_to_check = [target_purpose]
            if self.secondary_issuance:
                purposes_to_check.append('inflation_utxo')

            existing_inflatables_psbt = next(
                (
                    p for p in unsigned_psbts if p.get('purpose') in purposes_to_check
                ), None,
            )
            if existing_inflatables_psbt and existing_inflatables_psbt.get('psbt'):
                self._view_model.utxo_creation_view_model.current_purpose = target_purpose
                self.show_ifa_psbt_page(existing_inflatables_psbt.get('psbt'))
                return
        # For HW-online, proceed directly to PSBT creation
        if self.is_hardware_wallet and not self.is_offline_wallet:
            self._retry_after_utxo_inflate = bool(self.secondary_issuance)
        needed = compute_needed_utxos_for_ifa()
        # Show confirmation dialog for multisig/watch-only wallets
        accepted, _ = show_utxo_confirmation_dialog(
            self, self._utxo_dialog_active,
            lambda active: setattr(self, '_utxo_dialog_active', active),
        )
        if not accepted:
            return
        utxo_purpose = 'inflation_utxo' if self.secondary_issuance else 'issue_asset_ifa'
        self._view_model.utxo_creation_view_model.create_utxos_begin(
            purpose=utxo_purpose, num=needed,
        )

    def show_ifa_psbt_page(self, inflatables_psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        if not self.isVisible():
            return
        # Only respond if PSBT relates to IFA UTXO creation purposes
        if self._view_model.utxo_creation_view_model.current_purpose not in ['issue_asset_ifa', 'inflation', 'inflation_utxo']:
            return
        if inflatables_psbt:
            if self.is_multisig:
                ToastManager.success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_created_successfully', 'PSBT created successfully',
                    ),
                )
                self._view_model.page_navigation.inflatable_asset_page()
            else:
                self._view_model.page_navigation.receive_asset_page(
                    ReceiveAssetModel(
                        page_name='IFA page',
                        address_info='psbt_info', psbt=inflatables_psbt, is_signed=False,
                    ),
                )

    def show_inflate_psbt_page(self, psbt: str):
        """Display the unsigned PSBT for the inflate transaction itself in offline/watch-only."""
        if not self.isVisible():
            return
        if not psbt:
            return
        # Attach psbt to active/last draft so we can clean it up post-broadcast
        try:
            svc = WalletDataService.get_session()
            if svc is not None and self.params is not None:
                svc.add_psbt(
                    PsbtData(
                        psbt_base64=psbt,
                        signed=False, purpose='inflation',
                    ),
                )
                if self.params.asset_id:
                    svc.attach_inflate_psbt_to_secondary_draft(
                        self.params.asset_id, psbt,
                    )
        except Exception:
            pass
        if self.is_multisig:
            ToastManager.success(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_created_successfully', 'PSBT created successfully',
                ),
            )
            self._view_model.page_navigation.inflatable_asset_page()
        else:
            self._view_model.page_navigation.receive_asset_page(
                ReceiveAssetModel(
                    page_name='IFA secondary issuance',
                    address_info='psbt_info', psbt=psbt, is_signed=False,
                ),
            )

    def create_issue_inflatables_asset_draft(self, ticker, name, amount, inflation_amounts):
        """Create and save an Issue Asset draft when UTXOs are not available.
        It stores minimal metadata so the draft can be shown on the fungible page.
        """
        inflatables_wallet_service = WalletDataService.get_session()
        if inflatables_wallet_service is not None:
            inflatables_wallet_service.upsert_draft_issue_asset(
                IssueAssetDraftModel(
                    name=name,
                    ticker=ticker,
                    issued_amount=int(amount),
                    inflation_amounts=int(inflation_amounts),
                ),
            )

    def _load_inflatables_draft_data(self):
        """Load draft data using the draft ID"""
        wallet_service = WalletDataService.get_session()
        # Secondary issuance: resume from IFA secondary draft (amount only)
        try:
            if (
                self.secondary_issuance
                and self.from_draft
                and self.draft_id is not None
                and wallet_service is not None
            ):
                d = wallet_service.get_ifa_secondary_draft_by_id(
                    int(self.draft_id),
                )
                if isinstance(d, dict):
                    amt = d.get('amount')
                    if amt is not None:
                        self.ifa_form.issue_amount_input.setText(str(amt))
                    self.handle_button_enabled()
                return
        except Exception:
            pass

        drafts = wallet_service.list_draft_issue_assets()
        draft = next(
            (
                d for d in drafts if d.get(
                    'id',
                ) == self.draft_id
            ), None,
        )
        if draft:
            if 'name' in draft:
                self.ifa_form.name_input.setText(draft['name'])
            if 'ticker' in draft:
                self.ifa_form.ticker_input.setText(
                    draft['ticker'],
                )
            if 'issued_amount' in draft:
                self.ifa_form.issue_amount_input.setText(
                    str(draft['issued_amount']),
                )
            if 'inflation_amounts' in draft:
                self.ifa_form.total_supply_input.setText(
                    str(draft['inflation_amounts']),
                )
            self.handle_button_enabled()

    def validate_issuance_amount(self, amount):
        """Validate the issuance amount."""
        self.spendable_balance_validation()
        if self.ifa_form.error_label.isVisible():
            return
        max_amount_for_issuance = self.params.max_amount
        if not amount.strip().isdigit():
            self.ifa_form.hide_error()
            self.issue_ifa_btn.setDisabled(True)
            self.handle_button_enabled()
            return
        if max_amount_for_issuance is None:
            return
        if int(amount) > max_amount_for_issuance:
            self.ifa_form.error_label.setText(
                f"Amount exceeds maximum issuance amount of {
                    max_amount_for_issuance
                }",
            )
            self.ifa_form.error_label.show()
            self.issue_ifa_btn.setDisabled(True)
        else:
            self.ifa_form.hide_error()
        self.handle_button_enabled()

    def spendable_balance_validation(self):
        """Validate the spendable balance."""
        if self.asset_transactions.asset_balance.spendable == 0:
            self.ifa_form.error_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'spendable_balance_validation',
                ),
            )
            self.ifa_form.error_label.show()
            self.issue_ifa_btn.setDisabled(True)
            self.ifa_form.issue_amount_input.setReadOnly(True)
            self.ifa_form.fee_rate_input.setReadOnly(True)
        else:
            self.ifa_form.hide_error()
            self.ifa_form.issue_amount_input.setReadOnly(False)
            self.ifa_form.fee_rate_input.setReadOnly(False)
        self.handle_button_enabled()
