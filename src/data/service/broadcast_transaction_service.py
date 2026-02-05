# pylint: disable=too-few-public-methods
"""Service class for broadcast transaction operations"""
from __future__ import annotations

from rgb_lib import OperationResult
from rgb_lib import RespondToOperation

from src.data.repository.common_operations_repository import CommonOperationRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.service.psbt_inspection_service import PsbtInspectionService
from src.data.service.wallet_data_service import WalletDataService
from src.model.psbt_inspection_model import OperationContextModel
from src.model.psbt_inspection_model import PsbtInspectionResponseModel
from src.model.psbt_inspection_model import RgbInspectionResponseModel
from src.utils.custom_exception import CommonException
from src.utils.handle_exception import handle_exceptions


class BroadcastTransactionService:
    """
    Service class for broadcast transaction operations
    """

    @staticmethod
    def inspect_transaction(
        psbt_text: str, operation=None,
    ) -> tuple[PsbtInspectionResponseModel, OperationContextModel | None, RgbInspectionResponseModel | None]:
        """
        Inspects a transaction (PSBT) and returns detailed information.
        Handles both BTC and RGB inspections.
        """
        try:
            # 1. Inspect PSBT (BTC details)
            psbt_details = PsbtInspectionService.inspect_psbt(psbt_text)

            # 2. Extract Operation Context (if provided)
            operation_context = None
            rgb_details = None

            if operation is not None:
                operation_context = PsbtInspectionService.extract_operation_context(
                    operation,
                )

            # 3. Inspect RGB Transfer (if applicable)
            if operation_context and operation_context.consignment_paths:
                entropy = int(operation_context.entropy) if operation_context.entropy else 0
                rgb_details = PsbtInspectionService.inspect_rgb_transfer(
                    operation_context.consignment_paths,
                    psbt_text,
                    entropy,
                )

            return psbt_details, operation_context, rgb_details

        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def multisig_sign_and_post(unsigned_psbt: str, operation_idx: int | None) -> OperationResult:
        """
        Signs a PSBT and posts it back to the multisig bridge.
        """
        try:
            # 1. Sign PSBT
            signed_psbt = CommonOperationRepository.sign_psbt(unsigned_psbt)

            # 2. Ack with signed PSBT
            response = RespondToOperation.ACK(signed_psbt)
            if operation_idx is None:
                raise CommonException("Operation index missing for multisig post")

            result = RgbRepository.respond_to_operation(operation_idx, response)
            return result

        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def respond_nack(operation_idx: int | None) -> OperationResult:
        """
        Respond NACK to a multisig operation.
        """
        try:
            if operation_idx is None:
                raise CommonException("Operation index missing for NACK")
            
            response = RespondToOperation.NACK()
            result = RgbRepository.respond_to_operation(operation_idx, response)
            return result
        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def load_psbts(signed: bool) -> list[dict]:
        """
        Load list of PSBTs (signed or unsigned) from wallet data service.
        """
        try:
            wallet_service = WalletDataService.get_session()
            if wallet_service is not None:
                return wallet_service.list_psbt(signed)
            return []
        except Exception as exc:
            # Depending on how we want to handle this, we might log it or return empty
            # For now returning empty list as per original VM behavior safe-check
            return []
