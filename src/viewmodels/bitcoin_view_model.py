# mypy: ignore-errors
"""This module contains the BitcoinViewModel class, which represents the view model
for the Bitcoin page activities.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from src.data.service.bitcoin_page_service import BitcoinPageService
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListWithBalanceResponse
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.error_message import ERROR_FAILED_TO_GET_BALANCE
from src.utils.error_message import ERROR_NAVIGATION_BITCOIN_PAGE
from src.utils.error_message import ERROR_NAVIGATION_RECEIVE_BITCOIN_PAGE
from src.utils.error_message import ERROR_TITLE
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class BitcoinViewModel(QObject, ThreadManager):
    """This class represents the activities of the bitcoin page."""
    loading_started = Signal(bool)
    loading_finished = Signal(bool)
    error = Signal(str)
    transaction_loaded = Signal()

    def __init__(self, page_navigation: Any) -> None:
        super().__init__()
        self._page_navigation = page_navigation
        self.transaction: list[Transaction] = []
        self.spendable_bitcoin_balance_with_suffix: str = '0'
        self.total_bitcoin_balance_with_suffix: str = '0'

    def get_transaction_list(self, bitcoin_txn_hard_refresh=False):
        """This method is used to retrieve bitcoin transaction history in thread."""
        if bitcoin_txn_hard_refresh:
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
        self.loading_started.emit(True)

        def on_success(response: TransactionListWithBalanceResponse, is_data_ready=True):
            """This method is used  handle onsuccess for the bitcoin page."""
            spendable_balance = str(response.balance.vanilla.spendable)
            bitcoin_balance_with_suffix = spendable_balance + ' SATS'
            total_balance = str(response.balance.vanilla.future)
            self.total_bitcoin_balance_with_suffix = total_balance + ' SATS'
            self.spendable_bitcoin_balance_with_suffix = bitcoin_balance_with_suffix
            self.transaction = response.transactions
            self.transaction_loaded.emit()
            if is_data_ready:
                self.loading_finished.emit(False)

        def on_error(error: CommonException):
            """This method is used  handle onerror for the bitcoin page."""
            self.loading_finished.emit(False)
            self.error.emit(error.message)
            ToastManager.error(
                parent=None, title=ERROR_TITLE,
                description=ERROR_FAILED_TO_GET_BALANCE.format(error.message),
            )

        self.run_in_thread(
            BitcoinPageService.get_btc_transaction,
            {
                'key': 'bitcoinviewmodel_get_transaction_list',
                'use_cache': True,
                'callback': on_success,
                'error_callback': on_error,
            },
        )

    def on_send_bitcoin_click(self) -> None:
        """This method is used to navigate to the send bitcoin page."""
        try:
            self._page_navigation.send_bitcoin_page()
        except CommonException as error:
            ToastManager.error(
                parent=None, title=ERROR_TITLE,
                description=ERROR_NAVIGATION_BITCOIN_PAGE.format(
                    error.message,
                ),
            )

    def on_hard_refresh(self):
        """Remove cached data when user perform hard refresh"""
        try:
            self.get_transaction_list(bitcoin_txn_hard_refresh=True)
        except CommonException as error:
            ToastManager.error(
                description=error.message,
            )

    def on_receive_bitcoin_click(self) -> None:
        """This method is used to navigate to the receive bitcoin page."""
        try:
            self._page_navigation.receive_bitcoin_page()
        except CommonException as error:
            ToastManager.error(
                parent=None, title=ERROR_TITLE,
                description=ERROR_NAVIGATION_RECEIVE_BITCOIN_PAGE.format(
                    error.message,
                ),
            )
