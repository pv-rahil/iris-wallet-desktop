# pylint: disable=too-few-public-methods
"""
AT-SPI helper functions for e2e tests.
"""
from __future__ import annotations

import gc
import time

from dogtail.tree import root


def refresh_atspi_tree():
    """
    Force AT-SPI tree refresh by accessing root.
    This helps clear stale element caches between tests.
    """
    try:
        _ = root.children
        gc.collect()
        time.sleep(2)  # for stabilize the tree
    except Exception:
        pass
