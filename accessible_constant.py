"""Accessible name and description constants"""
# Application name
from __future__ import annotations

from src.utils.constant import APP_NAME

APP1_NAME = 'test_app_1'
APP2_NAME = 'test_app_2'
FIRST_SERVICE = f"{APP_NAME}_{APP1_NAME}"
SECOND_SERVICE = f"{APP_NAME}_{APP2_NAME}"
FIRST_APPLICATION = f"Iris Wallet Regtest {APP1_NAME}"
SECOND_APPLICATION = f"Iris Wallet Regtest {APP2_NAME}"
FIRST_APPLICATION_PATH = f"{APP_NAME}_{APP1_NAME}"
SECOND_APPLICATION_PATH = f"{APP_NAME}_{APP2_NAME}"

# Term and condition page
ACCEPT_BUTTON = 'accept_button'
DECLINE_BUTTON = 'decline_button'
TNC_TXT_DESCRIPTION = 'tnc_txt_description'

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

# Issue RGB20 asset page
ISSUE_RGB20_ASSET = 'issue_rgb20_asset'
ISSUE_RGB20_ASSET_CLOSE_BUTTON = 'issue_rgb20_asset_close_button'
RGB20_ASSET_TICKER = 'rgb20_asset_ticker'
RGB20_ASSET_NAME = 'rgb20_asset_name'
RGB20_ASSET_AMOUNT = 'rgb20_asset_amount'
ISSUE_RGB20_BUTTON = 'issue_rgb20_button'

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
ABOUT_BUTTON = 'about_button'
HELP_BUTTON = 'help_button'
FAUCET_BUTTON = 'faucet_button'
SIDEBAR_RECEIVE_ASSET_BUTTON = 'sidebar_receive_asset_button'
VIEW_UNSPENT_LIST_BUTTON = 'view_unspent_list_button'
SETTINGS_BUTTON = 'settings_button'

# Issue RGB25 asset page
ISSUE_RGB25_ASSET = 'issue_rgb25_asset'
ISSUE_RGB25_BUTTON = 'issue_rgb25_button'
RGB25_ASSET_DESCRIPTION = 'rgb25_asset_description'
RGB25_ASSET_NAME = 'rgb25_asset_name'
RGB25_ASSET_AMOUNT = 'rgb25_asset_amount'
RGB25_UPLOAD_FILE_BUTTON = 'rgb25_upload_file_button'
ISSUE_RGB25_ASSET_CLOSE_BUTTON = 'issue_rgb25_asset_close_button'

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
CONFIRMATION_DIALOG_CONTINUE_BUTTON = 'confirmation_dialog_continue_button'
CONFIRMATION_DIALOG_CANCEL_BUTTON = 'confirmation_dialog_cancel_button'
CONFIRMAION_DIALOG = 'confirmation_dialog'

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
DOWNLOAD_DEBUG_LOG = 'download_debug_log'

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
ASK_AUTH_FOR_IMPORTANT_QUESTION_TOGGLE = ''
HIDE_EXHAUSTED_ASSETS_TOGGLE = ''

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

# Restore dialog box
RESTORE_DIALOG_BOX = 'restore_dialog_box'
RESTORE_MNEMONIC_INPUT = 'restore_mnemonic_input'
RESTORE_PASSWORD_INPUT = 'restore_password_input'
RESTORE_CONTINUE_BUTTON = 'restore_continue_button'

# Enter wallet password
ENTER_WALLET_PASSWORD = 'enter_wallet_password'
LOGIN_BUTTON = 'login_button'

# Header frame
NETWORK_AND_BACKUP_FRAME = 'network_and_backup_frame'
KEYRING_TOGGLE_BUTTON = 'keyring_toggle_button'
HIDE_EXHAUSTED_ASSETS_TOGGLE = 'hide_exhausted_assets_toggle'
ASK_AUTH_FOR_IMPORTANT_QUESTION_TOGGLE = 'ask_auth_for_important_question_toggle'
ASK_AUTH_FOR_APP_LOGIN_TOGGLE = 'ask_auth_for_app_login_toggle'

# Keyring dialog box
KEYRING_DIALOG_BOX = 'keyring_dialog_box'
KEYRING_MNEMONICS_FRAME = 'keyring_mnemonics_frame'
KEYRING_COPY_BUTTON = 'keyring_copy_button'
KEYRING_PASSWORD_FRAME = 'keyring_password_frame'
KEYRING_PASSWORD_COPY_BUTTON = 'keyring_password_copy_button'
KEYRING_PASSWORD_VALUE_LABEL = 'keyring_password_value_label'
KEYRING_MNEMONIC_VALUE_LABEL = 'keyring_mnemonic_value_label'


# Fungibles page
FUNGIBLES_SCROLL_WIDGETS = 'fungibles_scroll_widget'

# Help page
HELP_CARD_TITLE_ACCESSIBLE_DESCRIPTION = 'help_card_title'

# Keyring password
FIRST_SERVICE = 'iris wallet vault_test_app_1'
NATIVE_AUTH_ENABLE = 'isNativeAuthenticationEnabled_test_app_1'
