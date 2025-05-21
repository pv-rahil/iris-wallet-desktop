"""This module contains constant variables.
"""
from __future__ import annotations

from src.model.enums.enums_model import NetworkEnumModel

DEFAULT_LOCALE = 'en_IN'
BACKED_URL_LIGHTNING_NETWORK = 'http://127.0.0.1:3001'
ORGANIZATION_NAME = 'rgb'
APP_NAME = 'iris-wallet-vault'
ORGANIZATION_DOMAIN = 'com.rgb.iriswalletvault'
LOG_FILE_MAX_SIZE = 1048576  # 1 mb
LOG_FILE_MAX_BACKUP_COUNT = 5
MNEMONIC_KEY = 'mnemonic'
ACCOUNT_XPUB = 'account_xpub'
WALLET_PASSWORD_KEY = 'wallet_password'
SAVED_INDEXER_URL = 'indexer_url'
SAVED_PROXY_ENDPOINT = 'proxy_endpoint'
NETWORK_KET = 'network'
CACHE_FILE_NAME = {
    NetworkEnumModel.MAINNET: 'iris-wallet-cache-mainnet',
    NetworkEnumModel.TESTNET: 'iris-wallet-cache-testnet',
    NetworkEnumModel.REGTEST: 'iris-wallet-cache-regtest',
}
DEFAULT_CACHE_FILENAME = 'iris-wallet-cache-default'
CACHE_FOLDER_NAME = 'cache'
CACHE_EXPIRE_TIMEOUT = 600
REQUEST_TIMEOUT = 120  # In seconds
NO_OF_UTXO = 1
MIN_CONFIRMATION = 1
UTXO_SIZE_SAT = 1000
MIN_UTXOS_SIZE = 1000
MIN_CAPACITY_SATS = 5506
FEE_RATE_FOR_CREATE_UTXOS = 5
RGB_INVOICE_DURATION_SECONDS = 86400
MAX_ALLOCATIONS_PER_UTXO = 1
MAX_ISSUE_AMOUNT = 18446744073709551615
INTERVAL = 2
MAX_RETRY_REFRESH_API = 3
FEE_RATE = 5
MAX_ASSET_FILE_SIZE = 5  # In mb
G_SCOPES = ['https://www.googleapis.com/auth/drive.file']
NATIVE_LOGIN_ENABLED = 'nativeLoginEnabled'
IS_NATIVE_AUTHENTICATION_ENABLED = 'isNativeAuthenticationEnabled'
PRIVACY_POLICY_URL = 'https://iriswallet.com/privacy_policy.html'
TERMS_OF_SERVICE_URL = 'https://iriswallet.com/testnet/terms_of_service.html'
LOG_FOLDER_NAME = 'logs'
PING_DNS_ADDRESS_FOR_NETWORK_CHECK = '8.8.8.8'
PING_DNS_SERVER_CALL_INTERVAL = 5000

INDEXER_URL_REGTEST = 'electrum.rgbtools.org:50041'
PROXY_ENDPOINT_REGTEST = 'rpcs://proxy.iriswallet.com/0.2/json-rpc'

INDEXER_URL_TESTNET = 'ssl://electrum.iriswallet.com:50013'
PROXY_ENDPOINT_TESTNET = 'rpcs://proxy.iriswallet.com/0.2/json-rpc'

INDEXER_URL_MAINNET = 'http://127.0.0.1:50003'
PROXY_ENDPOINT_MAINNET = 'http://127.0.0.1:3002/json-rpc'

# Block values for fee estimation
SLOW_TRANSACTION_FEE_BLOCKS = 17
MEDIUM_TRANSACTION_FEE_BLOCKS = 7
FAST_TRANSACTION_FEE_BLOCKS = 1

# Faucet urls
rgbRegtestFaucetURLs: list[str] = ['http://127.0.0.1:8081']
rgbTestnetFaucetURLs: list[str] = [
    'https://rgb-faucet.iriswallet.com/testnet-planb2023',
    'https://rgb-faucet.iriswallet.com/testnet-random2023',
]
rgbMainnetFaucetURLs: list[str] = [
    'https://rgb-faucet.iriswallet.com/mainnet-random2023',
]

# Faucet api keys
API_KEY_OPERATOR = 'defaultoperatorapikey'
API_KEY = 'defaultapikey'

# Bitcoin explorer url
BITCOIN_EXPLORER_URL = 'https://mempool.space'

# Syncing chain info label timer in milliseconds
SYNCING_CHAIN_LABEL_TIMER = 5000

# Email and github issue url for error report
CONTACT_EMAIL = 'iriswalletdesktop@gmail.com'
GITHUB_ISSUE_LINK = 'https://github.com/RGB-Tools/iris-wallet-vault/issues/new/choose'

# Translation context key
IRIS_WALLET_TRANSLATIONS_CONTEXT = 'iris_wallet_vault'

# Rgb lib commit ID
RGB_LIB_VERSION_KEY = 'rgb_lib_version'
CURRENT_RGB_LIB_VERSION = '0.3.0a12'
COMPATIBLE_RGB_LIB_VERSION = [
    '0.3.0a12',
]

# Directory names used in paths
APP_DIR = 'app'
