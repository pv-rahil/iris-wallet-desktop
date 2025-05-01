"""This module contains the ReceiveBitcoinViewModel class, which represents the view model
for the Receive bitcoin page page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.repository.btc_repository import BtcRepository
from src.model.btc_model import AddressResponseModel
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.worker import ThreadManager


class ReceiveBitcoinViewModel(QObject, ThreadManager):
    """This class represents the activities of the Receive bitcoin page."""
    address = Signal(str)
    is_loading = Signal(bool)
    error = Signal(str)

    def __init__(self, page_navigation) -> None:
        super().__init__()
        self._page_navigation = page_navigation

    def get_bitcoin_address(self, is_hard_refresh=False):
        """This method is used to retrieve bitcoin address."""
        if is_hard_refresh:
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
        self.is_loading.emit(True)
        self.run_in_thread(
            BtcRepository.get_address,
            {
                'callback': self.on_success,
                'error_callback': self.on_error,
            },
        )

    def on_success(self, response: AddressResponseModel):
        """This method handled onsuccess logic"""
        self.address.emit(response.address)
        self.is_loading.emit(False)

    def on_error(self, error: CommonException):
        """This method handled on_error logic"""
        print(error)
        self.error.emit(error.message)
        self.is_loading.emit(False)
