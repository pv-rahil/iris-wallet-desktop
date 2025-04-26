"""Service class to manage channel related thing when more then two api calls"""
from __future__ import annotations

from src.data.repository.btc_repository import BtcRepository
from src.data.repository.channels_repository import ChannelRepository
from src.data.repository.rgb_repository import RgbRepository
from src.data.repository.setting_card_repository import SettingCardRepository
from src.model.btc_model import BalanceResponseModel
from src.model.btc_model import EstimateFeeRequestModel
from src.model.btc_model import EstimateFeeResponse
from src.model.btc_model import UnspentsListResponseModel
from src.model.channels_model import OpenChannelResponseModel
from src.model.channels_model import OpenChannelsRequestModel
from src.model.rgb_model import CreateUtxosRequestModel
from src.model.setting_model import DefaultFeeRate
from src.utils.constant import MEDIUM_TRANSACTION_FEE_BLOCKS
from src.utils.constant import UTXO_SIZE_SAT_FOR_OPENING_CHANNEL
from src.utils.custom_exception import CommonException
from src.utils.handle_exception import handle_exceptions
from src.utils.logging import logger


class LnNodeChannelManagement:
    """This class contain ln node channel opening functionality"""
    @staticmethod
    def open_channel(open_channel_parameter: OpenChannelsRequestModel) -> OpenChannelResponseModel:
        """This method is responsibale to open a channel"""
        try:
            response: OpenChannelResponseModel = ChannelRepository.open_channel(
                open_channel_parameter,
            )
            return response
        except Exception as exc:
            return handle_exceptions(exc)

    @staticmethod
    def get_network_fee_for_channel_utxo(block_value: int = MEDIUM_TRANSACTION_FEE_BLOCKS) -> int:
        """
        Fetches the estimated fee rate from the Bitcoin network.
        If it fails or the fee rate is zero, the default fee rate from settings is used.

        Args:
            block_value (int): The number of blocks for fee estimation. Default is medium transaction fee blocks.

        Returns:
            int: The fee rate in sats/byte.
        """
        try:
            # Request fee estimation
            fee_response: EstimateFeeResponse = BtcRepository.estimate_fee(
                EstimateFeeRequestModel(blocks=block_value),
            )
            # Check if fee rate is valid
            if fee_response.fee_rate <= 0:
                default_fee_rate = LnNodeChannelManagement._get_default_fee_rate()
                logger.warning(
                    'Received 0 fee rate from estimate_fee API. Falling back to default fee rate: %s sats/byte.',
                    default_fee_rate,
                )
                return default_fee_rate

            logger.info(
                'Successfully fetched fee rate from API: %s sats/byte (blocks: %d).',
                fee_response.fee_rate, block_value,
            )
            return int(fee_response.fee_rate)

        except CommonException as exc:
            # Log detailed error information
            logger.error(
                'Failed to fetch fee rate due to %s: %s. Using default fee rate.',
                type(exc).__name__, str(exc),
            )
            default_fee_rate = LnNodeChannelManagement._get_default_fee_rate()
            logger.info(
                'Using default fee rate: %s sats/byte.',
                default_fee_rate,
            )
            return default_fee_rate

    @staticmethod
    def _get_default_fee_rate() -> int:
        """
        Retrieves the default fee rate from settings.

        Returns:
            int: The default fee rate in sats/byte.
        """
        default_fee_rate: DefaultFeeRate = SettingCardRepository.get_default_fee_rate()
        return default_fee_rate.fee_rate

    @staticmethod
    def create_utxo_for_channel(utxo_size):
        """Creates a UTXO for the Asset channel"""
        try:
            fee_rate = LnNodeChannelManagement.get_network_fee_for_channel_utxo()
            RgbRepository.create_utxo(
                CreateUtxosRequestModel(
                    size=utxo_size, fee_rate=fee_rate,
                ),
            )
        except CommonException as exc:
            handle_exceptions(exc)

    @staticmethod
    def _check_and_create_utxos_for_channel_opening() -> None:
        """
        Check if there are enough colorable UTXOs with no RGB allocations to open a channel.
        If not enough UTXOs are available, create additional UTXOs.

        Returns:
            bool: True if there are enough UTXOs or UTXOs were successfully created, False otherwise.
        """
        try:
            # Fetch the list of unspents (UTXOs) from the repository
            response: UnspentsListResponseModel = BtcRepository.list_unspents()
            # Filter UTXOs where colorable is True and there are no RGB allocations (empty list)
            # Iterate over the unspents and return True as soon as a match is found
            for unspent in response.unspents:
                if (
                    unspent
                    and unspent.utxo.colorable
                    and len(unspent.rgb_allocations) == 0
                    and unspent.utxo.btc_amount >= UTXO_SIZE_SAT_FOR_OPENING_CHANNEL
                ):
                    return
            logger_info_msg = f'Creating utxo for opening channel {
                UTXO_SIZE_SAT_FOR_OPENING_CHANNEL
            }'
            logger.info(logger_info_msg)
            balance: BalanceResponseModel = BtcRepository.get_btc_balance()
            if balance.vanilla.spendable < UTXO_SIZE_SAT_FOR_OPENING_CHANNEL:
                insufficient_sats = f'Insufficient balance: {
                    UTXO_SIZE_SAT_FOR_OPENING_CHANNEL
                } sats needed for channel opening, including transaction fees.'
                raise CommonException(insufficient_sats)
            # Create new UTXOs using the calculated amount
            RgbRepository.create_utxo(
                CreateUtxosRequestModel(
                    size=UTXO_SIZE_SAT_FOR_OPENING_CHANNEL,
                ),
            )
        except Exception as exc:
            raise exc
