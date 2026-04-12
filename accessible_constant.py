"""Accessible name and description constants"""
# Application name
from __future__ import annotations

from src.utils.constant import APP_NAME

APP1_NAME = 'test_app_1'
APP2_NAME = 'test_app_2'
APP3_NAME = 'test_app_3'
APP4_NAME = 'test_app_4'
FIRST_SERVICE = f"{APP_NAME}_{APP1_NAME}"
SECOND_SERVICE = f"{APP_NAME}_{APP2_NAME}"
THIRD_SERVICE = f"{APP_NAME}_{APP3_NAME}"
FOURTH_SERVICE = f"{APP_NAME}_{APP4_NAME}"
FIRST_APPLICATION = f"Iris Wallet Regtest {APP1_NAME}"
SECOND_APPLICATION = f"Iris Wallet Regtest {APP2_NAME}"
THIRD_APPLICATION = f"Iris Wallet Regtest {APP3_NAME}"
FOURTH_APPLICATION = f"Iris Wallet Regtest {APP4_NAME}"
FIRST_APPLICATION_PATH = f"{APP_NAME}_{APP1_NAME}"
SECOND_APPLICATION_PATH = f"{APP_NAME}_{APP2_NAME}"
THIRD_APPLICATION_PATH = f"{APP_NAME}_{APP3_NAME}"
FOURTH_APPLICATION_PATH = f"{APP_NAME}_{APP4_NAME}"
RGB_LEDGER_APP_NAME = 'rgb_ledger_app'
LEDGER_EMULATOR_APP_NAME = 'Ledger Nano SP Emulator'
HARDWARE_WALLET_VARIANTS = [
    'online_create_hardware',
    'offline_create_hardware', 'online_load_hardware', 'offline_load_hardware',
]

REQUIRE_USB_VARIANTS = [
    'offline_create_hardware', 'offline_create_on_device',
    'online_watch_only', 'offline_load_on_device', 'offline_load_hardware',
    'offline_multisig_on_device', 'offline_multisig_hardware',
    'offline_multisig_load_on_device', 'offline_multisig_load_hardware',
    'online_multisig_watch_only',
]
LOAD_WALLET_VARIANT = [
    'offline_load_hardware', 'offline_load_on_device',
    'online_load_hardware', 'online_load_on_device',
    'online_multisig_load_on_device', 'online_multisig_load_hardware',
    'offline_multisig_load_on_device', 'offline_multisig_load_hardware',
]
FAKEUSB_MOUNT_PATH = '/tmp/fakeusb_mount'


# Wallet variant names (centralized)
ONLINE_WATCH_ONLY = 'online_watch_only'
ONLINE_CREATE_ON_DEVICE = 'online_create_on_device'
ONLINE_CREATE_HARDWARE = 'online_create_hardware'
ONLINE_LOAD_ON_DEVICE = 'online_load_on_device'
ONLINE_LOAD_HARDWARE = 'online_load_hardware'

OFFLINE_CREATE_ON_DEVICE = 'offline_create_on_device'
OFFLINE_CREATE_HARDWARE = 'offline_create_hardware'
OFFLINE_LOAD_ON_DEVICE = 'offline_load_on_device'
OFFLINE_LOAD_HARDWARE = 'offline_load_hardware'

# Multisig wallet variants - Create
ONLINE_MULTISIG_ON_DEVICE = 'online_multisig_on_device'
ONLINE_MULTISIG_HARDWARE = 'online_multisig_hardware'
ONLINE_MULTISIG_WATCH_ONLY = 'online_multisig_watch_only'
OFFLINE_MULTISIG_ON_DEVICE = 'offline_multisig_on_device'
OFFLINE_MULTISIG_HARDWARE = 'offline_multisig_hardware'
OFFLINE_MULTISIG_WATCH_ONLY = 'offline_multisig_watch_only'

