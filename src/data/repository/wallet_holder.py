import rgb_lib

from src.model.common_operation_model import InitResponseModel

class WalletHolder:
    _wallet: rgb_lib.Wallet = None
    _online: rgb_lib.Online = None
    _init_response: InitResponseModel = None

    @classmethod
    def set_wallet(cls, wallet: rgb_lib.Wallet):
        cls._wallet = wallet

    @classmethod
    def get_wallet(cls) -> rgb_lib.Wallet:
        if cls._wallet is None:
            raise RuntimeError("Wallet not initialized yet")
        return cls._wallet

    @classmethod
    def set_online(cls, online: rgb_lib.Online):
        cls._online = online

    @classmethod
    def get_online(cls) -> rgb_lib.Online:
        if cls._online is None:
            raise RuntimeError("Online object not initialized yet")
        return cls._online

    @classmethod
    def set_init_response(cls, response: InitResponseModel):
        cls._init_response = response

    @classmethod
    def get_init_response(cls) -> InitResponseModel:
        if cls._init_response is None:
            raise RuntimeError("Init response not set yet")
        return cls._init_response
