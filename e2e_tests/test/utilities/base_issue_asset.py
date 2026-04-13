# pylint: disable=too-few-public-methods, too-many-arguments
"""
Base class for issue asset feature classes.
"""
from __future__ import annotations

from abc import abstractmethod
from contextlib import contextmanager
from typing import Generator

from accessible_constant import HARDWARE_WALLET_VARIANTS
from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import ONLINE_CREATE_HARDWARE
from accessible_constant import ONLINE_LOAD_HARDWARE
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_with_hardware_wallet
from e2e_tests.test.utilities.send_flow_helpers import handle_native_auth_and_focus
from e2e_tests.test.utilities.send_flow_helpers import handle_native_auth_utxo_and_success
from e2e_tests.test.utilities.send_flow_helpers import handle_success_home_button
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class IFAOperationsMixin:
    """
    Mixin for IFA-related operations providing common initialization.
    """

    wallet_feature: Wallet

    def _init_ifa_features(self, application) -> None:
        """
        Initialize IFA features including wallet feature.

        Args:
            application: Application instance.
        """
        self.wallet_feature = Wallet(application)

    def _get_issue_page_objects(self):
        """Get the issue page objects for IFA asset type."""
        return self.issue_ifa_page_objects


class BaseIssueAsset(IFAOperationsMixin):
    """
    Base class for issue asset feature classes providing common hardware wallet handling.
    """

    hardware_wallet_emulator = None

    def _init_hardware_wallet(self, variant_name: str | None, app_name: str = RGB_LEDGER_APP_NAME) -> bool:
        """
        Initialize hardware wallet emulator if variant requires it.

        Args:
            variant_name: Wallet variant name.
            app_name: Ledger app name (default: RGB_LEDGER_APP_NAME).

        Returns:
            True if hardware wallet was initialized.
        """
        if variant_name in HARDWARE_WALLET_VARIANTS and variant_name not in REQUIRE_USB_VARIANTS:
            self.hardware_wallet_emulator = handle_hardware_wallet(
                app_name=app_name,
            )
            return True
        return False

    def _init_multisig_hardware_wallet(self, wallet_variant_name: str | None, utxo_required: bool = True) -> bool:
        """
        Initialize hardware wallet for multisig if required.

        Args:
            wallet_variant_name: Wallet variant name.
            utxo_required: Whether UTXO is required.

        Returns:
            True if hardware wallet was initialized.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        if is_hardware and utxo_required:
            self.hardware_wallet_emulator = handle_hardware_wallet(
                app_name=RGB_LEDGER_APP_NAME,
            )
            return True
        return False

    def _is_multisig_hardware(self, wallet_variant_name: str | None) -> bool:
        """Check if wallet variant is multisig hardware."""
        return wallet_variant_name in MULTISIG_HARDWARE_VARIANTS

    def _is_online_hardware(self, wallet_variant_name: str | None) -> bool:
        """Check if wallet variant is online single-sig hardware."""
        return wallet_variant_name in (ONLINE_CREATE_HARDWARE, ONLINE_LOAD_HARDWARE)

    def _cleanup_hardware_wallet(self) -> None:
        """Clean up hardware wallet emulator if it exists."""
        if self.hardware_wallet_emulator:
            self.hardware_wallet_emulator.terminate()
            self.hardware_wallet_emulator = None

    def _confirm_on_hardware_wallet(
        self, wallet_feature, is_ifa: bool = False, is_inflate: bool = False,
        is_online: bool = True,
    ) -> None:
        """
        Confirm transaction on hardware wallet if emulator exists.

        Args:
            wallet_feature: Wallet feature instance.
            is_ifa: Whether this is an IFA issue or inflate operation (for UTXO count).
            is_inflate: Whether this is an IFA inflate operation (for final RGB signing).
            is_online: Whether this is an online hardware wallet.
        """
        if self.hardware_wallet_emulator:
            wallet_feature.confirm_transaction_on_hardware_wallet(
                LEDGER_EMULATOR_APP_NAME, is_ifa=is_ifa, is_inflate=is_inflate,
                is_online=is_online,
            )

    @contextmanager
    def _asset_operation_context(self, variant_name: str | None = None) -> Generator[None, None, None]:
        """
        Context manager for asset operations with hardware wallet handling.

        Args:
            variant_name: Wallet variant name for hardware wallet initialization.

        Yields:
            None
        """
        try:
            if variant_name:
                self._init_hardware_wallet(variant_name)
            yield
        except Exception as e:
            raise e
        finally:
            self._cleanup_hardware_wallet()

    @contextmanager
    def _multisig_asset_operation_context(
        self, wallet_variant_name: str | None = None, utxo_required: bool = True,
    ) -> Generator[None, None, None]:
        """
        Context manager for multisig asset operations with hardware wallet handling.

        Args:
            wallet_variant_name: Wallet variant name.
            utxo_required: Whether UTXO is required.

        Yields:
            None
        """
        try:
            self._init_multisig_hardware_wallet(
                wallet_variant_name, utxo_required,
            )
            yield
        except Exception as e:
            raise e
        finally:
            self._cleanup_hardware_wallet()

    def _enter_asset_ticker_if_displayed(self, ticker: str) -> None:
        """Enter asset ticker if the field is displayed."""
        page_objects = self._get_issue_page_objects()
        if self.do_is_displayed(page_objects.asset_ticker()):
            page_objects.enter_asset_ticker(ticker)

    def _enter_asset_name_if_displayed(self, name: str) -> None:
        """Enter asset name if the field is displayed."""
        page_objects = self._get_issue_page_objects()
        if self.do_is_displayed(page_objects.asset_name()):
            page_objects.enter_asset_name(name)

    def _enter_asset_amount_if_displayed(self, amount: str) -> None:
        """Enter asset amount if the field is displayed."""
        page_objects = self._get_issue_page_objects()
        if self.do_is_displayed(page_objects.asset_amount()):
            page_objects.enter_asset_amount(amount)

    def _click_issue_button_if_displayed(self) -> None:
        """Click issue button if displayed."""
        page_objects = self._get_issue_page_objects()
        # Each asset type has its own button method
        if hasattr(page_objects, 'issue_ifa_button'):
            if self.do_is_displayed(page_objects.issue_ifa_button()):
                page_objects.click_issue_ifa_button()
        elif hasattr(page_objects, 'issue_nia_button'):
            if self.do_is_displayed(page_objects.issue_nia_button()):
                page_objects.click_issue_nia_button()
        elif hasattr(page_objects, 'issue_cfa_button'):
            if self.do_is_displayed(page_objects.issue_cfa_button()):
                page_objects.click_issue_cfa_button()

    @abstractmethod
    def _get_issue_page_objects(self):
        """Get the issue page objects for the specific asset type."""

    @abstractmethod
    def do_is_displayed(self, element) -> bool:
        """Check if element is displayed."""

    @abstractmethod
    def do_focus_on_application(self, application) -> None:
        """Focus on the application."""

    def _enter_native_password_if_enabled(self, is_native_auth_enabled: bool) -> None:
        """
        Enter native password if native auth is enabled.

        Args:
            is_native_auth_enabled: Whether native auth is enabled.
        """
        if is_native_auth_enabled:
            self.enter_native_password()  # type: ignore[attr-defined]

    def _handle_issue_confirmation_and_success(
        self, application, is_native_auth_enabled: bool, is_ifa: bool = False,
        is_inflate: bool = False, is_online: bool = True,
    ) -> None:
        """
        Handle hardware wallet confirmation, native auth, and success flow.

        Args:
            application: Application instance.
            is_native_auth_enabled: Whether native auth is enabled.
            is_ifa: Whether this is an IFA issue or inflate operation (for UTXO count).
            is_inflate: Whether this is an IFA inflate operation (for final RGB signing).
            is_online: Whether this is an online hardware wallet.
        """
        self._confirm_on_hardware_wallet(
            self.wallet_feature, is_ifa=is_ifa, is_inflate=is_inflate,
            is_online=is_online,
        )
        handle_native_auth_and_focus(self, application, is_native_auth_enabled)
        handle_success_home_button(self)

    def _handle_multisig_issue_flow(
        self,
        application,
        wallet_variant_name: str | None,
        is_native_auth_enabled: bool,
        asset_ticker: str,
        asset_name: str,
        asset_amount: str,
        utxo_required: bool = True,
        pre_issue_callback=None,
    ) -> None:
        """
        Handle common multisig issue flow with native auth and UTXO handling.

        Args:
            application: Application instance.
            wallet_variant_name: Wallet variant name.
            is_native_auth_enabled: Whether native auth is enabled.
            asset_ticker: Asset ticker.
            asset_name: Asset name.
            asset_amount: Asset amount.
            utxo_required: Whether UTXO is required.
            pre_issue_callback: Optional callback to execute before entering asset details.
        """

        is_hardware = self._is_multisig_hardware(wallet_variant_name)
        with self._multisig_asset_operation_context(wallet_variant_name, utxo_required):
            self.do_focus_on_application(application)

            if pre_issue_callback:
                pre_issue_callback()

            self._enter_asset_ticker_if_displayed(asset_ticker)
            self._enter_asset_name_if_displayed(asset_name)
            self._enter_asset_amount_if_displayed(asset_amount)
            self._click_issue_button_if_displayed()

            self._enter_native_password_if_enabled(is_native_auth_enabled)

            handle_utxo_confirmation_with_hardware_wallet(
                self, self, self.wallet_feature, LEDGER_EMULATOR_APP_NAME,
                utxo_required=utxo_required, is_hardware=is_hardware,
            )

    def _handle_multisig_inflate_flow(
        self,
        application,
        wallet_variant_name: str | None,
        utxo_required: bool,
        is_native_auth_enabled: bool,
        pre_flow_callback=None,
    ) -> None:
        """
        Handle common multisig inflate/issue flow with native auth and UTXO handling.

        Args:
            application: Application instance.
            wallet_variant_name: Wallet variant name.
            utxo_required: Whether UTXO is required.
            is_native_auth_enabled: Whether native auth is enabled.
            pre_flow_callback: Optional callback to execute after focus but before main flow.
        """
        is_hardware = self._is_multisig_hardware(wallet_variant_name)
        with self._multisig_asset_operation_context(wallet_variant_name, utxo_required):
            self.do_focus_on_application(application)

            if pre_flow_callback:
                pre_flow_callback()

            handle_native_auth_utxo_and_success(
                self, application, self.wallet_feature,
                is_native_auth_enabled=is_native_auth_enabled,
                utxo_required=utxo_required,
                is_hardware=is_hardware,
            )