# Multisig wallet variants - Load
ONLINE_MULTISIG_LOAD_ON_DEVICE = 'online_multisig_load_on_device'
ONLINE_MULTISIG_LOAD_HARDWARE = 'online_multisig_load_hardware'
OFFLINE_MULTISIG_LOAD_ON_DEVICE = 'offline_multisig_load_on_device'
OFFLINE_MULTISIG_LOAD_HARDWARE = 'offline_multisig_load_hardware'
OFFLINE_MULTISIG_LOAD_WATCH_ONLY = 'offline_multisig_load_watch_only'

# Multisig create variants grouping
MULTISIG_CREATE_VARIANTS = [
    ONLINE_MULTISIG_ON_DEVICE,
    ONLINE_MULTISIG_HARDWARE,
    ONLINE_MULTISIG_WATCH_ONLY,
    OFFLINE_MULTISIG_ON_DEVICE,
    OFFLINE_MULTISIG_HARDWARE,
    OFFLINE_MULTISIG_WATCH_ONLY,
]

# Multisig load variants grouping
MULTISIG_LOAD_VARIANTS = [
    ONLINE_MULTISIG_LOAD_ON_DEVICE,
    ONLINE_MULTISIG_LOAD_HARDWARE,
    OFFLINE_MULTISIG_LOAD_ON_DEVICE,
    OFFLINE_MULTISIG_LOAD_HARDWARE,
    OFFLINE_MULTISIG_LOAD_WATCH_ONLY,
]

# All multisig variants
MULTISIG_VARIANTS = MULTISIG_CREATE_VARIANTS + MULTISIG_LOAD_VARIANTS

# Multisig hardware variants
MULTISIG_HARDWARE_VARIANTS = [
    ONLINE_MULTISIG_HARDWARE,
    OFFLINE_MULTISIG_HARDWARE,
    ONLINE_MULTISIG_LOAD_HARDWARE,
    OFFLINE_MULTISIG_LOAD_HARDWARE,
]

# Offline multisig hardware variants (require 4 apps)
OFFLINE_MULTISIG_HARDWARE_VARIANTS = [
    OFFLINE_MULTISIG_HARDWARE,
    OFFLINE_MULTISIG_LOAD_HARDWARE,
]

# Single-sig variants grouping
SINGLE_SIG_CREATE_VARIANTS = [
    ONLINE_WATCH_ONLY,
    ONLINE_CREATE_ON_DEVICE,
    ONLINE_CREATE_HARDWARE,
    OFFLINE_CREATE_ON_DEVICE,
    OFFLINE_CREATE_HARDWARE,
]

SINGLE_SIG_LOAD_VARIANTS = [
    ONLINE_LOAD_ON_DEVICE,
    ONLINE_LOAD_HARDWARE,
    OFFLINE_LOAD_ON_DEVICE,
    OFFLINE_LOAD_HARDWARE,
]

SINGLE_SIG_VARIANTS = SINGLE_SIG_CREATE_VARIANTS + SINGLE_SIG_LOAD_VARIANTS

