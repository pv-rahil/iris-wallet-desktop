"""
Mocked data for the common operation service test
"""
from __future__ import annotations

from src.model.common_operation_model import InitResponseModel
from src.model.common_operation_model import NetworkInfoResponseModel
from src.model.common_operation_model import UnlockResponseModel


mnemonic = {
    'mnemonic': 'skill lamp please gown put season degree collect decline account monitor insane',
}

# Mocked response of init api
mocked_data_init_api_response = InitResponseModel(**mnemonic)

network_info = {
    'network': 'Regtest',
    'height': 805434,
}

another_network_info = {
    'network': 'Testnet',
    'height': 805434,
}

# Mocked response of network info api
# When build network and node network same
mocked_network_info_api_res = NetworkInfoResponseModel(**network_info)
# when build network and ln node network diff
mocked_network_info_diff = NetworkInfoResponseModel(**another_network_info)
mocked_unlock_api_res = UnlockResponseModel(status=True)
mocked_password: str = 'Random@123'
