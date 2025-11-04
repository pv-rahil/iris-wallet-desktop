"""
IssueIfaPageObjects class provides methods to interact with issue IFA page elements.
"""
from __future__ import annotations

from accessible_constant import IFA_ASSET_AMOUNT
from accessible_constant import IFA_ASSET_NAME
from accessible_constant import IFA_ASSET_TICKER
from accessible_constant import ISSUE_IFA_ASSET_CLOSE_BUTTON
from accessible_constant import ISSUE_IFA_BUTTON
from e2e_tests.test.utilities.base_operation import BaseOperations


class IssueIfaPageObjects(BaseOperations):
    """
    IssueIfaPageObjects class provides methods to interact with issue IFA page elements.
    Note: IFA UI reuses accessible names from NIA constants.
    """

    def __init__(self, application):
        super().__init__(application)

        self.close_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ISSUE_IFA_ASSET_CLOSE_BUTTON,
        )
        self.asset_name = lambda: self.perform_action_on_element(
            role_name='text', name=IFA_ASSET_NAME,
        )
        self.asset_ticker = lambda: self.perform_action_on_element(
            role_name='text', name=IFA_ASSET_TICKER,
        )
        self.asset_amount = lambda: self.perform_action_on_element(
            role_name='text', name=IFA_ASSET_AMOUNT,
        )
        self.issue_ifa_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ISSUE_IFA_BUTTON,
        )

    def click_close_button(self):
        """Clicks the close button if it is displayed."""
        return self.do_click(self.close_button()) if self.do_is_displayed(self.close_button()) else None

    def enter_asset_name(self, asset_name):
        """Enters the asset name if it is displayed."""
        return self.do_set_value(self.asset_name(), asset_name) if self.do_is_displayed(self.asset_name()) else None

    def enter_asset_ticker(self, asset_ticker):
        """Enters the asset ticker if it is displayed."""
        return self.do_set_value(self.asset_ticker(), asset_ticker) if self.do_is_displayed(self.asset_ticker()) else None

    def enter_asset_amount(self, asset_amount):
        """Enters the asset amount if it is displayed."""
        return self.do_set_value(self.asset_amount(), asset_amount) if self.do_is_displayed(self.asset_amount()) else None

    def click_issue_ifa_button(self):
        """Clicks the issue IFA button if it is displayed."""
        return self.do_click(self.issue_ifa_button()) if self.do_is_displayed(self.issue_ifa_button()) else None
