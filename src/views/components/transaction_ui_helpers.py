"""Transaction UI helper functions for RGB asset detail."""
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from rgb_lib import TransferKind
from rgb_lib import TransferStatus

from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT


def map_transfer_status(transfer_status) -> str:
    """Map TransferStatus to corresponding TransactionStatusEnumModel.

    Args:
        transfer_status: The transfer status to map.

    Returns:
        The mapped status string.
    """
    status = {
        TransferStatus.WAITING_COUNTERPARTY: TransactionStatusEnumModel.WAITING_COUNTERPARTY.value,
        TransferStatus.WAITING_CONFIRMATIONS: TransactionStatusEnumModel.WAITING_CONFIRMATIONS.value,
        TransferStatus.FAILED: TransactionStatusEnumModel.FAILED.value,
    }
    return status.get(transfer_status, TransactionStatusEnumModel.FAILED)


def apply_transaction_style_by_status(
    frame,
    transfer_status: str,
    transaction_date: str,
) -> None:
    """Apply styling to transaction frame based on transfer status.

    Args:
        frame: The transaction detail frame to style.
        transfer_status: The transfer status string.
        transaction_date: The transaction date string.
    """
    if transfer_status == TransferStatusEnumModel.SENT.value:
        frame.transaction_amount.setStyleSheet(
            'color:#EB5A5A;font-weight: 600',
        )
    if transfer_status == TransferStatusEnumModel.RECEIVED.value:
        frame.transaction_amount.setStyleSheet(
            'color:#01A781;font-weight: 600',
        )
    if transaction_date == TransactionStatusEnumModel.FAILED:
        frame.transaction_amount.setStyleSheet(
            'color:#EB5A5A;font-weight: 600',
        )


def configure_transaction_time_display(
    frame,
    transaction_time: str,
    transaction_date: str,
    transaction_status,
) -> None:
    """Configure transaction time display based on status.

    Args:
        frame: The transaction detail frame.
        transaction_time: The transaction time string.
        transaction_date: The transaction date string.
        transaction_status: The transaction status object.
    """
    frame.transaction_time.setText(transaction_time)
    frame.transaction_date.setText(transaction_date)
    if transaction_status != TransferStatus.SETTLED:
        frame.transaction_time.setStyleSheet(
            'color:#959BAE;font-weight: 400; font-size:14px',
        )


def setup_on_chain_icon(
    frame,
    network_value: str,
    bitcoin_img_path: dict,
) -> QIcon:
    """Setup on-chain icon for transaction frame.

    Args:
        frame: The transaction detail frame.
        network_value: The network value string.
        bitcoin_img_path: Dict mapping network to image path.

    Returns:
        The configured QIcon.
    """
    on_chain_icon = QIcon()
    img_path = bitcoin_img_path.get(network_value)
    if img_path:
        on_chain_icon.addFile(
            img_path,
            QSize(), QIcon.Normal, QIcon.Off,
        )
        frame.transfer_type.setIcon(on_chain_icon)
        frame.transfer_type.setIconSize(QSize(18, 18))
        frame.transfer_type.setToolTip(
            QCoreApplication.translate(
                IRIS_WALLET_TRANSLATIONS_CONTEXT, 'on_chain', None,
            ),
        )
    return on_chain_icon


def handle_transaction_type_display(
    frame,
    transfer_status: str,
    transaction_type,
) -> None:
    """Handle display of transaction type vs transfer type.

    Args:
        frame: The transaction detail frame.
        transfer_status: The transfer status string.
        transaction_type: The transaction type object.
    """
    if transfer_status == TransferStatusEnumModel.INFLATION.value:
        frame.transaction_type.setText('INFLATION')
        frame.transaction_amount.setStyleSheet(
            'color:#01A781;font-weight: 600',
        )
        frame.transaction_type.show()
        frame.transfer_type.hide()
    elif transfer_status == TransferStatusEnumModel.INTERNAL.value:
        if transaction_type == TransferKind.ISSUANCE:
            frame.transaction_type.setText('ISSUANCE')
            frame.transaction_amount.setStyleSheet(
                'color:#01A781;font-weight: 600',
            )
            frame.transaction_type.show()
            frame.transfer_type.hide()
        else:
            frame.transfer_type.show()
            frame.transaction_type.hide()
    else:
        frame.transfer_type.show()
        frame.transaction_type.hide()
