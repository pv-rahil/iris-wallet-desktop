"""
Mocked data for the common operation service test
"""
from __future__ import annotations

from rgb_lib import Keys

from src.model.common_operation_model import UnlockResponseModel


MNEMONIC = 'skill lamp please gown put season degree collect decline account monitor insane'
XPUB = 'xpub1234567890'
ACCOUNT_XPUB = 'xpub1234567890'
ACCOUNT_XPUB_FINGERPRINT = 'xpub1234567890'
# Mocked response of init api
mocked_data_init_api_response = Keys(
    mnemonic=MNEMONIC, xpub=XPUB, account_xpub=ACCOUNT_XPUB, account_xpub_fingerprint=ACCOUNT_XPUB_FINGERPRINT,
)

mocked_unlock_api_res = UnlockResponseModel(status=True)
mocked_password: str = 'Random@123'
