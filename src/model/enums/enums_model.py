"""
This module defines enumeration models for different models.
"""
from __future__ import annotations

from enum import Enum


class NetworkEnumModel(str, Enum):
    """Enum model for network"""
    REGTEST = 'regtest'
    MAINNET = 'mainnet'
    TESTNET = 'testnet'


class TransactionStatusEnumModel(str, Enum):
    """Enum model for transaction status"""
    WAITING_CONFIRMATIONS = 'WaitingConfirmations'
    WAITING_COUNTERPARTY = 'WaitingCounterparty'
    SETTLED = 'Settled'
    CONFIRMED = 'CONFIRMED'
    FAILED = 'Failed'


class TransferStatusEnumModel(str, Enum):
    """"Enum model for transfer status"""
    ON_GOING_TRANSFER = 'Ongoing transfer'
    SENT = 'SENT'
    RECEIVED = 'RECEIVED'
    INTERNAL = 'INTERNAL'
    SEND = 'send'
    RECEIVE = 'receive'
    SEND_BTC = 'send_btc'
    RECEIVE_BTC = 'receive_btc'


class AssetTransferStatusEnumModel(str, Enum):
    """Transder status for asset transaction"""
    ISSUANCE = 'Issuance'
    RECEIVE_BLIND = 'ReceiveBlind'
    RECEIVE_WITNESS = 'ReceiveWitness'
    SEND = 'Send'


class NativeAuthType(str, Enum):
    """Enum for authentication type for native"""
    LOGGING_TO_APP = 'LOGGING_TO_APP'
    # operation like issue rgb20 or rgb25  and transactions
    MAJOR_OPERATION = 'MAJOR_OPERATION'


class AssetType(str, Enum):
    """Enum for asset type"""
    RGB20 = 'RGB20'
    RGB25 = 'RGB25'
    BITCOIN = 'BITCOIN'


class TransferType(str, Enum):
    """Enum for transfer type"""
    CREATEUTXOS = 'CreateUtxos'
    ISSUANCE = 'Issuance'
    ON_CHAIN = 'On chain'


class TokenSymbol(str, Enum):
    """Enum for token symbol"""
    BITCOIN = 'BTC'
    TESTNET_BITCOIN = 'tBTC'
    REGTEST_BITCOIN = 'rBTC'
    SAT = 'SAT'


class LoaderDisplayModel(str, Enum):
    """Enum for loader display modes."""
    FULL_SCREEN = 'full_screen'
    TOP_OF_SCREEN = 'top_of_screen'


class ToastPreset(Enum):
    """Enum for toast preset"""
    SUCCESS = 1
    WARNING = 2
    ERROR = 3
    INFORMATION = 4
