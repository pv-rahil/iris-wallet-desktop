"""Contain mocked function return data"""
from __future__ import annotations

from src.model.enums.enums_model import NetworkEnumModel
from src.model.rgb_faucet_model import BriefAssetInfo
from src.model.rgb_faucet_model import ConfigWalletResponse
from src.model.rgb_faucet_model import ListAssetResponseModel
from src.model.rgb_faucet_model import ListAvailableAsset
from src.model.rgb_faucet_model import ListFaucetAssetBalance
from src.model.rgb_faucet_model import ListFaucetAssetDetail
from src.model.rgb_faucet_model import RequestAssetResponseModel
from src.model.rgb_model import RgbInvoiceDataResponseModel


# Mocked network
mocked_network: NetworkEnumModel = NetworkEnumModel('regtest')

# When asset available
mocked_asset_list: ListAssetResponseModel = ListAssetResponseModel(
    assets={
        'rgb:2dNB6Sm-p8wKGMMkw-NmTWJ239m-GFLQvPS7n-pKKChp1mu-6921rgB': ListFaucetAssetDetail(
            balance=ListFaucetAssetBalance(
                future=1000, settled=1000, spendable=1000,
            ),
            details=None,
            name='fungible token',
            precision=0,
            ticker='FFA',
        ),
        'rgb:BX28km3-TB9BtPCcS-ftySPiDAq-YrH36uvtW-cXxGKNhxA-CcTRpv': ListFaucetAssetDetail(
            balance=ListFaucetAssetBalance(
                future=1000, settled=1000, spendable=1000,
            ),
            details=None,
            name='fungible token2',
            precision=0,
            ticker='FFA2',
        ),
    },
)

# When asset not available
mocked_asset_list_no_asset: ListAssetResponseModel = ListAssetResponseModel(
    assets={},
)

mocked_response_of_list_asset_faucet: ListAvailableAsset = ListAvailableAsset(
    faucet_assets=[
        BriefAssetInfo(
            asset_name='fungible token',
            asset_id='rgb:2dNB6Sm-p8wKGMMkw-NmTWJ239m-GFLQvPS7n-pKKChp1mu-6921rgB',
        ),
        BriefAssetInfo(
            asset_name='fungible token2',
            asset_id='rgb:BX28km3-TB9BtPCcS-ftySPiDAq-YrH36uvtW-cXxGKNhxA-CcTRpv',
        ),
    ],
)
# Invoice response data
invoice_response_data = {
    'recipient_id': 'utxob:2FZsSuk-iyVQLVuU4-Gc6J4qkE8-mLS17N4jd-MEx6cWz9F-MFkyE1n',
    'invoice': 'rgb:~/~/utxob:2FZsSuk-iyVQLVuU4-Gc6J4qkE8-mLS17N4jd-MEx6cWz9F-MFkyE1n?expiry=1695811760&endpoints=rpc://127.0.0.1:3000/json-rpc',
    'expiration_timestamp': 1695811760,
    'batch_transfer_idx': 123,
}

mocked_data_invoice_response: RgbInvoiceDataResponseModel = RgbInvoiceDataResponseModel(
    **invoice_response_data,
)
# config response data
config_response = {
    'groups': {
        'group': {
            'distribution': {
                'mode': 1,
            },
            'label': 'asset group',
            'requests_left': 1,
        },
    },
    'name': 'regtest faucet',
}
# When no keys
config_response_none_case = {
    'groups': {},
    'name': 'regtest faucet',
}
mocked_data_config_response: ConfigWalletResponse = ConfigWalletResponse(
    **config_response,
)
mocked_data_config_response_none_case: ConfigWalletResponse = ConfigWalletResponse(
    **config_response_none_case,
)
# Request asset response data
request_asset = {
    'asset': {
        'amount': 3,
        'asset_id': 'rgb:2GkcLyj-NPETgwFhZ-b8SKoea7w-QzYauayiX-NoFLP6BHb-aRGaitC',
        'details': None,
        'name': 'fungible token',
        'precision': 0,
        'schema': 'NIA',
        'ticker': 'FFA',
    },
    'distribution': {
        'mode': 1,
    },
}
mocked_data_request_asset: RequestAssetResponseModel = RequestAssetResponseModel(
    **request_asset,
)
