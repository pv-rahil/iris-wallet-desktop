"""
viewmodels
==========

Description:
------------
The `viewmodels` package contains various viewmodels that
connect view and model functionality.

Submodules:
-----------
- IssueRGB20ViewModel: Connects RGB20 models to IssueRGB20Widget
                       to enable communication between them.
- MainAssetViewModel: Connects main assets models to MainAssetWidget
                      to enable communication between them.
- SetWalletPasswordViewModel: Connects setWallet models to SetWalletWidget
                              to enable communication between them.
- TermsViewModel: Connects term models to TerAndConditionWidget
                  to enable communication between them.
- WelcomeViewModel: Connects welcome models to WelcomeWidget
                    to enable communication between them.

Usage:
------
Examples of how to use the utilities in this package:

    >>> from viewmodels import IssueRGB20ViewModel
    >>> model = IssueRGB20ViewModel()
    >>> print(model)
"""
from __future__ import annotations
