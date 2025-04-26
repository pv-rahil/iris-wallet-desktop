"""
data
====

Description:
------------
The `data` package contains various repositories that provide apis for
bitcoin, channels management, invoice, payments, peer, rgb and common operations.

Submodules:
-----------
- btc_repository: Functions for bitcoin related.
- channels_repository: Functions for channels related.
- common_operations_repository: Functions for common operations.
- invoices_repository: Functions for invoice.
- payments_repository: Functions for payments.
- peer_repository: Functions for peer.
- rgb_repository: Functions for rgb.
- setting_repository: Functions for system setting.

Usage:
------
Examples of how to use the repositories in this package:

    >>> from data import btc_repository
    >>> result = btc_repository.get_address(data)
    >>> print(result)

"""
from __future__ import annotations
