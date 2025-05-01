"""This module contains the UnspentListViewModel class, which represents the view model
for the unspent list page activities.
"""
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from rgb_lib import Unspent

from src.data.repository.btc_repository import BtcRepository
from src.model.btc_model import UnspentListRequestModel
from src.model.btc_model import UnspentsListResponseModel
from src.utils.cache import Cache
from src.utils.custom_exception import CommonException
from src.utils.worker import ThreadManager
from src.views.components.toast import ToastManager


class UnspentListViewModel(QObject, ThreadManager):
    """This class represents the activities of the channel management page."""
    list_loaded = Signal(bool)
    unspent_list: list[Unspent]
    loading_started = Signal(bool)
    loading_finished = Signal(bool)

    def __init__(self, page_navigation):
        super().__init__()
        self._page_navigation = page_navigation
        self.unspent_list = []

    def get_unspent_list(self, is_hard_refresh=False):
        """This method retrieves unspent transactions for the unspent list page."""
        if is_hard_refresh:
            cache = Cache.get_cache_session()
            if cache is not None:
                cache.invalidate_cache()
        self.loading_started.emit(True)

        def success(response: UnspentsListResponseModel, is_data_ready=True):
            """This method handles success."""
            if response is not None:
                self.unspent_list = [
                    unspent for unspent in response.unspents if unspent is not None
                ]
                self.list_loaded.emit(True)
                if is_data_ready:
                    self.loading_finished.emit(False)

        def error(err: CommonException):
            """This method handles error."""
            self.loading_finished.emit(True)
            print(err)
            ToastManager.error(
                description=err.message,
            )

        try:
            self.run_in_thread(
                BtcRepository.list_unspents,
                {
                    'args': [UnspentListRequestModel(settled_only=False, skip_sync=False)],
                    'key': 'unspentlistviewmodel_get_unspent_list',
                    'use_cache': True,
                    'callback': success,
                    'error_callback': error,
                },
            )
        except Exception as e:
            self.loading_finished.emit(True)
            ToastManager.error(
                description=f"An unexpected error occurred: {str(e)}",
            )
