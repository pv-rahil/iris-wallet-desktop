# pylint: disable=too-few-public-methods
"""
AT-SPI helper functions for e2e tests.
"""
from __future__ import annotations

import gc
import time

from dogtail.tree import root


def aggressive_cleanup():
    """Aggressive cleanup to prevent AT-SPI exhaustion in long tests."""
    # Refresh AT-SPI tree
    try:
        _ = root.children
    except Exception:
        pass
    # Force garbage collection
    gc.collect()
    # Small delay to let UI settle
    time.sleep(0.5)


def refresh_atspi_tree():
    """
    Force AT-SPI tree refresh by accessing root.
    This helps clear stale element caches between tests.
    """
    try:
        _ = root.children
    except Exception:
        pass
