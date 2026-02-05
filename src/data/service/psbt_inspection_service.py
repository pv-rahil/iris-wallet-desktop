"""Service module for PSBT inspection and display data processing.

This service handles all business logic for processing PSBT inspection results
and operation context, producing UI-ready display data for the view layer.
"""
# pylint: disable=broad-except
from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from src.data.repository.rgb_repository import RgbRepository
from src.model.psbt_inspection_model import OperationContextModel
from src.model.psbt_inspection_model import PsbtDisplayDataModel
from src.model.psbt_inspection_model import PsbtInspectionResponseModel
from src.model.psbt_inspection_model import RgbInspectionResponseModel
from src.utils.constant import IRIS_WALLET_TRANSLATIONS_CONTEXT
from src.utils.custom_exception import CommonException
from src.utils.handle_exception import handle_exceptions


class PsbtInspectionService:
    """Service for processing PSBT inspection results into UI-ready data.

    This service follows the same pattern as AssetDetailPageService:
    - Calls repository methods directly
    - Processes raw results into typed response models
    - Returns clean model objects for ViewModel/View
    """

    TRANSFER_TYPE_FALLBACKS: dict[str, str] = {
        'internal': 'Internal',
        'btc_transfer': 'BTC transfer',
        'inflation': 'Inflation',
        'asset_transfer': 'Asset transfer',
    }

    @staticmethod
    def wrap_to_two_lines(text: str, first_line_chars: int = 34) -> str:
        """Force a two-line display by inserting a newline near the middle."""
        if not isinstance(text, str):
            return str(text)
        if len(text) <= first_line_chars:
            return text
        return text[:first_line_chars] + '\n' + text[first_line_chars:]

    @staticmethod
    def get_transfer_type_display(transfer_type: str | None) -> str:
        """Get translated display text for a transfer type."""
        if transfer_type is None:
            return ''

        translated = QCoreApplication.translate(
            IRIS_WALLET_TRANSLATIONS_CONTEXT, transfer_type,
        )
        if translated and translated != transfer_type:
            return translated

        return PsbtInspectionService.TRANSFER_TYPE_FALLBACKS.get(transfer_type, transfer_type)

    @staticmethod
    def inspect_psbt(psbt: str) -> PsbtInspectionResponseModel | CommonException:
        """Inspect PSBT and return processed response model.

        Calls RgbRepository.inspect_psbt and processes the result.

        Args:
            psbt: The PSBT string to inspect.

        Returns:
            PsbtInspectionResponseModel with processed data, or CommonException on error.
        """
        try:
            raw_result = RgbRepository.inspect_psbt(psbt)

            if raw_result is None:
                return PsbtInspectionResponseModel()

            txid = raw_result.txid if raw_result.txid else ''
            fee_sat = raw_result.fee_sat
            sig_count = raw_result.signature_count if raw_result.signature_count else 0

            fee_display = ''
            if isinstance(fee_sat, int) and fee_sat >= 0:
                fee_display = f'{fee_sat:,} sats'

            return PsbtInspectionResponseModel(
                txid=txid,
                txid_display=PsbtInspectionService.wrap_to_two_lines(txid),
                fee_sats=fee_sat,
                fee_display=fee_display,
                signature_count=sig_count,
                is_valid=True,
            )

        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def inspect_rgb_transfer(
        consignment_paths: list[str],
        psbt: str,
        entropy: int,
    ) -> RgbInspectionResponseModel | CommonException:
        """Inspect RGB transfer and return processed response model.

        Calls RgbRepository.inspect_rgb_transfer and processes the result.

        Args:
            consignment_paths: List of consignment file paths.
            psbt: The PSBT string.
            entropy: The entropy value.

        Returns:
            RgbInspectionResponseModel with processed data, or CommonException on error.
        """
        try:
            raw_result = RgbRepository.inspect_rgb_transfer(consignment_paths, psbt, entropy)

            if raw_result is None:
                return RgbInspectionResponseModel()

            operations = raw_result.operations if raw_result.operations else None
            if not operations:
                return RgbInspectionResponseModel()

            op_info = operations[0]
            asset_id = op_info.asset_id if op_info.asset_id else None

            send_amount = 0
            inflation_amount = 0

            transitions = op_info.transitions if op_info.transitions else []
            for transition in transitions:
                outputs = transition.outputs if transition.outputs else []
                for output in outputs:
                    assignment = output.assignment if output.assignment else None
                    if assignment and assignment.is_FUNGIBLE():
                        amt = assignment.amount if assignment.amount else 0
                        inflation_amount += amt
                        is_ours = output.is_ours if output.is_ours is not None else True
                        if not is_ours:
                            send_amount += amt

            amount_value = send_amount if send_amount > 0 else inflation_amount
            amount_display = f'{amount_value:,}' if amount_value > 0 else None

            return RgbInspectionResponseModel(
                asset_id=str(asset_id) if asset_id else None,
                asset_id_display=PsbtInspectionService.wrap_to_two_lines(str(asset_id)) if asset_id else None,
                send_amount=send_amount,
                inflation_amount=inflation_amount,
                amount_display=amount_display,
            )

        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def classify_transfer_type(operation) -> str | None:
        """Classify the transfer type from an operation object."""
        if operation is None:
            return None

        names: list[str] = []

        if operation.details is not None:
            names.append(type(operation.details).__name__)

        names.append(type(operation).__name__)

        for name in names:
            if 'CreateUtxo' in name or 'CreateUtxos' in name or 'CREATE_UTXOS' in name:
                return 'internal'
            if 'SendBtc' in name or 'SEND_BTC' in name:
                return 'btc_transfer'
            if 'Inflation' in name or 'INFLATION' in name or 'Issue' in name or 'ISSUE' in name:
                return 'inflation'
            if 'Send' in name and 'Btc' not in name and 'SEND_' in name:
                return 'asset_transfer'

        return None

    @staticmethod
    def extract_operation_context(operation) -> OperationContextModel:
        """Extract and process operation context into a typed model."""
        if operation is None:
            return OperationContextModel()

        details = operation.details
        transfer_type = PsbtInspectionService.classify_transfer_type(operation)

        if details is None:
            return OperationContextModel(
                transfer_type=transfer_type,
                transfer_type_display=PsbtInspectionService.get_transfer_type_display(transfer_type),
                psbt=operation.psbt if operation.psbt else None,
            )

        return OperationContextModel(
            asset_id=details.asset_id if details.asset_id else None,
            amount=details.amount if details.amount else None,
            min_confirmations=details.min_confirmations if details.min_confirmations else None,
            consignment_paths=details.consignment_paths if details.consignment_paths else None,
            entropy=details.entropy if details.entropy else None,
            transfer_type=transfer_type,
            transfer_type_display=PsbtInspectionService.get_transfer_type_display(transfer_type),
            psbt=operation.psbt if operation.psbt else None,
        )

    @staticmethod
    def build_display_data(
        psbt_response: PsbtInspectionResponseModel,
        operation_context: OperationContextModel | None = None,
        rgb_response: RgbInspectionResponseModel | None = None,
    ) -> PsbtDisplayDataModel:
        """Build complete display data from processed responses."""
        has_consignment = bool(operation_context and operation_context.consignment_paths)
        has_inflation_fields = operation_context and any([
            operation_context.asset_id is not None,
            operation_context.amount is not None,
            operation_context.min_confirmations is not None,
        ])
        is_btc_only = not has_consignment and not has_inflation_fields and rgb_response is None
        is_inflation = operation_context and operation_context.transfer_type == 'inflation'

        # Determine asset_id source
        asset_id = None
        asset_id_display = None
        if rgb_response and rgb_response.asset_id:
            asset_id = rgb_response.asset_id
            asset_id_display = rgb_response.asset_id_display
        elif operation_context and operation_context.asset_id:
            asset_id = operation_context.asset_id
            asset_id_display = PsbtInspectionService.wrap_to_two_lines(operation_context.asset_id)

        # Determine amount source
        amount = None
        amount_display = None
        if rgb_response and rgb_response.amount_display:
            amount = rgb_response.send_amount or rgb_response.inflation_amount
            amount_display = rgb_response.amount_display
        elif operation_context and operation_context.amount:
            amount = operation_context.amount
            amount_display = f'{operation_context.amount:,}'

        # Transfer type
        transfer_type = operation_context.transfer_type if operation_context else None
        transfer_type_display = operation_context.transfer_type_display if operation_context else ''

        return PsbtDisplayDataModel(
            txid=psbt_response.txid,
            txid_display=psbt_response.txid_display,
            fee_sats=psbt_response.fee_sats,
            fee_display=psbt_response.fee_display,
            signature_count=psbt_response.signature_count,
            is_valid=psbt_response.is_valid,
            transfer_type=transfer_type,
            transfer_type_display=transfer_type_display,
            asset_id=asset_id,
            asset_id_display=asset_id_display,
            amount=amount,
            amount_display=amount_display,
            min_confirmations=operation_context.min_confirmations if operation_context else None,
            show_asset_tile=bool(asset_id),
            show_amount_tile=bool(amount and amount > 0),
            show_destination_tile=False,
            show_fee_tile=bool(psbt_response.fee_sats is not None and psbt_response.fee_sats >= 0),
            show_type_tile=bool(transfer_type),
            show_minconf_tile=bool(operation_context and operation_context.min_confirmations is not None),
            is_btc_only=is_btc_only,
            is_inflation_context=bool(is_inflation or (has_inflation_fields and not has_consignment)),
        )