NAME_TO_STEPS: dict[str, tuple[int, int, int, int, int]] = {
    # Online Standard
    ONLINE_WATCH_ONLY: (1, 1, 2, 0, 0),
    ONLINE_CREATE_ON_DEVICE: (1, 1, 1, 1, 1),
    ONLINE_CREATE_HARDWARE: (1, 1, 1, 1, 2),
    ONLINE_LOAD_ON_DEVICE: (1, 1, 1, 2, 1),
    ONLINE_LOAD_HARDWARE: (1, 1, 1, 2, 2),
    # Offline Standard
    OFFLINE_CREATE_ON_DEVICE: (1, 2, 0, 1, 1),
    OFFLINE_CREATE_HARDWARE: (1, 2, 0, 1, 2),
    OFFLINE_LOAD_ON_DEVICE: (1, 2, 0, 2, 1),
    OFFLINE_LOAD_HARDWARE: (1, 2, 0, 2, 0),
    # Online Multisig - Create
    ONLINE_MULTISIG_ON_DEVICE: (2, 1, 1, 1, 1),
    ONLINE_MULTISIG_HARDWARE: (2, 1, 1, 1, 2),
    ONLINE_MULTISIG_WATCH_ONLY: (2, 1, 2, 1, 0),
    # Offline Multisig - Create
    OFFLINE_MULTISIG_ON_DEVICE: (2, 2, 0, 1, 1),
    OFFLINE_MULTISIG_HARDWARE: (2, 2, 0, 1, 2),
    OFFLINE_MULTISIG_WATCH_ONLY: (2, 2, 2, 1, 0),
    # Online Multisig - Load
    ONLINE_MULTISIG_LOAD_ON_DEVICE: (2, 1, 1, 2, 1),
    ONLINE_MULTISIG_LOAD_HARDWARE: (2, 1, 1, 2, 2),
    # Offline Multisig - Load
    OFFLINE_MULTISIG_LOAD_ON_DEVICE: (2, 2, 0, 2, 1),
    OFFLINE_MULTISIG_LOAD_HARDWARE: (2, 2, 0, 2, 2),
    OFFLINE_MULTISIG_LOAD_WATCH_ONLY: (2, 2, 2, 2, 0),
}


# Term and condition page
ACCEPT_BUTTON = 'accept_button'
DECLINE_BUTTON = 'decline_button'
TNC_TXT_DESCRIPTION = 'tnc_txt_description'

# Selection page
OPTION_1_FRAME = 'option_1'
OPTION_2_FRAME = 'option_2'
WALLET_SELECTION_CONTINUE_BUTTON = 'wallet_selection_continue_button'

# Wallet mode summary dialog
WALLET_MODE_SUMMARY_DIALOG = 'wallet_mode_summary_dialog'
WALLET_MODE_SUMMARY_DIALOG_CANCEL_BUTTON = 'wallet_mode_summary_dialog_cancel_button'
WALLET_MODE_SUMMARY_DIALOG_CONTINUE_BUTTON = 'wallet_mode_summary_dialog_continue_button'

# Wallet password page
CREATE_BUTTON = 'create_button'
RESTORE_BUTTON = 'restore_button'
SET_WALLET_PASSWORD_CLOSE_BUTTON = 'set_wallet_password_close_button'
SET_WALLET_PASSWORD_PROCEED_BUTTON = 'set_wallet_password_proceed_button'
PASSWORD_VISIBILITY_BUTTON = 'password_visibility_button'
CONFIRM_PASSWORD_VISIBILITY_BUTTON = 'confirm_password_visibility_button'
PASSWORD_INPUT = 'password_input'
CONFIRM_PASSWORD_INPUT = 'confirm_password_input'
PASSWORD_SUGGESTION_BUTTON = 'password_suggestion_button'

# Bitcoin details page
RECEIVE_BITCOIN_BUTTON = 'receive_bitcoin_button'
SEND_BITCOIN_BUTTON = 'send_bitcoin_button'
BITCOIN_CLOSE_BUTTON = 'bitcoin_close_button'
BITCOIN_BALANCE = 'bitcoin_balance'
BITCOIN_SPENDABLE_BALANCE = 'bitcoin_spendable_balance'
BITCOIN_REFRESH_BUTTON = 'bitcoin_refresh_button'

# Receive asset page
RECEIVER_ADDRESS = 'receiver_address'
RECEIVE_ASSET_CLOSE_BUTTON = 'receive_asset_close_button'
INVOICE_COPY_BUTTON = 'address_copy_button'

# Send asset page
ENTER_RECEIVER_ADDRESS = 'enter_receiver_address'
PAY_AMOUNT = 'pay_amount'
SEND_ASSET_CLOSE_BUTTON = 'send_asset_close_button'
SEND_ASSET_REFRESH_BUTTON = 'send_asset_refresh_button'
SEND_ASSET_BUTTON = 'send_asset_button'
ASSET_ADDRESS_VALIDATION_LABEL = 'asset_address_validation_label'

