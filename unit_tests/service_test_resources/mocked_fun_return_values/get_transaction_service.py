"""Mocked data for the bitcoin page service service test"""
from __future__ import annotations

from rgb_lib import Balance
from rgb_lib import BlockTime
from rgb_lib import TransactionType

from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import Transaction
from src.model.btc_model import TransactionListResponse
from src.model.btc_model import TransactionListWithBalanceResponse

mock_data_transaction_type_user_send = Transaction(
    transaction_type=TransactionType.USER,
    txid='e28d416c3345e3558516830b7adfbc147f3f7563c9268e24f36d233048e6f9f2',
    received=99998405,
    sent=100000000,
    fee=595,
    confirmation_time=BlockTime(height=105, timestamp=1717006775),
)
mock_data_transaction_type_user_receive = Transaction(
    transaction_type=TransactionType.USER,
    txid='354ab4d3afbac320ea492086ad7590570455d625acd59aea799c58f83afc9f8f',
    received=100000000,
    sent=0,
    fee=2820,
    confirmation_time=BlockTime(height=104, timestamp=1717006478),
)
mock_data_transaction_type_createutxo = Transaction(
    transaction_type=TransactionType.CREATE_UTXOS,
    txid='673c88d7e435e6fe795bf30fd0363790a68c3a8dfd91f71b050170978c9413ea',
    received=199996291,
    sent=199998405,
    fee=2114,
    confirmation_time=BlockTime(height=106, timestamp=1717006902),
)
mock_data_transaction_unconfirm_type_user_send = Transaction(
    transaction_type=TransactionType.USER,
    txid='e28d416c3345e3558516830b7adfbc147f3f7563c9268e24f36d233048e6f9f2',
    received=99998405,
    sent=100000000,
    fee=595,
    confirmation_time=None,
)
mock_data_transaction_unconfirm_type_createutxos = Transaction(
    transaction_type=TransactionType.CREATE_UTXOS,
    txid='673c88d7e435e6fe795bf30fd0363790a68c3a8dfd91f71b050170978c9413ea',
    received=199996291,
    sent=199998405,
    fee=2114,
    confirmation_time=None,
)
mock_data_transaction_unconfirm_type_user_receive = Transaction(
    transaction_type=TransactionType.USER,
    txid='fb90ee1b9495be737595919f766b939c130dbc2f359b4e8ec21ead6358462a67',
    received=100000000,
    sent=0,
    fee=2820,
    confirmation_time=None,
)

mock_data_transaction_type_unknown = Transaction(
    transaction_type=TransactionType.DRAIN,
    txid='fb90ee1b9495be737595919f766b939c130dbc2f359b4e8ec21ead6358462a67',
    received=100000000,
    sent=0,
    fee=2820,
    confirmation_time=None,
)

mock_data_list_transaction_all = TransactionListResponse(
    transactions=[
        mock_data_transaction_type_user_send,
        mock_data_transaction_type_user_receive,
        mock_data_transaction_type_createutxo,
        mock_data_transaction_unconfirm_type_user_send,
        mock_data_transaction_unconfirm_type_createutxos,
        mock_data_transaction_unconfirm_type_user_receive,
    ],
)
mocked_data_balance = BalanceResponseModel(
    vanilla=Balance(
        settled=0, future=90332590, spendable=90332590,
    ), colored=Balance(settled=0, future=0, spendable=0),
)
mock_data_list_transaction_empty = TransactionListWithBalanceResponse(
    transactions=[], balance=mocked_data_balance,
)
mock_data_expected_list_transaction_all = TransactionListWithBalanceResponse(
    transactions=[
        Transaction(
            transaction_type=TransactionType.USER,
            txid='e28d416c3345e3558516830b7adfbc147f3f7563c9268e24f36d233048e6f9f2',
            received=99998405,
            sent=100000000,
            fee=595,
            confirmation_time=None,
        ),
        Transaction(
            transaction_type=TransactionType.CREATE_UTXOS,
            txid='673c88d7e435e6fe795bf30fd0363790a68c3a8dfd91f71b050170978c9413ea',
            received=199996291,
            sent=199998405,
            fee=2114,
            confirmation_time=None,
        ),
        Transaction(
            transaction_type=TransactionType.USER,
            txid='fb90ee1b9495be737595919f766b939c130dbc2f359b4e8ec21ead6358462a67',
            received=100000000,
            sent=0,
            fee=2820,
            confirmation_time=None,
        ),
        Transaction(
            transaction_type=TransactionType.CREATE_UTXOS,
            txid='673c88d7e435e6fe795bf30fd0363790a68c3a8dfd91f71b050170978c9413ea',
            received=199996291,
            sent=199998405,
            fee=2114,
            confirmation_time=BlockTime(
                height=106,
                timestamp=1717006902,
            ),
        ),
        Transaction(
            transaction_type=TransactionType.USER,
            txid='e28d416c3345e3558516830b7adfbc147f3f7563c9268e24f36d233048e6f9f2',
            received=99998405,
            sent=100000000,
            fee=595,
            confirmation_time=BlockTime(
                height=105,
                timestamp=1717006775,
            ),
        ),
        Transaction(
            transaction_type=TransactionType.USER,
            txid='354ab4d3afbac320ea492086ad7590570455d625acd59aea799c58f83afc9f8f',
            received=100000000,
            sent=0,
            fee=2820,
            confirmation_time=BlockTime(
                height=104,
                timestamp=1717006478,
            ),
        ),
    ],
    balance=BalanceResponseModel(
        vanilla=Balance(
            settled=0, future=90332590, spendable=90332590,
        ), colored=Balance(settled=0, future=0, spendable=0),
    ),
)
