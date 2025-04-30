from __future__ import annotations

import json
import os

import rgb_lib
from cryptography.fernet import Fernet

from src.model.common_operation_model import InitResponseModel
from src.utils.build_app_path import app_paths


class WalletHolder:
    _wallet: rgb_lib.Wallet = None
    _online: rgb_lib.Online = None
    _init_response = None

    _init_file_path = os.path.join(app_paths.app_path, 'wallet_init.dat')
    _encryption_key = b'xrMeekseyt4h5G9y_09SDjNBCuv1y1ljK1fYfN3Us3k='  # 32 bytes

    @classmethod
    def set_wallet(cls, wallet: rgb_lib.Wallet):
        cls._wallet = wallet

    @classmethod
    def get_wallet(cls) -> rgb_lib.Wallet:
        if cls._wallet is None:
            raise RuntimeError('Wallet not initialized yet')
        return cls._wallet

    @classmethod
    def set_online(cls, online: rgb_lib.Online):
        cls._online = online

    @classmethod
    def get_online(cls) -> rgb_lib.Online:
        if cls._online is None:
            raise RuntimeError('Online object not initialized yet')
        return cls._online

    @classmethod
    def set_init_response(cls, response: InitResponseModel):
        cls._init_response = response
        cls.save_init_response_to_file()  # Save whenever set manually

    @classmethod
    def get_init_response(cls) -> InitResponseModel:
        if cls._init_response is None:
            cls._load_init_response_from_file()

        if cls._init_response is None:
            raise RuntimeError('Init response not set and no saved file found')

        return cls._init_response

    @classmethod
    def save_init_response_to_file(cls):
        if cls._init_response is None:
            raise ValueError('Init response not set yet')

        data = cls._init_response.model_dump_json().encode('utf-8')
        fernet = Fernet(cls._encryption_key)
        encrypted = fernet.encrypt(data)

        with open(cls._init_file_path, 'wb') as file:
            file.write(encrypted)

    @classmethod
    def _load_init_response_from_file(cls):
        if not os.path.exists(cls._init_file_path):
            return  # Silent fail, will force re-init

        try:
            fernet = Fernet(cls._encryption_key)

            with open(cls._init_file_path, 'rb') as file:
                encrypted_data = file.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            json_data = json.loads(decrypted_data)

            cls._init_response = InitResponseModel(**json_data)
            print('Init response loaded from saved file.')

        except Exception as e:
            print(f"Error loading init file: {e}")
            cls._init_response = None  # Clean fail
