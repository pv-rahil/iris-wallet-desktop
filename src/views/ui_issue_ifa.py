# pylint: disable=too-many-instance-attributes, too-many-statements, unused-import
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
from PySide6.QtWidgets import QDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

import src.resources_rc
from accessible_constant import IFA_ASSET_AMOUNT
from accessible_constant import IFA_ASSET_NAME
from accessible_constant import IFA_ASSET_TICKER
from accessible_constant import IFA_ASSET_TOTAL_SUPPLY
from accessible_constant import ISSUE_IFA_ASSET_CLOSE_BUTTON
from accessible_constant import ISSUE_IFA_BUTTON
from src.data.repository.setting_card_repository import SettingCardRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.wallet_data_service import WalletDataService
from src.model.common_operation_model import IssueAssetDraftModel
from src.model.common_operation_model import ReceiveAssetModel
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import NetworkEnumModel
from src.model.enums.enums_model import PsbtStatus
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.helpers import register_multisig_button
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.rgb_model import RgbAssetPageLoadModel
from src.model.setting_model import DefaultFeeRate
from src.model.setting_model import DefaultMinConfirmation
from src.model.success_model import SuccessPageModel
from src.utils.common_utils import enforce_u64_max_input
from src.utils.common_utils import set_number_validator
from src.utils.common_utils import set_placeholder_value
from src.utils.constant import FEE_RATE
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.decorators.check_colorable_available import get_unspent_utxo_count
from src.utils.error_message import ERROR_NOT_ENOUGH_UNCOLORED
from src.utils.helpers import load_stylesheet
from src.utils.render_timer import RenderTimer
from src.viewmodels.main_view_model import MainViewModel
from src.views.components.buttons import PrimaryButton
from src.views.components.confirmation_dialog import ConfirmationDialog
from src.views.components.hw_operation_dialog import HardwareWalletOperationDialog
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame
from src.utils.info_message import INFO_OPERATION_POSTED_TO_MULTISIG_BRIDGE


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
        self.is_hardware_wallet = SettingRepository.get_key_storage_type(
        ) == KeyStorageType.HARDWARE_WALLET
        self.is_offline_wallet = SettingRepository.get_wallet_type(
        ) == WalletType.OFFLINE_TYPE_WALLET
        self.is_watch_only = SettingRepository.get_wallet_access_type(
        ) == WalletAccessType.WATCH_ONLY
        self.is_multisig = SettingRepository.get_wallet_signature_type(
        ) == WalletSignatureType.MULTI_SIG_WALLET
        self.asset_transactions: ListTransferAssetWithBalanceResponseModel | None = None
        self.value_of_default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        self._retry_after_utxo_inflate = False
        self.issue_ifa_grid_layout = QGridLayout(self)
        self.issue_ifa_grid_layout.setObjectName('issue_nia_grid_layout')
        self.issue_ifa_wallet_logo = WalletLogoFrame(self)
        self.issue_ifa_grid_layout.addWidget(
            self.issue_ifa_wallet_logo, 0, 0, 1, 2,
        )
        self.draft_id = draft_id
        self.from_draft = from_draft

        self.horizontal_spacer_ifa_widget = QSpacerItem(
            265,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_ifa_grid_layout.addItem(
            self.horizontal_spacer_ifa_widget, 1, 3, 1, 1,
        )

        self.vertical_spacer_ifa_widget = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_ifa_grid_layout.addItem(
            self.vertical_spacer_ifa_widget, 3, 1, 1, 1,
        )

        self.inflatables_horizontal_spacer_2 = QSpacerItem(
            266,
            20,
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self.issue_ifa_grid_layout.addItem(
            self.inflatables_horizontal_spacer_2, 2, 0, 1, 1,
        )

        self.issue_ifa_vertical_spacer_1 = QSpacerItem(
            20,
            190,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.issue_ifa_grid_layout.addItem(
            self.issue_ifa_vertical_spacer_1, 0, 2, 1, 1,
        )

        self.issue_ifa_widget = QWidget(self)
        self.issue_ifa_widget.setObjectName(
            'issue_nia_widget',
        )
        self.issue_ifa_widget.setMinimumSize(QSize(499, 608))
        self.issue_ifa_widget.setMaximumSize(QSize(466, 608))

        self.inner_grid_layout = QGridLayout(self.issue_ifa_widget)
        self.inner_grid_layout.setSpacing(6)
        self.inner_grid_layout.setObjectName('inner_grid_layout')
        self.inner_grid_layout.setContentsMargins(1, 4, 1, 30)
        self.vertical_layout_issue_ifa = QVBoxLayout()
        self.vertical_layout_issue_ifa.setSpacing(6)
        self.vertical_layout_issue_ifa.setObjectName(
            'vertical_layout_setup_wallet_password',
        )
        self.issue_ifa_title_layout = QHBoxLayout()
        self.issue_ifa_title_layout.setObjectName('horizontal_layout_1')
        self.issue_ifa_title_layout.setContentsMargins(35, 9, 40, 0)
        self.issue_ifa_title = QLabel(
            self.issue_ifa_widget,
        )
        self.issue_ifa_title.setObjectName(
            'set_wallet_password_label',
        )
        self.issue_ifa_title.setMinimumSize(QSize(415, 63))

        self.issue_ifa_title_layout.addWidget(self.issue_ifa_title)

        self.ifa_close_btn = QPushButton(self.issue_ifa_widget)
        self.ifa_close_btn.setAccessibleName(ISSUE_IFA_ASSET_CLOSE_BUTTON)
        self.ifa_close_btn.setObjectName('close_btn')
        self.ifa_close_btn.setMinimumSize(QSize(24, 24))
        self.ifa_close_btn.setMaximumSize(QSize(50, 65))
        self.ifa_close_btn.setAutoFillBackground(False)
        self.ifa_close_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        issue_ifa_close_icon = QIcon()
        issue_ifa_close_icon.addFile(
            ':/assets/x_circle.png',
            QSize(),
            QIcon.Normal,
            QIcon.Off,
        )
        self.ifa_close_btn.setIcon(issue_ifa_close_icon)
        self.ifa_close_btn.setIconSize(QSize(24, 24))
        self.ifa_close_btn.setCheckable(False)
        self.ifa_close_btn.setChecked(False)

        self.issue_ifa_title_layout.addWidget(
            self.ifa_close_btn, 0, Qt.AlignHCenter,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.issue_ifa_title_layout,
        )

        self.header_line = QFrame(self.issue_ifa_widget)
        self.header_line.setObjectName('line_3')

        self.header_line.setFrameShape(QFrame.HLine)
        self.header_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_ifa.addWidget(self.header_line)

        self.inflatables_asset_ticker_layout = QVBoxLayout()
        self.inflatables_asset_ticker_layout.setSpacing(0)
        self.inflatables_asset_ticker_layout.setObjectName('vertical_layout_1')
        self.inflatables_asset_ticker_layout.setContentsMargins(60, -1, 0, -1)

        self.inflatables_asset_ticker_label = QLabel(self.issue_ifa_widget)
        self.inflatables_asset_ticker_label.setObjectName('asset_ticker_label')
        self.inflatables_asset_ticker_label.setMinimumSize(QSize(0, 35))
        self.inflatables_asset_ticker_label.setBaseSize(QSize(0, 0))
        self.inflatables_asset_ticker_label.setAutoFillBackground(False)
        self.inflatables_asset_ticker_label.setFrameShadow(QFrame.Plain)
        self.inflatables_asset_ticker_label.setLineWidth(1)

        self.inflatables_asset_ticker_layout.addWidget(
            self.inflatables_asset_ticker_label,
        )

        self.inflatables_short_identifier_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_short_identifier_input.setObjectName(
            'issue_nia_input',
        )
        self.inflatables_short_identifier_input.setAccessibleName(
            IFA_ASSET_TICKER,
        )
        self.inflatables_short_identifier_input.setMinimumSize(QSize(0, 40))
        self.inflatables_short_identifier_input.setMaximumSize(QSize(370, 40))

        self.inflatables_short_identifier_input.setFrame(False)
        self.inflatables_short_identifier_input.setClearButtonEnabled(False)

        self.inflatables_asset_ticker_layout.addWidget(
            self.inflatables_short_identifier_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_ticker_layout,
        )

        self.inflatables_asset_name_layout = QVBoxLayout()
        self.inflatables_asset_name_layout.setSpacing(0)
        self.inflatables_asset_name_layout.setObjectName('vertical_layout_2')
        self.inflatables_asset_name_layout.setContentsMargins(60, -1, 0, -1)

        self.inflatables_asset_name_label = QLabel(self.issue_ifa_widget)
        self.inflatables_asset_name_label.setObjectName('asset_name_label')
        self.inflatables_asset_name_label.setMinimumSize(QSize(0, 40))
        self.inflatables_asset_name_label.setMaximumSize(QSize(370, 40))
        self.inflatables_asset_name_layout.addWidget(
            self.inflatables_asset_name_label,
        )

        self.inflatables_asset_name_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_asset_name_input.setObjectName('asset_name_input')
        self.inflatables_asset_name_input.setAccessibleName(IFA_ASSET_NAME)
        self.inflatables_asset_name_input.setMinimumSize(QSize(0, 40))
        self.inflatables_asset_name_input.setMaximumSize(QSize(370, 40))

        self.inflatables_asset_name_input.setFrame(False)
        self.inflatables_asset_name_input.setClearButtonEnabled(False)

        self.inflatables_asset_name_layout.addWidget(
            self.inflatables_asset_name_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_name_layout,
        )
        self.inflatables_asset_supply_layout = QVBoxLayout()
        self.inflatables_asset_supply_layout.setSpacing(0)
        self.inflatables_asset_supply_layout.setObjectName('vertical_layout_3')
        self.inflatables_asset_supply_layout.setContentsMargins(60, -1, 0, -1)

        # Total Supply title with info icon
        self.inflatables_total_supply_title_widget = QWidget(
            self.issue_ifa_widget,
        )
        self.inflatables_total_supply_title_layout = QHBoxLayout(
            self.inflatables_total_supply_title_widget,
        )
        self.inflatables_total_supply_title_layout.setContentsMargins(
            0, 0, 0, 0,
        )
        self.inflatables_total_supply_title_layout.setSpacing(0)
        self.inflatables_total_supply_label = QLabel(self.issue_ifa_widget)
        self.inflatables_total_supply_label.setObjectName('total_supply_label')
        self.inflatables_total_supply_label.setMinimumSize(QSize(0, 40))
        self.inflatables_total_supply_label.setMaximumSize(QSize(100, 40))
        self.inflatables_total_supply_title_layout.addWidget(
            self.inflatables_total_supply_label,
        )
        self.inflatables_total_supply_info_btn = QPushButton(
            self.issue_ifa_widget,
        )
        self.inflatables_total_supply_info_btn.setObjectName(
            'total_supply_info_btn',
        )
        self.inflatables_total_supply_info_btn.setCursor(
            QCursor(Qt.PointingHandCursor),
        )
        self.inflatables_total_supply_info_btn.setFlat(True)
        info_icon = QIcon(':/assets/info_circle.png')
        self.inflatables_total_supply_info_btn.setIcon(info_icon)
        self.inflatables_total_supply_info_btn.setIconSize(QSize(50, 50))
        self.inflatables_total_supply_info_btn.setFixedSize(QSize(50, 50))
        self.inflatables_total_supply_title_layout.addWidget(
            self.inflatables_total_supply_info_btn,
        )

        self.inflatables_total_supply_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_total_supply_input.setObjectName('amount_input')
        self.inflatables_total_supply_input.setAccessibleName(
            IFA_ASSET_TOTAL_SUPPLY,
        )
        self.inflatables_total_supply_input.setMinimumSize(QSize(0, 40))
        self.inflatables_total_supply_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.inflatables_total_supply_input)
        self.inflatables_total_supply_input.setFrame(False)
        self.inflatables_total_supply_input.setClearButtonEnabled(False)

        self.inflatables_issue_supply_label = QLabel(self.issue_ifa_widget)
        self.inflatables_issue_supply_label.setObjectName('total_supply_label')
        self.inflatables_issue_supply_label.setMinimumSize(QSize(0, 40))
        self.inflatables_issue_supply_label.setMaximumSize(QSize(370, 40))

        self.inflatables_issue_amount_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_issue_amount_input.setObjectName('amount_input')
        self.inflatables_issue_amount_input.setAccessibleName(IFA_ASSET_AMOUNT)
        self.inflatables_issue_amount_input.setMinimumSize(QSize(0, 40))
        self.inflatables_issue_amount_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.inflatables_issue_amount_input)
        self.inflatables_issue_amount_input.setFrame(False)
        self.inflatables_issue_amount_input.setClearButtonEnabled(False)

        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_total_supply_title_widget, alignment=Qt.AlignLeft,
        )
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_total_supply_input,
        )
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_issue_supply_label,
        )
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_issue_amount_input,
        )

        self.inflatables_error_label = QLabel(self.issue_ifa_widget)
        self.inflatables_error_label.setObjectName('error_label')
        self.inflatables_error_label.setMinimumSize(QSize(0, 40))
        self.inflatables_error_label.setMaximumSize(QSize(370, 40))
        self.inflatables_error_label.setWordWrap(True)
        self.inflatables_error_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter,
        )
        self.inflatables_error_label.setStyleSheet('color: #D32F2F;')
        self.inflatables_error_label.hide()
        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_error_label,
        )

        self.inflatables_fee_rate_label = QLabel(self.issue_ifa_widget)
        self.inflatables_fee_rate_label.setObjectName('fee_rate_label')
        self.inflatables_fee_rate_label.setMinimumSize(QSize(0, 40))
        self.inflatables_fee_rate_label.setMaximumSize(QSize(370, 40))

        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_fee_rate_label,
        )

        self.inflatables_fee_rate_input = QLineEdit(
            self.issue_ifa_widget,
        )
        self.inflatables_fee_rate_input.setObjectName('amount_input')
        self.inflatables_fee_rate_input.setMinimumSize(QSize(0, 40))
        self.inflatables_fee_rate_input.setMaximumSize(QSize(370, 40))
        set_number_validator(self.inflatables_fee_rate_input)
        self.inflatables_fee_rate_input.setFrame(False)
        self.inflatables_fee_rate_input.setClearButtonEnabled(False)
        self.inflatables_fee_rate_input.setText(
            str(self.value_of_default_fee_rate.fee_rate),
        )
        self.inflatables_fee_rate_input.setPlaceholderText(
            str(self.value_of_default_fee_rate.fee_rate),
        )

        self.inflatables_asset_supply_layout.addWidget(
            self.inflatables_fee_rate_input,
        )

        self.vertical_layout_issue_ifa.addLayout(
            self.inflatables_asset_supply_layout,
        )

        self.vertical_spacer_issue_ifa = QSpacerItem(
            20,
            40,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        )

        self.vertical_layout_issue_ifa.addItem(
            self.vertical_spacer_issue_ifa,
        )

        self.inflatables_footer_line = QFrame(self.issue_ifa_widget)
        self.inflatables_footer_line.setObjectName('bottom_line_frame')

        self.inflatables_footer_line.setFrameShape(QFrame.HLine)
        self.inflatables_footer_line.setFrameShadow(QFrame.Sunken)

        self.vertical_layout_issue_ifa.addWidget(self.inflatables_footer_line)

        self.inflatables_issue_button_spacer = QSpacerItem(
            20, 22, QSizePolicy.Preferred, QSizePolicy.Preferred,
        )
        self.vertical_layout_issue_ifa.addItem(
            self.inflatables_issue_button_spacer,
        )
        self.issue_ifa_btn = PrimaryButton()
        self.issue_ifa_btn.setAccessibleName(ISSUE_IFA_BUTTON)
        self.issue_ifa_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.issue_ifa_btn.setMinimumSize(QSize(402, 40))
        self.issue_ifa_btn.setMaximumSize(QSize(402, 40))

        self.issue_ifa_btn.setCursor(
            QCursor(Qt.CursorShape.PointingHandCursor),
        )
        self.vertical_layout_issue_ifa.addWidget(
            self.issue_ifa_btn, 0, Qt.AlignCenter,
        )

        self.inner_grid_layout.addLayout(
            self.vertical_layout_issue_ifa,
            0,
            0,
            1,
            1,
        )

        self.issue_ifa_grid_layout.addWidget(
            self.issue_ifa_widget,
            1, 1, 2, 2,
        )
        self.setup_ui_connection()
        self.retranslate_ui()
        # Apply prefill rules for secondary issuance
        if self.params is not None and self.secondary_issuance:
            if self.params.asset_name:
                self.inflatables_asset_name_input.setText(
                    self.params.asset_name,
                )
            if self.params.asset_id:
                self.inflatables_short_identifier_input.setText(
                    self.params.asset_id,
                )
                self.inflatables_short_identifier_input.setCursorPosition(0)
                self.inflatables_short_identifier_input.setReadOnly(True)
            # Hide total supply fields and lock name in secondary issuance
            self.inflatables_total_supply_title_widget.hide()
            self.inflatables_total_supply_input.hide()
            self.inflatables_asset_name_input.setReadOnly(True)
            self.issue_ifa_widget.setFixedHeight(608)

        if self.from_draft and self.draft_id:
            self._load_inflatables_draft_data()
        else:
            if not self.secondary_issuance:
                self.inflatables_short_identifier_input.setText('')
                self.inflatables_asset_name_input.setText('')
                self.inflatables_issue_amount_input.setText('')
                self.inflatables_fee_rate_label.hide()
                self.inflatables_fee_rate_input.hide()

    def setup_ui_connection(self):
        """Set up connections for UI elements."""
        self.inflatables_asset_name_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.inflatables_short_identifier_input.textChanged.connect(
            self.handle_button_enabled,
        )
        self.inflatables_issue_amount_input.textChanged.connect(
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
            self.inflatables_issue_amount_input.textChanged.connect(
                self.validate_issuance_amount,
            )
            view_model = self._view_model.cfa_view_model
            self.asset_transactions: ListTransferAssetWithBalanceResponseModel = view_model.txn_list
            self.spendable_balance_validation()
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
        self.inflatables_issue_amount_input.textChanged.connect(
            lambda: set_placeholder_value(self.inflatables_issue_amount_input),
        )
        self.inflatables_issue_amount_input.textChanged.connect(
            lambda text: enforce_u64_max_input(
                self.inflatables_issue_amount_input, text,
            ),
        )
        # Validate supply relationships only in primary issuance
        if not self.secondary_issuance:
            self.inflatables_total_supply_input.textChanged.connect(
                self.validate_supply_fields,
            )
            self.inflatables_issue_amount_input.textChanged.connect(
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
            self.inflatables_asset_ticker_label.setText(
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
            self.inflatables_fee_rate_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'ifa_fee_rate',
                    None,
                ),
            )
            self.inflatables_issue_supply_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'issue_new_supply',
                    None,
                ),
            )

        else:
            self.inflatables_asset_ticker_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'asset_ticker',
                    None,
                ),
            )
            self.inflatables_issue_supply_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'issue_supply',
                    None,
                ),
            )
        self.inflatables_short_identifier_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'short_identifier',
                None,
            ),
        )
        self.inflatables_asset_name_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'asset_name',
                None,
            ),
        )
        self.inflatables_asset_name_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'name_of_the_asset',
                None,
            ),
        )
        self.inflatables_issue_amount_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'amount_to_issue',
                None,
            ),
        )
        self.inflatables_total_supply_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        self.inflatables_total_supply_info_btn.setToolTip(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'ifa_total_supply_help',
                None,
            ),
        )
        self.inflatables_total_supply_input.setPlaceholderText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'total_supply',
                None,
            ),
        )
        # Fee label text via translation (sat/vB)
        self.inflatables_fee_rate_label.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT,
                'fee_rate_sat_vb',
                None,
            ),
        )
        self.inflatables_fee_rate_input.setPlaceholderText(
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
        short_identifier = self.inflatables_short_identifier_input.text().upper()
        asset_name = self.inflatables_asset_name_input.text()
        amount_to_issue = self.inflatables_issue_amount_input.text()
        total_supply = self.inflatables_total_supply_input.text()
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

    def on_secondary_issuance_click(self):
        """Handle the click event for secondary issuance."""
        value_of_default_min_confirmation: DefaultMinConfirmation = SettingCardRepository.get_default_min_confirmation()
        amount_to_issue = self.inflatables_issue_amount_input.text()
        fee_text = self.inflatables_fee_rate_input.text() or FEE_RATE
        svc = WalletDataService.get_session()
        if svc is not None and self.params is not None:
            active = None
            if self.from_draft and self.draft_id is not None:
                svc.set_active_secondary_draft(
                    int(self.draft_id), self.params.asset_id,
                )
            else:
                amt_text = amount_to_issue or ''
                pref_amt = int(amt_text) if amt_text.strip().isdigit() else None
                active = svc.get_active_secondary_draft_for_asset(
                    self.params.asset_id,
                )
                if active is None or active.get('amount') != pref_amt:
                    draft_id = svc.add_ifa_secondary_draft_meta(
                        asset_id=self.params.asset_id,
                        asset_name=self.params.asset_name,
                        amount=pref_amt,
                    )
                    if draft_id is not None:
                        svc.set_active_secondary_draft(
                            int(draft_id), self.params.asset_id,
                        )
                        self.draft_id = draft_id
                        self.from_draft = True
                else:
                    svc.set_active_secondary_draft(
                        int(active.get('id')), self.params.asset_id,
                    )
            existing_unsigned = None
            drafts = svc.list_psbt(False) or []
            for p in drafts:
                if p.get('purpose') == 'inflate_asset' and p.get('psbt'):
                    existing_unsigned = p.get('psbt')
                    break
            if existing_unsigned:
                self._view_model.utxo_creation_view_model.current_purpose = 'inflate_asset'
                self.show_inflate_psbt_page(existing_unsigned)
                return
        if (self.is_hardware_wallet and self.is_online_wallet) or self.is_watch_only or self.is_multisig:
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
            self.inflatables_short_identifier_input.text(),
            self.inflatables_issue_amount_input.text(),
            self.inflatables_asset_name_input.text(),
        ])

        valid_amounts = (
            self.inflatables_issue_amount_input.text() != '0' and
            self.inflatables_total_supply_input.text() != '0'
        )

        no_errors = not self.inflatables_error_label.isVisible()

        if inputs_filled and valid_amounts and no_errors:
            self.issue_ifa_btn.setDisabled(False)
        else:
            self.issue_ifa_btn.setDisabled(True)

    def _show_error(self, msg: str):
        self.inflatables_error_label.setText(msg)
        self.inflatables_error_label.show()

    def validate_supply_fields(self):
        """Inline validation for total vs initial/new issue supply (primary issuance only)."""
        if self.secondary_issuance:
            # No total supply field in secondary mode
            self.handle_button_enabled()
            return
        total_text = self.inflatables_total_supply_input.text()
        issue_text = self.inflatables_issue_amount_input.text()
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
            self.inflatables_error_label.hide()
        self.handle_button_enabled()

    def _delete_active_secondary_draft_on_success(self):
        if not self.secondary_issuance:
            return
        if not self.params or not self.params.asset_id:
            return
        svc = WalletDataService.get_session()
        if svc is None:
            return
        active = svc.get_active_secondary_draft_for_asset(
            self.params.asset_id,
        )
        if isinstance(active, dict) and active.get('id') is not None:
            svc.delete_ifa_secondary_draft(int(active.get('id')))

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

    def handle_ifa_hw_dialog(self, message: str, dialog_type: Enum):
        """Centralized hardware wallet dialog update handler."""
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(
            parent=self,
        )
        # Always close the dialog immediately on SUCCESS and delete secondary draft
        if dialog_type == PsbtStatus.SUCCESS:
            if ifa_hw_dialog.isVisible():
                ifa_hw_dialog.accept()
            try:
                if self.secondary_issuance and self.params is not None:
                    svc = WalletDataService.get_session()
                    if svc is not None:
                        active = None
                        if self.params.asset_id:  # ensure str, not None
                            active = svc.get_active_secondary_draft_for_asset(
                                self.params.asset_id,
                            )

                        if active and active.get('id'):
                            draft_id = active.get('id')
                            svc.delete_ifa_secondary_draft(
                                int(draft_id) if draft_id else 0,
                            )
            except Exception:
                pass
            return
        # Intercept common UTXO errors and route to UTXO creation (inflate path)
        if dialog_type == PsbtStatus.ERROR and message:
            if ('NoAvailableUtxos' in message) or (ERROR_NOT_ENOUGH_UNCOLORED in message):
                if not self._prompt_bitcoin_app_and_confirm():
                    return
                # Show confirmation dialog for multisig/watch-only wallets
                if (
                    SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET
                    or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
                ):
                    dialog = ConfirmationDialog(
                        message='UTXO creation is required before issuing this asset. '
                                'This will generate a PSBT that needs to be signed by all cosigners. ',
                        parent=self,
                        icon_type='info',
                    )
                    if dialog.exec() != QDialog.Accepted:
                        return
                self._retry_after_utxo_inflate = bool(self.secondary_issuance)
                utxo_purpose = 'inflate_asset' if self.secondary_issuance else 'issue_asset_ifa'
                # Determine only missing UTXOs to create (required = 3)
                current = get_unspent_utxo_count()
                needed = 3 - max(0, current - 1)
                needed = needed if needed > 0 else 1
                self._view_model.utxo_creation_view_model.create_utxos_begin(
                    purpose=utxo_purpose, num=needed,
                )
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
        if current_purpose not in ['issue_asset_ifa', 'inflate_asset']:
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
        if purpose not in ('issue_asset_ifa', 'inflate_asset'):
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
            elif purpose == 'inflate_asset':
                # Before retrying inflate, guide user to open RGB app on Ledger (HW-online only)
                if self.is_hardware_wallet and self.is_online_wallet and (self._retry_after_utxo_inflate or self.secondary_issuance):
                    if not self._prompt_rgb_app_and_confirm():
                        return
                self._retry_after_utxo_inflate = False
                self.on_secondary_issuance_click()

    def _close_hw_dialog_if_open(self):
        """Close the hardware wallet dialog if it is currently visible."""
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        if ifa_hw_dialog.isVisible():
            ifa_hw_dialog.accept()

    def _prompt_bitcoin_app_and_confirm(self) -> bool:
        """Prompt user to open Bitcoin/Bitcoin Test app on Ledger and return True if confirmed."""
        network = SettingRepository.get_wallet_network()
        expected_btc_app = 'Bitcoin' if network == NetworkEnumModel.MAINNET else 'Bitcoin Test'
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        ifa_hw_dialog.setMinimumWidth(500)
        guidance_msg = f"Please open '{
            expected_btc_app
        }' on your Ledger and click Continue."
        ifa_hw_dialog.set_loading(guidance_msg)
        ifa_hw_dialog.done_button.setText('Continue')
        ifa_hw_dialog.done_button.setVisible(True)
        ifa_hw_dialog.cancel_button.setVisible(True)
        if not ifa_hw_dialog.isVisible():
            ifa_hw_dialog.show()
        result = ifa_hw_dialog.exec()
        return result == QDialog.Accepted

    def _prompt_rgb_app_and_confirm(self) -> bool:
        """Prompt user to open RGB/RGB Test app on Ledger and return True if confirmed."""
        network = SettingRepository.get_wallet_network()
        expected_rgb_app = 'RGB' if network == NetworkEnumModel.MAINNET else 'RGB Test'
        ifa_hw_dialog = HardwareWalletOperationDialog.get_instance(parent=self)
        ifa_hw_dialog.setMinimumWidth(500)
        guidance_msg = f"Ready for secondary issuance. Please open '{
            expected_rgb_app
        }' on your Ledger and click Continue."
        ifa_hw_dialog.set_loading(guidance_msg)
        ifa_hw_dialog.done_button.setText('Continue')
        ifa_hw_dialog.done_button.setVisible(True)
        ifa_hw_dialog.cancel_button.setVisible(True)
        if not ifa_hw_dialog.isVisible():
            ifa_hw_dialog.show()
        result = ifa_hw_dialog.exec()
        return result == QDialog.Accepted

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
            target_purpose = 'inflate_asset' if self.secondary_issuance else 'issue_asset_ifa'
            existing_inflatables_psbt = next(
                (
                    p for p in unsigned_psbts if p.get('purpose') == target_purpose
                ), None,
            )
            if existing_inflatables_psbt and existing_inflatables_psbt.get('psbt'):
                self._view_model.utxo_creation_view_model.current_purpose = target_purpose
                self.show_ifa_psbt_page(existing_inflatables_psbt.get('psbt'))
                return
        # For HW-online, prompt for Bitcoin app first; for others, proceed directly to PSBT creation
        if self.is_hardware_wallet and self.is_online_wallet:
            if not self._prompt_bitcoin_app_and_confirm():
                return
            self._retry_after_utxo_inflate = bool(self.secondary_issuance)
        current = get_unspent_utxo_count()
        needed = 3 - max(0, current - 1)
        needed = needed if needed > 0 else 1
        # Show confirmation dialog for multisig/watch-only wallets
        if (
            SettingRepository.get_wallet_signature_type() == WalletSignatureType.MULTI_SIG_WALLET
            or SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
        ):
            dialog = ConfirmationDialog(
                message='UTXO creation is required before issuing this asset. '
                        'This will generate a PSBT that needs to be signed by all cosigners. ',
                parent=self,
                icon_type='info',
            )
            if dialog.exec() != QDialog.Accepted:
                return
        self._view_model.utxo_creation_view_model.create_utxos_begin(
            purpose='issue_asset_ifa', num=needed,
        )

    def show_ifa_psbt_page(self, inflatables_psbt):
        """Navigate to the receive asset page and display the PSBT as a QR code."""
        if not self.isVisible():
            return
        # Only respond if PSBT relates to IFA UTXO creation purposes
        if self._view_model.utxo_creation_view_model.current_purpose not in ['issue_asset_ifa', 'inflate_asset']:
            return
        if inflatables_psbt:
            if self.is_multisig:
                ToastManager.success(
                    QCoreApplication.translate(
                        IRIS_WALLET_TRANSLATIONS_CONTEXT, 'psbt_created_successfully', 'PSBT created successfully',
                    )
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
                svc.add_psbt(psbt, signed=False, purpose='inflate_asset')
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
                )
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
        inflatables_wallet_service = WalletDataService.get_session()
        # Secondary issuance: resume from IFA secondary draft (amount only)
        try:
            if (
                self.secondary_issuance
                and self.from_draft
                and self.draft_id is not None
                and inflatables_wallet_service is not None
            ):
                d = inflatables_wallet_service.get_ifa_secondary_draft_by_id(
                    int(self.draft_id),
                )
                if isinstance(d, dict):
                    amt = d.get('amount')
                    if amt is not None:
                        self.inflatables_issue_amount_input.setText(str(amt))
                    self.handle_button_enabled()
                return
        except Exception:
            pass

        inflatables_drafts = inflatables_wallet_service.list_draft_issue_assets()
        draft = next(
            (
                d for d in inflatables_drafts if d.get(
                    'id',
                ) == self.draft_id
            ), None,
        )
        if draft:
            if 'name' in draft:
                self.inflatables_asset_name_input.setText(draft['name'])
            if 'ticker' in draft:
                self.inflatables_short_identifier_input.setText(
                    draft['ticker'],
                )
            if 'issued_amount' in draft:
                self.inflatables_issue_amount_input.setText(
                    str(draft['issued_amount']),
                )
            if 'inflation_amounts' in draft:
                self.inflatables_total_supply_input.setText(
                    str(draft['inflation_amounts']),
                )
            self.handle_button_enabled()

    def validate_issuance_amount(self, amount):
        """Validate the issuance amount."""
        self.spendable_balance_validation()
        if self.inflatables_error_label.isVisible():
            return
        max_amount_for_issuance = self.params.max_amount
        if not amount.strip().isdigit():
            self.inflatables_error_label.hide()
            self.issue_ifa_btn.setDisabled(True)
            self.handle_button_enabled()
            return
        if max_amount_for_issuance is None:
            return
        if int(amount) > max_amount_for_issuance:
            self.inflatables_error_label.setText(
                f"Amount exceeds maximum issuance amount of {
                    max_amount_for_issuance
                }",
            )
            self.inflatables_error_label.show()
            self.issue_ifa_btn.setDisabled(True)
        else:
            self.inflatables_error_label.hide()
        self.handle_button_enabled()

    def spendable_balance_validation(self):
        """Validate the spendable balance."""
        if self.asset_transactions.asset_balance.spendable == 0:
            self.inflatables_error_label.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT,
                    'spendable_balance_validation',
                ),
            )
            self.inflatables_error_label.show()
            self.issue_ifa_btn.setDisabled(True)
            self.inflatables_issue_amount_input.setReadOnly(True)
            self.inflatables_fee_rate_input.setReadOnly(True)
        else:
            self.inflatables_error_label.hide()
            self.inflatables_issue_amount_input.setReadOnly(False)
            self.inflatables_fee_rate_input.setReadOnly(False)
        self.handle_button_enabled()
