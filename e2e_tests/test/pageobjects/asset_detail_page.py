# pylint: disable=too-many-instance-attributes
"""
This file contains the AssetDetailPageObjects class, which provides methods for interacting with the asset detail page.
"""
from __future__ import annotations

from dogtail.tree import root

from accessible_constant import ASSET_CLOSE_BUTTON
from accessible_constant import ASSET_ID_COPY_BUTTON
from accessible_constant import ASSET_RECEIVE_BUTTON
from accessible_constant import ASSET_REFRESH_BUTTON
from accessible_constant import ASSET_SEND_BUTTON
from accessible_constant import ASSET_SPENDABLE_BALANCE
from accessible_constant import ASSET_TOTAL_BALANCE
from accessible_constant import CONFIRMAION_DIALOG
from accessible_constant import CONFIRMATION_DIALOG_CONTINUE_BUTTON
from accessible_constant import RGB_TRANSACTION_DETAIL_FRAME
from accessible_constant import TRANSACTION_DETAIL_CLOSE_BUTTON
from accessible_constant import TRANSFER_STATUS
from e2e_tests.test.utilities.base_operation import BaseOperations


class AssetDetailPageObjects(BaseOperations):
    """
    This class provides methods for interacting with the asset detail page.
    """

    def __init__(self, application):
        """
        Initializes the AssetDetailPageObjects class.
        Parameters:
            application (object): The application object.
        """
        super().__init__(application)

        self.close_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ASSET_CLOSE_BUTTON,
        )
        self.send_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ASSET_SEND_BUTTON,
        )
        self.refresh_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ASSET_REFRESH_BUTTON,
        )
        self.total_balance = lambda: self.perform_action_on_element(
            role_name='label', description=ASSET_TOTAL_BALANCE,
        )
        self.spendable_balance = lambda: self.perform_action_on_element(
            role_name='label', description=ASSET_SPENDABLE_BALANCE,
        )
        self.rgb_transaction_frame = lambda: self.get_first_element(
            role_name='panel', name=RGB_TRANSACTION_DETAIL_FRAME,
        )
        self.transfer_status = lambda: self.get_first_element(
            role_name='label', description=TRANSFER_STATUS,
        )
        self.receive_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ASSET_RECEIVE_BUTTON,
        )
        self.copy_button = lambda: self.perform_action_on_element(
            role_name='push button', name=ASSET_ID_COPY_BUTTON,
        )
        self.fail_transfer_button = lambda: self.get_first_element(
            role_name='push button', name=TRANSACTION_DETAIL_CLOSE_BUTTON,
        )
        self.confirmation_dialog = lambda: root.child(
            roleName='dialog', name=CONFIRMAION_DIALOG,
        )
        self.confirmation_continue_button = lambda: self.confirmation_dialog().child(
            roleName='push button', name=CONFIRMATION_DIALOG_CONTINUE_BUTTON,
        )

    def click_close_button(self):
        """
        Clicks the close button on the asset detail page.

        Returns:
            bool: True if the button is clicked successfully, None otherwise.
        """
        return self.do_click(self.close_button()) if self.do_is_displayed(self.close_button()) else None

    def click_send_button(self):
        """
        Clicks the send button on the asset detail page.

        Returns:
            bool: True if the button is clicked successfully, None otherwise.
        """
        return self.do_click(self.send_button()) if self.do_is_displayed(self.send_button()) else None

    def click_receive_button(self):
        """
        Clicks the receive button on the asset detail page.

        Returns:
            bool: True if the button is clicked successfully, None otherwise.
        """
        return self.do_click(self.receive_button()) if self.do_is_displayed(self.receive_button()) else None

    def click_refresh_button(self):
        """
        Clicks the refresh button on the asset detail page.

        Returns:
            bool: True if the button is clicked successfully, None otherwise.
        """
        return self.do_click(self.refresh_button()) if self.do_is_displayed(self.refresh_button()) else None

    def get_total_balance(self):
        """
        Retrieves the total balance from the asset detail page.

        Returns:
            str: The total balance if it is displayed, None otherwise.
        """
        return self.do_get_text(self.total_balance()) if self.do_is_displayed(self.total_balance()) else None

    def get_spendable_balance(self):
        """
        Retrieves the spendable balance from the asset detail page.

        Returns:
            str: The spendable balance if it is displayed, None otherwise.
        """
        return self.do_get_text(self.spendable_balance()) if self.do_is_displayed(self.spendable_balance()) else None

    def click_rgb_transaction_on_chain_frame(self):
        """
        Clicks the bitcoin transaction frame on the asset detail page.
        """
        return self.do_click(self.rgb_transaction_frame()) if self.do_is_displayed(self.rgb_transaction_frame()) else None

    def get_transfer_status(self):
        """
        Retrieves the transfer status from the asset detail page.
        """
        return self.do_get_text(self.transfer_status()) if self.do_is_displayed(self.transfer_status()) else None

    def click_copy_button(self):
        """
        Clicks the copy button on the asset detail page.
        """
        return self.do_click(self.copy_button()) if self.do_is_displayed(self.copy_button()) else None

    def click_confirmation_continue_button(self):
        """
        Clicks the transaction detail frame on the asset detail page.
        """
        return self.do_click(self.confirmation_continue_button()) if self.do_is_displayed(self.confirmation_continue_button()) else None

    def click_fail_transfer_button(self):
        """
        Clicks the fail transfer button on the asset detail page.
        """
        return self.do_click(self.fail_transfer_button()) if self.do_is_displayed(self.fail_transfer_button()) else None