# Issue NIA asset page
ISSUE_NIA_ASSET = 'issue_nia_asset'
ISSUE_NIA_ASSET_CLOSE_BUTTON = 'issue_nia_asset_close_button'
NIA_ASSET_TICKER = 'nia_asset_ticker'
NIA_ASSET_NAME = 'nia_asset_name'
NIA_ASSET_AMOUNT = 'nia_asset_amount'
ISSUE_NIA_BUTTON = 'issue_nia_button'

# Success page
SUCCESS_PAGE_CLOSE_BUTTON = 'success_page_close_button'
SUCCESS_PAGE_HOME_BUTTON = 'success_page_home_button'

# Toaster
TOASTER_CLOSE_BUTTON = 'toaster_close_button'
TOASTER_DESCRIPTION = 'toaster_description'
TOASTER_TITLE = 'toaster_title'
TOASTER_FRAME = 'toaster_frame'

# Sidebar
BACKUP_BUTTON = 'backup_button'
FUNGIBLE_BUTTON = 'fungible_button'
COLLECTIBLE_BUTTON = 'collectible_button'
INFLATABLE_BUTTON = 'inflatable_button'
ABOUT_BUTTON = 'about_button'
HELP_BUTTON = 'help_button'
FAUCET_BUTTON = 'faucet_button'
SIDEBAR_RECEIVE_ASSET_BUTTON = 'sidebar_receive_asset_button'
VIEW_UNSPENT_LIST_BUTTON = 'view_unspent_list_button'
SETTINGS_BUTTON = 'settings_button'
BROADCAST_TRANSACTION_BUTTON = 'broadcast_transaction_button'
SIGN_PSBT_BUTTON = 'sign_psbt_button'

# Issue CFA asset page
ISSUE_CFA_ASSET = 'issue_cfa_asset'
ISSUE_CFA_BUTTON = 'issue_cfa_button'
CFA_ASSET_DESCRIPTION = 'cfa_asset_description'
CFA_ASSET_NAME = 'cfa_asset_name'
CFA_ASSET_AMOUNT = 'cfa_asset_amount'
CFA_UPLOAD_FILE_BUTTON = 'cfa_upload_file_button'
ISSUE_CFA_ASSET_CLOSE_BUTTON = 'issue_cfa_asset_close_button'

# File chooser
FILE_CHOOSER = 'file chooser'

# Asset details page
ASSET_SEND_BUTTON = 'asset_send_button'
ASSET_REFRESH_BUTTON = 'asset_refresh_button'
ASSET_CLOSE_BUTTON = 'asset_close_button'
ASSET_TOTAL_BALANCE = 'asset_total_balance'
ASSET_SPENDABLE_BALANCE = 'asset_spendable_balance'
ASSET_RECEIVE_BUTTON = 'asset_receive_button'
ASSET_AMOUNT_VALIDATION = 'asset_amount_validation'
ASSET_ID_COPY_BUTTON = 'asset_id_copy_button'
TRANSACTION_DETAIL_CLOSE_BUTTON = 'transaction_detail_close_button'
SECONDARY_ISSUANCE_BUTTON = 'secondary_issuance_button'

# Confirmation dialog page
CONFIRMATION_DIALOG_CONTINUE_BUTTON = 'confirmation_dialog_continue_button'
CONFIRMATION_DIALOG_CANCEL_BUTTON = 'confirmation_dialog_cancel_button'
CONFIRMATION_DIALOG = 'confirmation_dialog'
CONFIRMATION_DIALOG_CHECKBOX = 'confirmation_dialog_checkbox'

# Asset transaction details page
AMOUNT_VALUE = 'amount_value'
ASSET_TRANSACTION_DETAIL_CLOSE_BUTTON = 'asset_transaction_detail_close_button'
ASSET_TX_ID = 'asset_tx_id'

# Fee rate
SLOW_CHECKBOX = 'slow_checkbox'
MEDIUM_CHECKBOX = 'medium_checkbox'
FAST_CHECKBOX = 'fast_checkbox'
CUSTOM_CHECKBOX = 'custom_checkbox'
FEE_RATE_INPUT = 'fee_rate_input'

