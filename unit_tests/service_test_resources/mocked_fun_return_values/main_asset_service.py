"""Mocked data for the main asset page service test"""
from __future__ import annotations

from rgb_lib import AssetCfa
from rgb_lib import AssetNia
from rgb_lib import AssetUda
from rgb_lib import Balance

from src.model.btc_model import BalanceResponseModel
from src.model.rgb_model import GetAssetResponseModel
from src.model.rgb_model import Media
from src.model.rgb_model import Token


mock_nia_asset = AssetNia(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
    asset_iface='RGB20',
    ticker='USDT',
    name='Tether',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=777000, future=777000, spendable=777000,
    ),
    media=None,
)

mock_uda_asset = AssetUda(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
    asset_iface='RGB20',
    ticker='UNI',
    name='Unique',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=777000, future=777000, spendable=777000,
    ),
    token=Token(
        index=0,
        ticker='TKN',
        name='Token',
        details='token details',
        embedded_media=True,
        media=Media(
            file_path='/path/to/media',
            mime='text/plain',
            digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
            hex='0x00',
        ),
        attachments={
            '0': Media(
                file_path='path/to/attachment0',
                mime='text/plain',
                digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
                hex='0x00',
            ),
            '1': Media(
                file_path='path/to/attachment1',
                mime='image/png',
                digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
                hex='0x00',
            ),
        },
        reserves=False,
    ),
)

mock_cfa_asset = AssetCfa(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
    asset_iface='RGB20',
    name='Collectible',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=777000, future=777000, spendable=777000,
    ),
    media=Media(
        file_path='/path/to/media', mime='text/plain',
        digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
        hex=None,
    ),
)

mock_get_asset_response_model = GetAssetResponseModel(
    nia=[mock_nia_asset],
    cfa=[mock_cfa_asset],
    uda=[mock_uda_asset],
)

"""Mock Return Data Of Function - BtcRepository.get_btc_balance"""
mock_balance_response_data = BalanceResponseModel(
    vanilla=Balance(settled=777000, future=777000, spendable=777000),
    colored=Balance(settled=777000, future=777000, spendable=777000),
)


"""Mock Return Data - if is_exhausted_asset_enabled true"""

mock_nia_asset_exhausted_asset = AssetNia(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k333',
    asset_iface='RGB20',
    ticker='TTK',
    name='super man',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=0, future=0, spendable=0,
    ),
    media=None,
)

mock_uda_asset_exhausted_asset = AssetUda(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
    asset_iface='RGB20',
    ticker='UNI',
    name='Unique',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=0, future=0, spendable=0,
    ),
    token=Token(
        index=0,
        ticker='TKN',
        name='Token',
        details='token details',
        embedded_media=True,
        media=Media(
            file_path='/path/to/media',
            mime='text/plain',
            digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
            hex='0x00',
        ),
        attachments={
            '0': Media(
                file_path='path/to/attachment0',
                mime='text/plain',
                digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
                hex='0x00',
            ),
            '1': Media(
                file_path='path/to/attachment1',
                mime='image/png',
                digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
                hex='0x00',
            ),
        },
        reserves=False,
    ),
)

mock_cfa_asset_exhausted_asset = AssetCfa(
    asset_id='rgb:2dkSTbr-jFhznbPmo-TQafzswCN-av4gTsJjX-ttx6CNou5-M98k8Zd',
    asset_iface='RGB20',
    name='Collectible',
    details='asset details',
    precision=0,
    issued_supply=777,
    timestamp=1691160565,
    added_at=1691161979,
    balance=Balance(
        settled=0, future=0, spendable=0,
    ),
    media=Media(
        file_path='/path/to/media', mime='text/plain',
        digest='5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03',
        hex=None,
    ),
)


mock_get_asset_response_model_when_exhausted_asset = GetAssetResponseModel(
    nia=[mock_nia_asset, mock_nia_asset_exhausted_asset],
    cfa=[mock_cfa_asset, mock_cfa_asset_exhausted_asset],
    uda=[mock_uda_asset, mock_uda_asset_exhausted_asset],
)
