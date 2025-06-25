"""
viewmodels
==========

Description:
------------
The `viewmodels` package contains various viewmodels that
connect view and model functionality.

Submodules:
-----------
- IssueNIAViewModel: Connects NIA models to IssueNIAWidget
                       to enable communication between them.
- MainAssetViewModel: Connects main assets models to MainAssetWidget
                      to enable communication between them.
- SetWalletPasswordViewModel: Connects setWallet models to SetWalletWidget
                              to enable communication between them.
- TermsViewModel: Connects term models to TerAndConditionWidget
                  to enable communication between them.
- WelcomeViewModel: Connects welcome models to WelcomeWidget
                    to enable communication between them.
- BackupViewModel: Handles backup operations and UI signals.
- BitcoinViewModel: Manages Bitcoin page activities.
- CFAViewModel: Manages activities related to CFA assets.
- EnterWalletPasswordViewModel: Manages the set wallet password page.
- FaucetsViewModel: Manages activities related to faucets.
- EstimateFeeViewModel: Estimates transaction fees.
- HeaderFrameViewModel: Handles network connectivity in the header.
- IssueCFAViewModel: Manages activities related to issuing CFA assets.
- ReceiveBitcoinViewModel: Manages activities of the receive Bitcoin page.
- ReceiveCFAViewModel: Manages activities of the receive CFA asset page.
- RestoreViewModel: Manages activities of the restore page.
- SendBitcoinViewModel: Manages activities of the send Bitcoin page.
- SettingViewModel: Manages settings and configurations.
- SplashViewModel: Manages activities of the splash page.
- UnspentListViewModel: Manages activities of the unspent list page.

Usage:
------
Examples of how to use the utilities in this package:

    >>> from viewmodels import IssueNIAViewModel
    >>> model = IssueNIAViewModel()
    >>> print(model)
"""
from __future__ import annotations
