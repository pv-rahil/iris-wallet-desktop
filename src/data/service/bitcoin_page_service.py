# pylint: disable=too-few-public-methods,too-many-statements
"""
This module provides the service for bitcoin page.
"""
from __future__ import annotations

from datetime import datetime

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.setting_repository import SettingRepository
from src.data.service.helpers.bitcoin_page_helper import calculate_transaction_amount
from src.data.service.helpers.bitcoin_page_helper import get_transaction_status
from src.data.service.wallet_data_service import WalletDataService
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse
from src.model.enums.enums_model import TransactionStatusEnumModel
from src.model.enums.enums_model import TransferStatusEnumModel
from src.model.enums.enums_model import WalletType
from src.utils.custom_exception import ServiceOperationException
from src.utils.handle_exception import handle_exceptions


class BitcoinPageService:
    """
    Service class for bitcoin page data.
    """
    @staticmethod
    def get_btc_transaction() -> TransactionListWithBalanceResponse:
        """Gives transaction list for on-chain transactions"""
        try:
            # For transaction status
            transfer_status: TransferStatusEnumModel | None = None
            transaction_status: TransactionStatusEnumModel | None = None
            bitcoin_balance: BalanceResponseModel | None = None
            transaction_list: TransactionListResponse | None = None
            bitcoin_balance, transaction_list = BitcoinPageService._fetch_balance_and_transactions()
            if not transaction_list or not transaction_list.transactions:
                return TransactionListWithBalanceResponse(transactions=[], balance=bitcoin_balance)

            # Separate transactions with and without confirmation times
            confirm_transactions_list: list[Transaction] = []
            unconfirm_transaction_list: list[Transaction] = []

            for transaction in transaction_list.transactions:
                if transaction is None:
                    continue

                # Use helper to calculate amount
                amount: str | None = calculate_transaction_amount(
                    transaction=transaction,
                )
                if amount is None:
                    raise ServiceOperationException(
                        f'Unable to calculate amount {amount}',
                    ) from None
                transaction.amount = amount

                # Getting transaction status
                transfer_status, transaction_status = get_transaction_status(
                    transaction,
                )
                if transfer_status is None or transaction_status is None:
                    raise ServiceOperationException(
                        'Unable to get transaction status',
                    ) from None
                transaction.transfer_status = transfer_status
                transaction.transaction_status = transaction_status

                if transaction.confirmation_time is not None:
                    try:
                        # Extract the timestamp from the ConfirmationTime object
                        if transaction.confirmation_time.timestamp is None:
                            raise ServiceOperationException(
                                'Confirmation time is missing a timestamp',
                            )

                        timestamp = transaction.confirmation_time.timestamp

                        # Convert the timestamp to a datetime object
                        dt_object = datetime.fromtimestamp(timestamp)

                        # Format the datetime object to the desired format
                        date_str = dt_object.strftime('%Y-%m-%d')
                        time_str = dt_object.strftime('%H:%M:%S')

                        # Assign the formatted date and time to the transaction attributes
                        transaction.confirmation_normal_time = time_str
                        transaction.confirmation_date = date_str

                    except AttributeError as exc:
                        raise ServiceOperationException(
                            f'AttributeError: {exc}',
                        ) from exc
                    except Exception as exc:
                        raise ServiceOperationException(
                            f'An error occurred: {exc}',
                        ) from exc

                if transaction.confirmation_time:
                    confirm_transactions_list.append(transaction)
                else:
                    unconfirm_transaction_list.append(transaction)

            # Sort transactions with confirmation times by timestamp in reverse order
            confirm_transactions_list.sort(
                key=lambda t: t.confirmation_time.timestamp if t.confirmation_time else 0,
                reverse=True,
            )

            # Combine both lists, prioritizing transactions without confirmation times
            sorted_transactions: TransactionListResponse = TransactionListResponse(
                transactions=unconfirm_transaction_list + confirm_transactions_list,
            )
            return TransactionListWithBalanceResponse(transactions=sorted_transactions.transactions, balance=bitcoin_balance)
        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def _fetch_balance_and_transactions() -> tuple[BalanceResponseModel, TransactionListResponse]:
        """Fetch balance and transactions depending on wallet type."""
        if SettingRepository.get_wallet_type() == WalletType.OFFLINE_TYPE_WALLET:
            wallet_service = WalletDataService.get_session()
            if wallet_service is None:
                return BalanceResponseModel(balance=0), TransactionListResponse(transactions=[])
            return (
                wallet_service.get_btc_balance(),
                wallet_service.list_transactions(),
            )
        return (
            BtcRepository.get_btc_balance(),
            BtcRepository.list_transactions(),
        )
