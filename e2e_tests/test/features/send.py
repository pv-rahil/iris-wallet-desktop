# pylint: disable=too-many-arguments,too-many-branches
"""
SendOperation class provides methods for sending assets using bitcoin transfer.
"""
from __future__ import annotations

import time

from accessible_constant import LEDGER_EMULATOR_APP_NAME
from accessible_constant import MULTISIG_HARDWARE_VARIANTS
from accessible_constant import REQUIRE_USB_VARIANTS
from accessible_constant import RGB_LEDGER_APP_NAME
from e2e_tests.test.features.wallet import Wallet
from e2e_tests.test.pageobjects.main_page_objects import MainPageObjects
from e2e_tests.test.utilities.base_operation import BaseOperations
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_dialog
from e2e_tests.test.utilities.psbt_helpers import handle_utxo_confirmation_with_hardware_wallet
from e2e_tests.test.utilities.wallet_variants import handle_hardware_wallet


class SendOperation(MainPageObjects, BaseOperations):
    """
    Initializes the SendOperation class with the application.
    """

    def __init__(self, application):
        """
        Sends assets using bitcoin transfer.
        """
        self.hardware_wallet = None
        self.wallet_features = Wallet(application)
        super().__init__(application)

    def send(self, application, receiver_invoice, amount=None, is_hardware_wallet: bool = False, purpose: str | None = None, is_native_auth_enabled: bool = False):
        """
        Send assets

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        """
        try:
            # Use RGB Ledger app for all hardware wallet operations (can sign both BTC and RGB)
            if is_hardware_wallet:
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
                self.send_asset_page_objects.enter_asset_invoice(
                    receiver_invoice,
                )
            self.do_focus_on_application(application)

            if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
                self.send_asset_page_objects.enter_asset_amount(amount)

            if self.do_is_displayed(self.send_asset_page_objects.send_button()):
                self.send_asset_page_objects.click_send_button()

            if is_native_auth_enabled is True:
                self.enter_native_password()

            if is_hardware_wallet:
                # RGB app handles both BTC and RGB transactions
                is_rgb = purpose == 'send_asset'
                is_btc = not is_rgb  # BTC send only when NOT sending RGB asset
                # Assume online hardware wallet for send operations
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_rgb=is_rgb, is_online=True, is_btc=is_btc,
                )
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                time.sleep(2)
                self.hardware_wallet.terminate()

    def send_with_no_fund(self, application, receiver_invoice, amount):
        """
        Send assets without sufficient funds.
        """
        validation = None
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)

        if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if self.do_is_displayed(self.send_asset_page_objects.amount_validation()):
            validation = self.send_asset_page_objects.get_amount_validation()

        if self.do_is_displayed(self.send_asset_page_objects.send_asset_close_button()):
            self.send_asset_page_objects.click_send_asset_close_button()

        return validation

    def send_with_custom_fee_rate(self, application, receiver_invoice, amount, fee_rate, is_hardware_wallet: bool = False):
        """
        Sends assets using bitcoin with a custom fee rate.
        """
        try:

            description = None

            self.do_focus_on_application(application)
            if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
                self.send_asset_page_objects.enter_asset_invoice(
                    receiver_invoice,
                )

            if self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
                self.send_asset_page_objects.enter_asset_amount(amount)

            if self.do_is_displayed(self.send_asset_page_objects.fee_rate_input()):
                self.send_asset_page_objects.enter_fee_rate(fee_rate)

            if is_hardware_wallet:
                self.hardware_wallet = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
                # Wait for emulator to be fully initialized
                time.sleep(3)

            self.do_focus_on_application(application)

            if self.do_is_displayed(self.send_asset_page_objects.send_button()):
                self.send_asset_page_objects.click_send_button()

            if is_hardware_wallet:
                self.wallet_features.confirm_transaction_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME, is_btc=True,
                )

            self.do_focus_on_application(application)
            _, description = self.toaster_page_objects.click_toaster_frame()
        except Exception as e:
            raise e
        finally:
            if self.hardware_wallet:
                self.hardware_wallet.terminate()
        return description

    def create_psbt(
        self, application, receiver_invoice, amount=None, fee_rate=None, wallet_variant_name=None,
        is_native_auth_enabled: bool = False, utxo_required: bool = True,
    ):
        """
        Create psbt

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        :param wallet_variant_name: The wallet variant name for USB sync check.
        :param is_native_auth_enabled: Whether native auth is enabled.
        """
        self.do_focus_on_application(application)

        if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
            self.send_asset_page_objects.enter_asset_invoice(receiver_invoice)
        self.do_focus_on_application(application)

        if amount and hasattr(self.send_asset_page_objects, 'asset_amount_input') and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
            self.send_asset_page_objects.enter_asset_amount(amount)

        if fee_rate:
            if self.do_is_displayed(self.send_asset_page_objects.fee_rate_input()):
                self.send_asset_page_objects.enter_fee_rate(fee_rate)

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if utxo_required:
            handle_utxo_confirmation_dialog(self, self, utxo_required=True)

        if is_native_auth_enabled:
            self.enter_native_password()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        try:
            if self.do_is_displayed(self.bitcoin_detail_page_objects.bitcoin_close_button()):
                self.bitcoin_detail_page_objects.click_bitcoin_close_button()
        except Exception as _:
            pass

        if wallet_variant_name and wallet_variant_name in REQUIRE_USB_VARIANTS:
            self.wallet_features.usb_sync()

    def create_psbt_for_multisig(self, application, receiver_invoice, amount, wallet_variant_name, utxo_required: bool = False, is_native_auth_enabled: bool = False):
        """
        Create psbt for multisig wallet

        :param receiver_invoice: The recipient's invoice.
        :param amount: The amount to send.
        :param wallet_variant_name: The wallet variant name.
        :param utxo_required: Whether UTXO creation is required.
        :param is_native_auth_enabled: Whether native auth is enabled.
        """
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        hardware_wallet_emulator = None
        try:
            if is_hardware and utxo_required:
                hardware_wallet_emulator = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )
            self.do_focus_on_application(application)

            if self.do_is_displayed(self.send_asset_page_objects.invoice_input()):
                self.send_asset_page_objects.enter_asset_invoice(
                    receiver_invoice,
                )

            if amount and self.do_is_displayed(self.send_asset_page_objects.asset_amount_input()):
                self.send_asset_page_objects.enter_asset_amount(amount)

            if self.do_is_displayed(self.send_asset_page_objects.send_button()):
                self.send_asset_page_objects.click_send_button()

            if is_native_auth_enabled:
                self.enter_native_password()

            if utxo_required:
                handle_utxo_confirmation_with_hardware_wallet(
                    self, self, self.wallet_features, LEDGER_EMULATOR_APP_NAME,
                    utxo_required=True, is_hardware=is_hardware, wallet_variant=wallet_variant_name,
                )

            try:
                if self.do_is_displayed(self.bitcoin_detail_page_objects.bitcoin_close_button()):
                    self.bitcoin_detail_page_objects.click_bitcoin_close_button()
            except Exception as _:
                pass

            if wallet_variant_name in REQUIRE_USB_VARIANTS:
                self.wallet_features.usb_sync()
        except Exception as e:
            raise e
        finally:
            if hardware_wallet_emulator:
                hardware_wallet_emulator.terminate()

    def send_asset_for_multisig(self, application, wallet_variant_name, is_native_auth_enabled: bool = False):
        """
        Send asset for multisig wallet

        :param is_native_auth_enabled: Whether native auth is enabled.
        """
        self.do_focus_on_application(application)
        is_hardware = wallet_variant_name in MULTISIG_HARDWARE_VARIANTS
        usb_require = wallet_variant_name in REQUIRE_USB_VARIANTS
        hw_emu = None
        try:
            if is_hardware and not usb_require:
                hw_emu = handle_hardware_wallet(
                    app_name=RGB_LEDGER_APP_NAME,
                )

            if self.do_is_displayed(self.asset_detail_page_objects.resume_draft_frame()):
                self.asset_detail_page_objects.click_resume_draft_frame()

            if self.do_is_displayed(self.send_asset_page_objects.send_button()):
                self.send_asset_page_objects.click_send_button()

            if is_native_auth_enabled:
                self.enter_native_password()

            if hw_emu:
                self.wallet_features.sign_multisig_on_hardware_wallet(
                    LEDGER_EMULATOR_APP_NAME,
                )

            if usb_require:
                self.wallet_features.usb_sync()
                # Wait for USB sync to complete before switching apps
                time.sleep(3)

        except Exception as e:
            raise e
        finally:
            if hw_emu:
                hw_emu.terminate()

    def send_asset_for_single_sig_offline(self, application, is_native_auth_enabled: bool = False):
        """
        Send asset for single-sig offline wallet (watch-only with hardware signer)

        :param application: Application instance.
        :param is_native_auth_enabled: Whether native auth is enabled.
        """
        self.do_focus_on_application(application)

        # Click resume draft if displayed (for continuing after UTXO creation)
        if self.do_is_displayed(self.asset_detail_page_objects.resume_draft_frame()):
            self.asset_detail_page_objects.click_resume_draft_frame()

        if self.do_is_displayed(self.send_asset_page_objects.send_button()):
            self.send_asset_page_objects.click_send_button()

        if is_native_auth_enabled:
            self.enter_native_password()

        if self.do_is_displayed(self.receive_asset_page_objects.receive_asset_close_button()):
            self.receive_asset_page_objects.click_receive_asset_close_button()

        self.wallet_features.usb_sync()
