"""
Mocked data for the common operation service test
"""
from __future__ import annotations

from rgb_lib import Keys


MNEMONIC = 'skill lamp please gown put season degree collect decline account monitor insane'
XPUB = 'xpub1234567890'
ACCOUNT_XPUB_VANILLA = 'xpub1234567890'
ACCOUNT_XPUB_COLORED = 'xpub1234567890'
ACCOUNT_XPUB_COLORED_FINGERPRINT = 'xpub1234567890'
# Mocked response of init api
mocked_data_init_api_response = Keys(
    mnemonic=MNEMONIC, xpub=XPUB, account_xpub_vanilla=ACCOUNT_XPUB_VANILLA,
    account_xpub_colored=ACCOUNT_XPUB_COLORED, account_xpub_colored_fingerprint=ACCOUNT_XPUB_COLORED_FINGERPRINT,
)

mocked_password: str = 'Random@123'
