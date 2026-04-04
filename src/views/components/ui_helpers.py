# pylint: disable=too-few-public-methods
"""Common UI utilities to reduce code duplication across views."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from src.data.repository.setting_repository import SettingRepository
from src.model.enums.enums_model import KeyStorageType
from src.model.enums.enums_model import WalletAccessType
from src.model.enums.enums_model import WalletSignatureType
from src.model.enums.enums_model import WalletType
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.helpers import register_multisig_button
from src.views.components.buttons import PrimaryButton


def setup_issue_button_connection(
    button: PrimaryButton,
    view_model,
    target_page,
    is_multisig: bool,
    is_offline_wallet: bool,
    parent_layout,
) -> None:
    """Setup button click connection for issue asset navigation.

    Args:
        button: The button to connect.
        view_model: The main view model.
        target_page: The target page to navigate to.
        is_multisig: Whether wallet is multisig.
        is_offline_wallet: Whether wallet is offline.
        parent_layout: Layout to add button to if not offline.
    """
    if not is_multisig:
        button.clicked.connect(
            lambda: view_model.main_asset_view_model.navigate_issue_asset(
                target_page,
            ),
        )
    else:
        register_multisig_button(
            view_model,
            button,
            lambda: view_model.main_asset_view_model.navigate_issue_asset(
                target_page,
            ),
        )
    if not is_offline_wallet:
        parent_layout.addWidget(button, 0, Qt.AlignHCenter)


@dataclass
class WalletTypeFlags:
    """Container for wallet type flag values."""

    is_hardware_wallet: bool
    is_offline_wallet: bool
    is_watch_only: bool
    is_multisig: bool


def get_wallet_type_flags() -> WalletTypeFlags:
    """Get wallet type flags from settings repository.

    Returns:
        WalletTypeFlags: Dataclass containing all wallet type flags.
    """
    return WalletTypeFlags(
        is_hardware_wallet=SettingRepository.get_key_storage_type()
        == KeyStorageType.HARDWARE_WALLET,
        is_offline_wallet=SettingRepository.get_wallet_type()
        == WalletType.OFFLINE_TYPE_WALLET,
        is_watch_only=SettingRepository.get_wallet_access_type()
        == WalletAccessType.WATCH_ONLY,
        is_multisig=SettingRepository.get_wallet_signature_type()
        == WalletSignatureType.MULTI_SIG_WALLET,
    )


def create_empty_state_widget(
    button_text_key: str,
    button_accessible_name: str,
    parent: QWidget | None = None,
    transparent: bool = False,
) -> tuple[QFrame, PrimaryButton]:
    """Create an empty state widget with title, subtitle, and action button.

    Args:
        button_text_key: Translation key for the button text.
        button_accessible_name: Accessible name for the button.
        parent: Optional parent widget.
        transparent: Whether to use transparent background styling.

    Returns:
        tuple[QFrame, PrimaryButton]: The configured empty state frame and button.
    """
    wrapper = QFrame(parent)
    if transparent:
        wrapper.setStyleSheet(
            'QFrame{border:none; background: transparent;} QLabel{background:transparent;}',
        )
    wrapper.setFixedWidth(680)
    wrapper.setFixedHeight(200)

    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(2)

    # Title
    title = QLabel()
    title.setText(
        QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT,
            'no_assets_issued',
        ),
    )
    title.setStyleSheet('color:#fff; font:600 20px "Inter"; border:none;')
    layout.addWidget(title, 0, Qt.AlignHCenter)

    # Subtitle
    subtitle = QLabel()
    subtitle.setText(
        QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT,
            'no_assets_issued_sub',
        ),
    )
    subtitle.setStyleSheet(
        'color: rgba(255,255,255,0.75); font: 14px "Inter"; border:none;',
    )
    subtitle.setWordWrap(True)
    subtitle.setAlignment(Qt.AlignHCenter)
    subtitle.setFixedWidth(560)
    layout.addWidget(subtitle, 0, Qt.AlignHCenter)

    # Action button
    button = PrimaryButton()
    button.setText(
        QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT,
            button_text_key,
        ),
    )
    button.setAccessibleName(button_accessible_name)
    button.setCursor(QCursor(Qt.PointingHandCursor))
    button.setFixedWidth(200)

    return wrapper, button