# Bitcoin tx page
BITCOIN_TX_ID = 'bitcoin_tx_id'
BITCOIN_AMOUNT_VALUE = 'bitcoin_amount_value'
BITCOIN_TX_PAGE_CLOSE_BUTTON = 'bitcoin_tx_page_close_button'

# Transaction detail page
BITCOIN_TRANSACTION_DETAIL_FRAME = 'bitcoin_transaction_detail_frame'
RGB_TRANSACTION_DETAIL_FRAME = 'rgb_transaction_detail_frame'
TRANSFER_STATUS = 'transfer_status'

# About page
INDEXER_URL_ACCESSIBLE_DESCRIPTION = 'indexer_url'
RGB_PROXY_URL_ACCESSIBLE_DESCRIPTION = 'rgb_proxy_url'
INDEXER_URL_COPY_BUTTON = 'indexer_url_copy_button'
RGB_PROXY_URL_COPY_BUTTON = 'rgb_proxy_url_copy_button'
VANILLA_XPUB_COPY_BUTTON = 'vanilla_xpub_copy_button'
COLORED_XPUB_COPY_BUTTON = 'colored_xpub_copy_button'
MASTER_FINGERPRINT_COPY_BUTTON = 'master_fingerprint_copy_button'
DOWNLOAD_DEBUG_LOG = 'download_debug_log'

# Broadcast/Sign PSBT page
BROADCAST_TRANSACTION_PAGE_CLOSE_BUTTON = 'broadcast_transaction_page_close_button'
BROADCAST_TRANSACTION_PSBT_INPUT = 'broadcast_transaction_psbt_input'
BROADCAST_TRANSACTION_METHOD_SELECTOR = 'broadcast_transaction_method_selector'
BROADCAST_TRANSACTION_PAGE_BUTTON = 'broadcast_transaction_page_button'
SIGN_PSBT_PAGE_BUTTON = 'sign_psbt_page_button'
IMPORT_PSBT_BUTTON = 'import_psbt_button'
EXPORT_PSBT_BUTTON = 'export_psbt_button'
CLEAR_PSBT_BUTTON = 'clear_psbt_button'
REJECT_PSBT_BUTTON = 'reject_psbt_button'

# Settings page
ASK_AUTH_FOR_IMPORTANT_QUESTION = 'auth_for_imp_question'
ASK_AUTH_FOR_APP_LOGIN = 'ask_auth_for_app_login'
HIDE_EXHAUSTED_ASSETS = 'hide_exhausted_assets'
KEYRING_STORAGE = 'keyring_storage'
SET_DEFAULT_FEE_RATE = 'set_default_fee_rate'
SET_DEFAULT_MIN_EXPIRATION = 'set_min_confirmation'
SPECIFY_INDEXER_URL = 'specify_indexer_url'
SPECIFY_RGB_PROXY_URL = 'specify_rgb_proxy_url'
INPUT_BOX_NAME = 'input_box'
KEYRING_TOGGLE_BUTTON = 'keyring_toggle_button'
ASK_AUTH_FOR_APP_LOGIN_TOGGLE = 'ask_auth_for_app_login_toggle'
HIDE_EXHAUSTED_ASSETS_TOGGLE = 'hide_exhausted_assets_toggle'
ASK_AUTH_FOR_IMPORTANT_QUESTION_TOGGLE = 'ask_auth_for_important_question_toggle'

# View unspent list page
UNSPENT_UTXO_ASSET_ID = 'unspent_utxo_asset_id'
UNSPENT_WIDGET = 'unspent_widget'
UNSPENT_CLICKABLE_FRAME = 'unspent_clickable_frame'
UNSPENT_UTXO_OUTPOINT = 'unspent_utxo_outpoint'

