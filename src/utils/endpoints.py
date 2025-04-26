"""
This module defines the endpoints for API
"""
# Channels
from __future__ import annotations

CLOSE_CHANNEL_ENDPOINT = '/closechannel'
LIST_CHANNELS_ENDPOINT = '/listchannels'
OPEN_CHANNEL_ENDPOINT = '/openchannel'

# Peers
CONNECT_PEER_ENDPOINT = '/connectpeer'
DISCONNECT_PEER_ENDPOINT = '/disconnectpeer'
LIST_PEERS_ENDPOINT = '/listpeers'

# Payments
KEY_SEND_ENDPOINT = '/keysend'
LIST_PAYMENTS_ENDPOINT = '/listpayments'
SEND_PAYMENT_ENDPOINT = '/sendpayment'

# Invoice
DECODE_LN_INVOICE_ENDPOINT = '/decodelninvoice'
INVOICE_STATUS_ENDPOINT = '/invoicestatus'
LN_INVOICE_ENDPOINT = '/lninvoice'

# On-chain
ADDRESS_ENDPOINT = '/address'
BTC_BALANCE_ENDPOINT = '/btcbalance'
LIST_TRANSACTIONS_ENDPOINT = '/listtransactions'
LIST_UNSPENT_ENDPOINT = '/listunspents'
SEND_BTC_ENDPOINT = '/sendbtc'
ESTIMATE_FEE_ENDPOINT = '/estimatefee'

# RGB
ASSET_BALANCE_ENDPOINT = '/assetbalance'
CREATE_UTXO_ENDPOINT = '/createutxos'
DECODE_RGB_INVOICE_ENDPOINT = '/decodergbinvoice'
FAIL_TRANSFER_ENDPOINT = '/failtransfers'
ISSUE_ASSET_ENDPOINT_NIA = '/issueassetnia'
ISSUE_ASSET_ENDPOINT_CFA = '/issueassetcfa'
ISSUE_ASSET_ENDPOINT_UDA = '/issueassetuda'
LIST_ASSETS_ENDPOINT = '/listassets'
LIST_TRANSFERS_ENDPOINT = '/listtransfers'
REFRESH_TRANSFERS_ENDPOINT = '/refreshtransfers'
RGB_INVOICE_ENDPOINT = '/rgbinvoice'
SEND_ASSET_ENDPOINT = '/sendasset'
GET_ASSET_MEDIA = '/getassetmedia'
POST_ASSET_MEDIA = '/postassetmedia'

# Swaps
LIST_TRADES_ENDPOINT = '/listtrades'
MAKER_EXECUTE_ENDPOINT = '/makerexecute'
MAKER_INIT_ENDPOINT = '/makerinit'
TAKER_ENDPOINT = '/taker'

# Other
BACKUP_ENDPOINT = '/backup'
CHANGE_PASSWORD_ENDPOINT = '/changepassword'
CHECK_INDEXER_URL_ENDPOINT = '/checkindexerurl'
CHECK_PROXY_ENDPOINT = '/checkproxyendpoint'
INIT_ENDPOINT = '/init'
LOCK_ENDPOINT = '/lock'
NETWORK_INFO_ENDPOINT = '/networkinfo'
NODE_INFO_ENDPOINT = '/nodeinfo'
RESTORE_ENDPOINT = '/restore'
SEND_ONION_MESSAGE_ENDPOINT = '/sendonionmessage'
SHUTDOWN_ENDPOINT = '/shutdown'
SIGN_MESSAGE_ENDPOINT = '/signmessage'
UNLOCK_ENDPOINT = '/unlock'

# Faucet
LIST_FAUCET_ASSETS = '/control/assets'
WALLET_CONFIG = '/receive/config'
REQUEST_FAUCET_ASSET = '/receive/asset'

ENDPOINTS_TO_CACHE: list[str] = [
    BTC_BALANCE_ENDPOINT,
    LIST_TRANSACTIONS_ENDPOINT,
    LIST_UNSPENT_ENDPOINT,
]
