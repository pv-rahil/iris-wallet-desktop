# pylint: disable=too-many-instance-attributes, too-few-public-methods
"""
Multisig setup page – full-page view.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtCore import QStandardPaths
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QSpacerItem
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from accessible_constant import MULTISIG_BACK_BUTTON
from accessible_constant import MULTISIG_CONTINUE_BUTTON
from accessible_constant import MULTISIG_EXPORT_BUTTON
from src.data.repository.setting_repository import SettingRepository
from src.data.service.multisig_setup_service import MultisigSetupService
from src.model.broadcast_transaction_model import MultisigThresholdLabels
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.utils.common_utils import copy_text
from src.utils.constant import ACCOUNT_XPUB_COLORED
from src.utils.constant import ACCOUNT_XPUB_VANILLA
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.constant import MASTER_FINGERPRINT
from src.utils.constant import VANILLA_KEYCHAIN
from src.utils.constant import WALLET_PASSWORD_KEY
from src.utils.helpers import load_stylesheet
from src.utils.keyring_storage import get_value
from src.utils.local_store import local_store
from src.utils.logging import logger
from src.utils.page_navigation_events import PageNavigationEventManager
from src.views.components.buttons import PrimaryButton
from src.views.components.buttons import SecondaryButton
from src.views.components.cosigner_detail_card import CosignerDetailCard
from src.views.components.multisig_cosigner_frame import CosignerFrame
from src.views.components.multisig_review_frame import ReviewFrame
from src.views.components.multisig_threshold_frame import ThresholdFrame
from src.views.components.toast import ToastManager
from src.views.components.wallet_logo_frame import WalletLogoFrame


class MultisigSetupPage(QWidget):
    """Multisig wallet setup page — handles threshold, key generation and cosigner collection."""

    def __init__(self, view_model):
        super().__init__()
        self._view_model = view_model
        self._threshold_locked = False
        self._current_step = 1
        self.footer: QHBoxLayout = None
        self.export_button: PrimaryButton = None
        self.back_button: PrimaryButton = None
        self.reset_button: PrimaryButton = None
        self.title: QLabel = None
        self.close_btn: QPushButton = None
        self.creator_frame: QFrame = None
        self.creator_v: QVBoxLayout = None
        self.creator_actions: QHBoxLayout = None

        network = SettingRepository.get_wallet_network()
        self._password = get_value(WALLET_PASSWORD_KEY, network.value)

        if not self._password:
            logger.error('Multisig setup accessed without password set!')
            PageNavigationEventManager.get_instance().selection_page_signal.emit(None)
            return

        self._setup_models()
        self._setup_ui()
        self._setup_connections()
        self.retranslate_ui()
        saved_m, saved_n = SettingRepository.get_multisig_config()
        if saved_m and saved_n:
            self.threshold_frame.required_signer_input.setText(str(saved_m))
            self.threshold_frame.total_signer_input.setText(str(saved_n))

            is_hardware_wallet = SettingRepository.get_key_storage_type(
            ) == KeyStorageType.HARDWARE_WALLET
            if is_hardware_wallet and not self._is_watch_only:
                master_fp = local_store.get_value(MASTER_FINGERPRINT)
                account_xpub_vanilla = local_store.get_value(
                    ACCOUNT_XPUB_VANILLA,
                )
                account_xpub_colored = local_store.get_value(
                    ACCOUNT_XPUB_COLORED,
                )

                if master_fp and account_xpub_vanilla and account_xpub_colored:
                    self._complete_threshold_confirmation_after_hw_connect(
                        saved_m, saved_n,
                    )
                    return

            stored_cosigners = SettingRepository.get_cosigners()
            if stored_cosigners:
                self._restore_cosigner_inputs(stored_cosigners)
                self._update_continue_enabled()
        self.back_button.hide()
        self._update_summary()
        self._update_continue_enabled()

    def _setup_ui(self):
        """Build and wire the widget tree."""
        self.setStyleSheet(
            load_stylesheet(
                'views/qss/multisig_setup_page.qss',
            ),
        )

        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)

        self.logo = WalletLogoFrame(self)
        self.grid.addWidget(self.logo, 0, 0, 1, 2)
        self.grid.addItem(
            QSpacerItem(
                268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
            ), 1, 0,
        )

        self.card = QWidget(self)
        self.card.setObjectName('ms_page_card')
        self.card.setMinimumSize(QSize(770, 530))
        self.card.setMaximumSize(QSize(770, 530))
        self.v = QVBoxLayout(self.card)
        self.v.setContentsMargins(0, 12, 0, 20)
        self.v.setSpacing(10)
        self.vertical_layout = self.v
        self.breadcrumb_widget = None

        self.continue_button = PrimaryButton()
        self.continue_button.setFixedSize(QSize(100, 40))
        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.continue_button.setAccessibleName(MULTISIG_CONTINUE_BUTTON)

        # Title row
        self._build_title_row()

        # Step 1: Threshold frame
        self.threshold_frame = ThresholdFrame(self.card)
        self.v.addWidget(self.threshold_frame)

        # Step 2: Review frame (hidden until step 2)
        self.review_frame = ReviewFrame(self.card)
        self.v.addWidget(self.review_frame)

        # Creator frame (action row placeholder)
        self._build_creator_frame()

        # Step 3: Cosigners frame (hidden until step 3)
        self.cos_frame = CosignerFrame(self.card)
        self.v.addWidget(self.cos_frame)

        # Footer
        self._build_footer()

        # Grid spacers
        self.grid.addItem(
            QSpacerItem(
                20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding,
            ), 0, 1,
        )
        self.grid.addWidget(self.card, 1, 1)
        self.grid.addItem(
            QSpacerItem(
                20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding,
            ), 2, 1,
        )
        self.grid.addItem(
            QSpacerItem(
                268, 20, QSizePolicy.Expanding, QSizePolicy.Minimum,
            ), 1, 2,
        )

    def _build_title_row(self):
        """Build the title row with close button."""
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(30, 9, 30, 0)
        self.title = QLabel()
        self.title.setObjectName('ms_title')
        self.title.setMinimumSize(QSize(415, 63))
        self.title.setMaximumSize(QSize(415, 63))
        title_layout.addWidget(self.title)
        title_layout.addStretch()

        self.close_btn = QPushButton()
        self.close_btn.setObjectName('close_button')
        self.close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setIcon(QIcon(':/assets/x_circle.png'))
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.clicked.connect(
            self._view_model.page_navigation.selection_page,
        )
        title_layout.addWidget(self.close_btn)
        self.v.addLayout(title_layout)
        self.close_btn.show()

        above_line = QFrame(self.card)
        above_line.setObjectName('above_line_frame')
        above_line.setFrameShape(QFrame.HLine)
        above_line.setFrameShadow(QFrame.Sunken)
        self.v.addWidget(above_line)

    def _build_creator_frame(self):
        """Build the creator frame for action row."""
        self.creator_frame = QFrame(self.card)
        self.creator_frame.setObjectName('capabilities_frame')
        self.creator_frame.hide()
        self.creator_v = QVBoxLayout(self.creator_frame)
        self.creator_v.setContentsMargins(35, 0, 20, 0)
        self.creator_actions = QHBoxLayout()
        self.creator_actions.setContentsMargins(35, 0, 0, 0)
        self.creator_actions.setSpacing(12)
        self.creator_v.addLayout(self.creator_actions)
        self.v.addWidget(self.creator_frame)

    def _setup_models(self):
        """Initialize internal state models."""
        self._threshold_locked = False
        self._current_step = 1
        self._is_watch_only = (
            SettingRepository.get_wallet_access_type() == WalletAccessType.WATCH_ONLY
        )
        self._steps_total = 2 if self._is_watch_only else 3

    def _setup_connections(self):
        """Connect UI signals to slots."""
        self.threshold_frame.required_signer_input.textChanged.connect(
            self._update_summary,
        )
        self.threshold_frame.total_signer_input.textChanged.connect(
            self._update_summary,
        )
        self.threshold_frame.required_signer_input.textChanged.connect(
            self._update_continue_enabled,
        )
        self.threshold_frame.total_signer_input.textChanged.connect(
            self._update_continue_enabled,
        )

    def _build_footer(self):
        self.footer = QHBoxLayout()
        self.footer.setContentsMargins(0, 4, 35, 12)

        self.export_button = PrimaryButton()
        self.export_button.setIcon(QIcon(':/assets/export.png'))
        self.export_button.setIconSize(QSize(18, 18))
        self.export_button.setLayoutDirection(Qt.RightToLeft)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.setFixedSize(QSize(100, 40))
        self.export_button.setAccessibleName(MULTISIG_EXPORT_BUTTON)
        self.export_button.hide()
        self.export_button.clicked.connect(self._export_cosigner_to_file)
        self.footer.addSpacing(35)
        self.footer.addWidget(self.export_button)

        self.back_button = PrimaryButton()
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_button.setFixedSize(QSize(100, 40))
        self.back_button.setAccessibleName(MULTISIG_BACK_BUTTON)
        self.back_button.clicked.connect(self._go_back)
        self.footer.addStretch()
        self.footer.addSpacing(12)
        self.footer.addWidget(self.back_button)
        self.footer.addSpacing(12)
        self.continue_button.clicked.connect(self._go_next)
        self.footer.addWidget(self.continue_button)
        self.v.addLayout(self.footer)

    def retranslate_ui(self):
        """Set or refresh all translatable UI strings."""
        self.title.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'multisig_setup_title',
            ),
        )
        self.back_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'back',
            ),
        )
        self.export_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'export',
            ) + ' ',
        )
        # Update threshold frame strings
        labels = MultisigThresholdLabels(
            info_title=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configure_signature_requirements',
            ),
            info_sub=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'choose_number_of_signatures',
            ),
            tot_lbl=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_label',
            ),
            tot_help=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'total_cosigners_help',
            ),
            req_lbl=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'required_signatures_label',
            ),
            req_help=QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'required_signatures_help',
            ),
        )
        self.threshold_frame.retranslate_ui(labels)
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
            ),
        )

    def _complete_threshold_confirmation_after_hw_connect(self, _m: int, n: int):
        """Complete threshold confirmation after returning from hardware wallet setup."""
        self.threshold_frame.set_inputs_enabled(False)
        self._threshold_locked = True

        self.cos_frame.clear_cosigner_rows()

        for i in range(2, n + 1):
            self._add_cosigner_row(i)

        self.threshold_frame.hide()
        self.creator_frame.hide()
        self.back_button.show()
        self.close_btn.hide()

        if self._is_watch_only:
            self.cos_frame.show()
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 640))
            self.card.setMaximumSize(QSize(770, 640))
            self._update_continue_enabled()
            self.continue_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
                ),
            )
        else:
            self._populate_wallet_review_fields()
            self.review_frame.show()
            self.cos_frame.hide()
            self._current_step = 2
            self.export_button.show()
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
            self._update_continue_enabled()
            self.continue_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                ),
            )

    def _generate_wallet_keys(self) -> bool:
        """Generate wallet keys for multisig setup. Returns True on success."""
        result = MultisigSetupService.generate_wallet_keys(self._password)
        if result is None:
            return False
        return True

    def _on_confirm_threshold(self) -> bool:
        """Lock threshold and create exact N cosigner rows."""
        n = self._get_total_signer()
        m = self._get_required_signer()
        if m > n or m < 1 or n < 2:
            return False

        self.threshold_frame.set_inputs_enabled(False)
        self._threshold_locked = True
        SettingRepository.set_multisig_config(m, n)

        is_hardware_wallet = SettingRepository.get_key_storage_type(
        ) == KeyStorageType.HARDWARE_WALLET

        if not self._is_watch_only:
            if is_hardware_wallet:
                SettingRepository.set_multisig_config(m, n)
                self._view_model.page_navigation.hardware_wallet_connect_page(
                    is_multisig=True,
                )
                return True

            if not self._generate_wallet_keys():
                self.threshold_frame.set_inputs_enabled(True)
                self._threshold_locked = False
                SettingRepository.set_multisig_config(None, None)
                return False

        self.cos_frame.clear_cosigner_rows()

        for i in range(2, n + 1):
            self._add_cosigner_row(i)

        self.continue_button.setEnabled(False)
        self._threshold_locked = True
        self.threshold_frame.set_inputs_enabled(False)
        self._update_summary()
        self._update_continue_enabled()
        return True

    def _handle_step1_transition(self) -> None:
        """Handle transition from step 1 to step 2."""
        if not self._on_confirm_threshold():
            self._update_continue_enabled()
            return

        self.threshold_frame.hide()
        self.creator_frame.hide()
        self.back_button.show()
        self.close_btn.hide()

        if self._is_watch_only:
            self._configure_watch_only_review_fields()
            self.review_frame.show()
            self.cos_frame.hide()
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
        else:
            self._populate_wallet_review_fields()
            self.review_frame.show()
            self.cos_frame.hide()
            self._current_step = 2
            self.export_button.show()
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
        self._update_continue_enabled()
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
            ),
        )

    def _handle_step2_transition(self) -> None:
        """Handle transition from step 2 to step 3."""
        if self._is_watch_only:
            if not self._save_watch_only_review_fields():
                self._update_continue_enabled()
                return
            self.review_frame.hide()
            self.cos_frame.show()
            if hasattr(self, 'reset_button'):
                self.footer.replaceWidget(
                    self.reset_button, self.export_button,
                )
                self.reset_button.deleteLater()
                del self.reset_button
            self.export_button.hide()
            self._current_step = 3
        else:
            self.review_frame.hide()
            self.cos_frame.show()
            self.export_button.hide()
            self._current_step = 3

        total_signer = self._get_total_signer()
        if total_signer > 2:
            self.card.setMinimumSize(QSize(770, 640))
            self.card.setMaximumSize(QSize(770, 640))
        else:
            self.card.setMinimumSize(QSize(770, 520))
            self.card.setMaximumSize(QSize(770, 520))
        self.continue_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'continue',
            ),
        )
        self._update_continue_enabled()

    def _go_next(self):
        self.continue_button.setEnabled(False)
        if self._current_step == 1:
            self._handle_step1_transition()
        elif self._current_step == 2:
            self._handle_step2_transition()
        elif self._current_step == 3:
            if not self._save_cosigners_data():
                self._update_continue_enabled()
                return
            self._view_model.page_navigation.welcome_page()

    def _go_back(self):
        if self._current_step == 2:
            self.threshold_frame.set_inputs_enabled(True)
            self.cos_frame.hide()
            self.review_frame.hide()
            self.threshold_frame.show()
            self.creator_frame.hide()
            self.back_button.hide()
            self.export_button.hide()
            self._current_step = 1
            self.card.setMinimumSize(QSize(770, 530))
            self.card.setMaximumSize(QSize(770, 530))
            self._update_summary()
            self._update_continue_enabled()
            self.close_btn.show()
            SettingRepository.set_multisig_config(None, None)
            self.continue_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                ),
            )
        elif self._current_step == 3:
            self.cos_frame.hide()
            self.review_frame.show()
            self.export_button.show()
            self._current_step = 2
            self.card.setMinimumSize(QSize(770, 570))
            self.card.setMaximumSize(QSize(770, 570))
            self._update_continue_enabled()
            self.continue_button.setText(
                QCoreApplication.translate(
                    IRIS_WALLET_TRANSLATIONS_CONTEXT, 'next',
                ),
            )

    def _configure_watch_only_review_fields(self):
        self._populate_wallet_review_fields()
        self.export_button.hide()
        self.review_frame.clear_fields()
        self.review_frame.cosigner_string_value_widget.setReadOnly(False)
        if self.review_frame.cosigner_string_copy_btn:
            self.review_frame.cosigner_string_copy_btn.hide()
        self.reset_button = SecondaryButton()
        self.reset_button.setIcon(QIcon(':/assets/x_cross.png'))
        self.reset_button.setIconSize(QSize(18, 18))
        self.reset_button.setLayoutDirection(Qt.RightToLeft)
        self.reset_button.setFixedSize(QSize(100, 36))
        self.reset_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_button.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'reset',
            ) + ' ',
        )
        self.reset_button.clicked.connect(self._on_watch_only_reset_clicked)
        self.footer.replaceWidget(self.export_button, self.reset_button)
        self.export_button.hide()
        self.review_frame.cosigner_string_value_widget.textChanged.connect(
            self._on_watch_only_cosigner_string_changed,
        )

    def _on_watch_only_reset_clicked(self):
        self.review_frame.clear_fields()
        self._update_continue_enabled()

    def _on_watch_only_cosigner_string_changed(self, text):
        result = MultisigSetupService.parse_cosigner_string(text)
        if not result.is_valid:
            self.review_frame.clear_fields()
            self._update_continue_enabled()
            return
        self.review_frame.fp_value_widget.setText(result.master_fingerprint)
        self.review_frame.keychain_value_widget.setText(
            str(result.vanilla_keychain) if result.vanilla_keychain is not None else '',
        )
        self.review_frame.xpub_vanilla_value_widget.setText(
            result.account_xpub_vanilla,
        )
        self.review_frame.xpub_colored_value_widget.setText(
            result.account_xpub_colored,
        )
        self._update_continue_enabled()

    def _save_watch_only_review_fields(self) -> bool:
        fp = self.review_frame.fp_value_widget.text().strip()
        keychain = self.review_frame.keychain_value_widget.text().strip()
        vanilla = self.review_frame.xpub_vanilla_value_widget.text().strip()
        colored = self.review_frame.xpub_colored_value_widget.text().strip()
        return MultisigSetupService.save_watch_only_data(fp, keychain, vanilla, colored)

    def _populate_wallet_review_fields(self):
        data = MultisigSetupService.get_wallet_review_data()

        self.review_frame.fp_value_widget.setText(data['master_fingerprint'])
        self.review_frame.keychain_value_widget.setText(data['keychain'])
        self.review_frame.path_value_widget.setText(data['derivation_path'])
        self.review_frame.xpub_vanilla_value_widget.setText(
            MultisigSetupService.truncate_text(data['account_xpub_vanilla']),
        )
        self.review_frame.xpub_colored_value_widget.setText(
            MultisigSetupService.truncate_text(data['account_xpub_colored']),
        )

        if not self._is_watch_only:
            if data['master_fingerprint'] and data['account_xpub_vanilla'] and data['account_xpub_colored']:
                cosigner_str = MultisigSetupService.generate_cosigner_string(
                    data['master_fingerprint'],
                    data['account_xpub_vanilla'],
                    data['account_xpub_colored'],
                    int(data['keychain']) if data['keychain'].isdigit() else 0,
                )
                if cosigner_str:
                    self.review_frame.cosigner_string_value_widget.setText(
                        cosigner_str,
                    )
                    self.review_frame.cosigner_string_value_widget.setCursorPosition(
                        0,
                    )
                    self.review_frame.cosigner_string_copy_btn.clicked.connect(
                        lambda: copy_text(cosigner_str),
                    )
                    self.review_frame.xpub_colored_copy_btn.clicked.connect(
                        lambda: copy_text(data['account_xpub_colored']),
                    )
                else:
                    self.review_frame.cosigner_string_value_widget.setText(
                        'Error generating string',
                    )
            else:
                self.review_frame.cosigner_string_value_widget.setText(
                    'Incomplete signer data',
                )

    def _add_cosigner_row(self, index: int):
        card = CosignerDetailCard(index, self)
        if self._get_total_signer() == 2:
            card.set_collapsible(False)
        if card.import_btn:
            card.import_btn.clicked.connect(
                lambda: self._import_cosigner_from_file(card),
            )
        if card.reset_btn:
            card.reset_btn.clicked.connect(card.string_input.clear)
        if card.string_input:
            card.string_input.textChanged.connect(
                lambda text, c=card: self._on_cosigner_string_changed(text, c),
            )
        self.cos_frame.add_cosigner_row(card)
        if index == 2 and card.string_input:
            card.string_input.setFocus()

    def _on_cosigner_string_changed(self, text, row_w):
        row_w.string_input.setCursorPosition(0)
        result = MultisigSetupService.parse_cosigner_string(text)
        if not result.is_valid:
            row_w.fp_input.clear()
            row_w.vanilla_xpub_input.clear()
            row_w.colored_xpub_input.clear()
            row_w.keychain_input.clear()
            row_w.string_input.setReadOnly(False)
            row_w.import_btn.setVisible(True)
            row_w.reset_btn.setVisible(False)
            self._update_continue_enabled()
            return
        row_w.fp_input.setText(result.master_fingerprint)
        row_w.vanilla_xpub_input.setText(
            MultisigSetupService.truncate_text(result.account_xpub_vanilla),
        )
        row_w.vanilla_xpub_str = result.account_xpub_vanilla
        row_w.colored_xpub_input.setText(
            MultisigSetupService.truncate_text(result.account_xpub_colored),
        )
        row_w.colored_xpub_str = result.account_xpub_colored
        row_w.keychain_input.setText(
            str(result.vanilla_keychain) if result.vanilla_keychain is not None else '0',
        )
        self._update_continue_enabled()
        row_w.string_input.setReadOnly(True)
        row_w.import_btn.setVisible(False)
        row_w.reset_btn.setVisible(True)

    def _restore_cosigner_inputs(self, cosigners_data: list[dict]):
        if not self._threshold_locked:
            self._on_confirm_threshold()
        for data in cosigners_data:
            idx = data.get('index')
            if not idx:
                continue
            target_card = next(
                (c for c in self.cos_frame.get_cosigner_rows() if c.index == idx), None,
            )
            if target_card:
                if MASTER_FINGERPRINT in data:
                    target_card.fp_input.setText(data[MASTER_FINGERPRINT])
                if VANILLA_KEYCHAIN in data:
                    val = data[VANILLA_KEYCHAIN]
                    target_card.keychain_input.setText(
                        str(val) if val is not None else '0',
                    )
                if ACCOUNT_XPUB_VANILLA in data:
                    target_card.vanilla_xpub_input.setText(
                        MultisigSetupService.truncate_text(
                            data[ACCOUNT_XPUB_VANILLA],
                        ),
                    )
                    target_card.vanilla_xpub_str = data[ACCOUNT_XPUB_VANILLA]
                if ACCOUNT_XPUB_COLORED in data:
                    target_card.colored_xpub_input.setText(
                        MultisigSetupService.truncate_text(
                            data[ACCOUNT_XPUB_COLORED],
                        ),
                    )
                    target_card.colored_xpub_str = data[ACCOUNT_XPUB_COLORED]
        self.threshold_frame.set_inputs_enabled(False)

    def _save_cosigners_data(self) -> bool:
        cosigner_rows = []
        for card in self.cos_frame.get_cosigner_rows():
            card.clear_error()
            cosigner_string = card.string_input.text().strip()
            if not cosigner_string:
                card.show_error('Cosigner details required')
                return False
            result = MultisigSetupService.parse_cosigner_string(
                cosigner_string,
            )
            if not result.is_valid:
                card.show_error('Invalid cosigner details')
                return False
            cosigner_rows.append({
                'index': card.index,
                'string': cosigner_string,
            })
        return MultisigSetupService.save_cosigners_data(cosigner_rows)

    def _get_required_signer(self) -> int:
        return self.threshold_frame.get_required_signer()

    def _get_total_signer(self) -> int:
        return self.threshold_frame.get_total_signer()

    def _update_continue_enabled(self):
        if self._current_step == 1:
            n = self._get_total_signer()
            m = self._get_required_signer()
            self.continue_button.setEnabled((2 <= n <= 15) and (2 <= m <= n))
            return

        if self.cos_frame.isVisible():
            n = self._get_total_signer()
            cosigner_rows = self.cos_frame.get_cosigner_rows()
            n_rows = len(cosigner_rows)
            all_filled = all_valid = True
            any_duplicates = False
            seen = set()
            for card in cosigner_rows:
                card.clear_error()
                xpub_str = card.vanilla_xpub_str
                if xpub_str:
                    if xpub_str in seen:
                        card.show_error('Duplicate Cosigner')
                        any_duplicates = True
                        all_valid = False
                    else:
                        seen.add(xpub_str)
                else:
                    all_filled = False
                    if card.string_input.text().strip():
                        card.show_error('Invalid cosigner details')
                        all_valid = False
            self.continue_button.setEnabled(
                all_filled and all_valid and not any_duplicates and n_rows == n - 1,
            )
        else:
            self.continue_button.setEnabled(True)

    def _update_summary(self):
        n = self._get_total_signer()
        m = self._get_required_signer()
        self.threshold_frame.summary_text.setText(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'configuration_note',
            ).format(m if m >= 1 else 0, n if n >= 1 else 0),
        )

    def _export_cosigner_to_file(self):
        download_dir = QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation,
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export Cosigner Data',
            os.path.join(download_dir, 'cosigner.txt'),
            'Text Files (*.txt);;All Files (*)',
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.review_frame.cosigner_string_value_widget.text())
                ToastManager.success(
                    description='Cosigner data exported successfully!', parent=self,
                )
            except Exception as e:
                logger.error('Failed to export cosigner data: %s', e)
                ToastManager.error(
                    description=f'Failed to export cosigner data: {e}', parent=self,
                )

    def _import_cosigner_from_file(self, target_card):
        downloads_dir = QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation,
        )
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Import Cosigner Data', downloads_dir,
            'Text Files (*.txt);;All Files (*)',
        )
        if file_path:
            try:
                with open(file_path, encoding='utf-8') as f:
                    cosigner_string = f.read().strip()
                target_card.string_input.setText(cosigner_string)
                if not target_card.is_expanded:
                    target_card.toggle_content()
                ToastManager.success(
                    description='Cosigner data imported successfully!', parent=self,
                )
            except Exception as e:
                logger.error('Failed to import cosigner data: %s', e)
                ToastManager.error(
                    description=f'Failed to import cosigner data: {e}', parent=self,
                )