# Backup page
BACKUP_CLOSE_BUTTON = 'backup_close_button'
SHOW_MNEMONIC_BUTTON = 'show_mnemonic_button'
CONFIGURE_BACKUP_BUTTON = 'configure_backup_button'
BACKUP_WINDOW = 'backup_window'
BACKUP_WALLET_DATA_BUTTON = 'backup_wallet_data_button'
MNEMONIC_FRAME = 'mnemonic_frame'

# Keyring dialog box
KEYRING_DIALOG_BOX = 'keyring_dialog_box'
KEYRING_MNEMONICS_FRAME = 'keyring_mnemonics_frame'
KEYRING_MNEMONIC_COPY_BUTTON = 'keyring_copy_button'
KEYRING_PASSWORD_FRAME = 'keyring_password_frame'
KEYRING_PASSWORD_COPY_BUTTON = 'keyring_password_copy_button'
KEYRING_PASSWORD_VALUE_LABEL = 'keyring_password_value_label'
KEYRING_MNEMONIC_VALUE_LABEL = 'keyring_mnemonic_value_label'
KEYRING_CONTINUE_BUTTON = 'keyring_continue_button'
KEYRING_CANCEL_BUTTON = 'keyring_cancel_button'
SAVE_CREDENTIALS_CHECK_BOX = 'save_credentials_check_box'

# Watch-only wallet (xpubs and master fingerprint)
KEYRING_XPUB_VANILLA_FRAME = 'keyring_xpub_vanilla_frame'
KEYRING_XPUB_VANILLA_COPY_BUTTON = 'keyring_xpub_vanilla_copy_button'
KEYRING_XPUB_VANILLA_VALUE_LABEL = 'keyring_xpub_vanilla_value_label'
KEYRING_XPUB_COLORED_FRAME = 'keyring_xpub_colored_frame'
KEYRING_XPUB_COLORED_COPY_BUTTON = 'keyring_xpub_colored_copy_button'
KEYRING_XPUB_COLORED_VALUE_LABEL = 'keyring_xpub_colored_value_label'
KEYRING_FINGERPRINT_FRAME = 'keyring_fingerprint_frame'
KEYRING_FINGERPRINT_COPY_BUTTON = 'keyring_fingerprint_copy_button'
KEYRING_FINGERPRINT_VALUE_LABEL = 'keyring_fingerprint_value_label'

# Restore dialog box
RESTORE_DIALOG_BOX = 'restore_dialog_box'
RESTORE_MNEMONIC_INPUT = 'restore_mnemonic_input'
RESTORE_PASSWORD_INPUT = 'restore_password_input'
RESTORE_CONTINUE_BUTTON = 'restore_continue_button'
# Restore dialog box (watch-only/hardware fields)
RESTORE_XPUB_VANILLA_INPUT = 'restore_xpub_vanilla_input'
RESTORE_XPUB_COLORED_INPUT = 'restore_xpub_colored_input'
RESTORE_FINGERPRINT_INPUT = 'restore_fingerprint_input'

# Enter wallet password
ENTER_WALLET_PASSWORD = 'enter_wallet_password'
LOGIN_BUTTON = 'login_button'

# Header frame
NETWORK_AND_BACKUP_FRAME = 'network_and_backup_frame'
HEADER_USB_SYNC_FRAME = 'header_usb_sync_frame'
HEADER_PSBT_INFO_FRAME = 'header_psbt_info_frame'


# Fungibles page
FUNGIBLES_SCROLL_WIDGETS = 'fungibles_scroll_widget'

# Help page
HELP_CARD_TITLE_ACCESSIBLE_DESCRIPTION = 'help_card_title'

# Keyring password
FIRST_SERVICE = 'iris-wallet-vault_test_app_1'
NATIVE_AUTH_ENABLE = 'isNativeAuthenticationEnabled_test_app_1'

# Hardware wallet selection dialog
HW_DEVICE_SELECTION_DIALOG = 'hardware_wallet_device_dialog'
HW_DEVICE_SELECTION_DIALOG_CONNECT_BUTTON = 'hardware_wallet_device_dialog_connect_button'
HW_DEVICE_SELECTION_DIALOG_CANCEL_BUTTON = 'hardware_wallet_device_dialog_cancel_button'
LEDGER_EMULATOR_RADIO_BUTTON = 'Ledger Nano S Plus'

