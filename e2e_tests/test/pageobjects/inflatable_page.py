"""
Inflatable page objects class for interacting with IFA assets.
"""
from __future__ import annotations

from accessible_constant import FUNGIBLES_SCROLL_WIDGETS
from accessible_constant import HEADER_PSBT_INFO_FRAME
from accessible_constant import HEADER_USB_SYNC_FRAME
from accessible_constant import ISSUE_IFA_ASSET
from accessible_constant import NETWORK_AND_BACKUP_FRAME
from e2e_tests.test.utilities.base_operation import BaseOperations


class InflatablePageObjects(BaseOperations):
    """Inflatable page objects class."""

    def __init__(self, application):
        """
        Initializes the InflatablePageObjects class with the application.

        Args:
            application: The application instance.
        """
        super().__init__(application)

        self.ifa_asset_name = None
        # Uses same accessible name as wired in InflatableAssetWidget.action_button
        self.issue_ifa_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ISSUE_IFA_ASSET,
        )
        self.backup_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=NETWORK_AND_BACKUP_FRAME,
        )
        self.scroll_area = lambda: self.perform_action_on_element(
            role_name='filler', name=FUNGIBLES_SCROLL_WIDGETS,
        )
        self.usb_sync_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=HEADER_USB_SYNC_FRAME,
        )
        self.psbt_info_frame = lambda: self.perform_action_on_element(
            role_name='panel', name=HEADER_PSBT_INFO_FRAME,
        )

    def click_issue_ifa_button(self):
        """Clicks the issue IFA button if it is displayed."""
        return self.do_click(self.issue_ifa_button()) if self.do_is_displayed(self.issue_ifa_button()) else None

    def get_ifa_asset_name(self, asset_name):
        """
        Retrieves the IFA asset name label text.
        """
        self.ifa_asset_name = self.perform_action_on_element(
            role_name='label', name=asset_name,
        )
        return self.do_get_text(self.ifa_asset_name) if self.do_is_displayed(self.ifa_asset_name) else None

    def click_ifa_frame(self, asset_name):
        """Clicks an IFA asset frame by visible asset label name."""
        self.ifa_asset_name = self.perform_action_on_element(
            role_name='label', name=asset_name,
        )
        return self.do_click(self.ifa_asset_name) if self.do_is_displayed(self.ifa_asset_name) else None
