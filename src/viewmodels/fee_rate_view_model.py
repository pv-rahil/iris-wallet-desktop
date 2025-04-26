"""
This module contains the EstimateFeeViewModel class, which represents the view model for the estimate fee activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.utils.common_utils import TRANSACTION_SPEEDS
from src.utils.error_message import ERROR_SOMETHING_WENT_WRONG
from src.utils.info_message import INFO_CUSTOM_FEE_RATE
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class EstimateFeeViewModel(QObject, ThreadManager):
    """This class is responsible for getting the estimated fee for the desired transaction speed."""
    loading_status = Signal(bool, bool)
    fee_estimation_success = Signal(float)
    fee_estimation_error = Signal()

    def __init__(self):
        super().__init__()
        self.blocks = 0

    def get_fee_rate(self, tx_speed: str) -> None:
        """
        Estimates the transaction fee based on the selected speed (slow, medium, fast).

        Args:
            tx_speed (str): The transaction speed selected by the user.
        """
        self.blocks = TRANSACTION_SPEEDS.get(tx_speed, 0)

        if self.blocks == 0:
            ToastManager.info(
                description='Invalid transaction speed selected.',
            )
            return

        self.loading_status.emit(True, True)

        try:
            self.run_in_thread(
                BtcRepository.estimate_fee,
                {
                    'args': [EstimateFeeRequestModel(blocks=self.blocks)],
                    'callback': self.on_success_fee_estimation,
                    'error_callback': self.on_estimate_fee_error,
                },
            )
        except ConnectionError:
            self.loading_status.emit(False, True)
            ToastManager.info(
                description='Network error. Please check your connection.',
            )

        except Exception as e:
            self.loading_status.emit(False, True)
            ToastManager.info(
                description=f"An unexpected error occurred: {str(e)}",
            )

    def on_success_fee_estimation(self, response: EstimateFeeResponse) -> None:
        """Handles successful fee estimation."""
        self.loading_status.emit(False, True)
        self.fee_estimation_success.emit(response.fee_rate)

    def on_estimate_fee_error(self) -> None:
        """Handles errors during fee estimation."""
        self.loading_status.emit(False, True)
        self.fee_estimation_error.emit()
        ToastManager.info(
            description=INFO_CUSTOM_FEE_RATE.format(
                ERROR_SOMETHING_WENT_WRONG,
            ),
        )