# Hardware wallet connect page
HARDWARE_WALLET_CONNECT_PAGE = 'hardware_wallet_connect_page'
HARDWARE_WALLET_CONNECT_PAGE_LEDGER_OPTION = 'hardware_wallet_connect_page_ledger_option'
HARDWARE_WALLET_CONNECT_PAGE_TREZOR_OPTION = 'hardware_wallet_connect_page_trezor_option'
HARDWARE_WALLET_CONNECT_PAGE_CONTINUE_BUTTON = 'hardware_wallet_connect_page_continue_button'

# Watch only dialog box
WATCH_ONLY_DIALOG = 'watch_only_dialog'
WATCH_ONLY_XPUB_VANILLA = 'watch_only_xpub_vanilla'
WATCH_ONLY_XPUB_COLORED = 'watch_only_xpub_colored'
WATCH_ONLY_MASTER_FINGERPRINT = 'watch_only_master_fingerprint'
WATCH_ONLY_CHECKBOX = 'watch_only_checkbox'
WATCH_ONLY_CANCEL_BUTTON = 'watch_only_cancel_button'
WATCH_ONLY_CONTINUE_BUTTON = 'watch_only_continue_button'

# USB sync dialog
USB_SYNC_DIALOG = 'usb_sync_dialog'
USB_SYNC_DIALOG_CANCEL_BUTTON = 'usb_sync_dialog_cancel_button'
USB_SYNC_DIALOG_CONTINUE_BUTTON = 'usb_sync_dialog_continue_button'

# Issue IFA asset page
ISSUE_IFA_ASSET = 'issue_ifa_asset'
ISSUE_IFA_ASSET_CLOSE_BUTTON = 'ifa_asset_close_button'
IFA_ASSET_TICKER = 'ifa_asset_ticker'
IFA_ASSET_NAME = 'ifa_asset_name'
IFA_ASSET_AMOUNT = 'ifa_asset_amount'
IFA_ASSET_TOTAL_SUPPLY = 'ifa_asset_total_supply'
ISSUE_IFA_BUTTON = 'issue_ifa_button'

# Multisig setup page
MULTISIG_SETUP_PAGE = 'multisig_setup_page'
MULTISIG_TOTAL_SIGNER_INPUT = 'multisig_total_signer_input'
MULTISIG_REQUIRED_SIGNER_INPUT = 'multisig_required_signer_input'
MULTISIG_CONTINUE_BUTTON = 'multisig_continue_button'
MULTISIG_BACK_BUTTON = 'multisig_back_button'
MULTISIG_EXPORT_BUTTON = 'multisig_export_button'
MULTISIG_COLORED_XPUB_COPY_BUTTON = 'multisig_colored_xpub_copy_button'
MULTISIG_COSIGNER_STRING_COPY_BUTTON = 'multisig_cosigner_string_copy_button'
MULTISIG_COSIGNER_STRING_INPUT = 'multisig_cosigner_string_input'
MULTISIG_COSIGNER_CARD = 'multisig_cosigner_card'
MULTISIG_COSIGNER_IMPORT_BUTTON = 'multisig_cosigner_import_button'
MULTISIG_COSIGNER_RESET_BUTTON = 'multisig_cosigner_reset_button'
MULTISIG_COSIGNER_CARD_TITLE = 'multisig_cosigner_card_title'
MULTISIG_COSIGNER_CARD_DESCRIPTION = 'multisig_cosigner_card_description'
MULTISIG_COSIGNER_CARD_PUBLIC_KEY = 'multisig_cosigner_card_public_key'
MULTISIG_COSIGNER_CARD_THRESHOLD = 'multisig_cosigner_card_threshold'
MULTISIG_REVIEW_COSIGNER_STRING_INPUT = 'multisig_review_cosigner_string_input'
