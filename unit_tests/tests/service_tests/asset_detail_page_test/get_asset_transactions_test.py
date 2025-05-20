# pylint: disable=redefined-outer-name, unused-argument, unused-import
"""Unit tests for get_asset_transactions method """
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.data.service.asset_detail_page_services import AssetDetailPageService
from src.model.rgb_model import AssetIdModel
from src.model.rgb_model import ListTransferAssetWithBalanceResponseModel
from src.model.rgb_model import ListTransfersRequestModel
from src.utils.custom_exception import CommonException
from src.utils.custom_exception import ServiceOperationException
from unit_tests.repository_fixture.rgb_repository_mock import mock_get_asset_balance
from unit_tests.repository_fixture.rgb_repository_mock import mock_list_transfers
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_asset_balance,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_asset_id,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_no_transaction,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_transaction_type_issuance,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_transaction_type_receive_blind,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_transaction_type_receive_witness,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_transaction_type_send,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_when_transaction_type_inValid,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_when_transaction_type_issuance,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_when_transaction_type_receive_blind,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_when_transaction_type_receive_witness,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_list_when_transaction_type_send,
)
from unit_tests.service_test_resources.mocked_fun_return_values.asset_detail_page_service import (
    mocked_data_no_transaction,
)

# Disable the redefined-outer-name warning as
# it's normal to pass mocked object in tests function
# pylint: disable=redefined-outer-name


@pytest.fixture
def mock_rgb_repository(mocker):
    """Mock RgbRepository"""
    return mocker.patch(
        'src.data.service.asset_detail_page_services.RgbRepository',
        autospec=True,
    )


def test_no_transaction(mock_list_transfers, mock_get_asset_balance):
    """case 1: When no transaction"""
    list_transaction_mock_object = mock_list_transfers(
        mocked_data_no_transaction,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )

    result = AssetDetailPageService.get_asset_transactions(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )
    assert not result.transfers
    assert result.asset_balance == mocked_data_list_no_transaction.asset_balance
    assert isinstance(result, ListTransferAssetWithBalanceResponseModel)


def test_transaction_type_send(mock_list_transfers, mock_get_asset_balance):
    """case 2: When transaction type issuence"""
    list_transaction_mock_object = mock_list_transfers(
        mocked_data_list_when_transaction_type_send.transfers,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )
    result = AssetDetailPageService.get_asset_transactions(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )

    # Verify the result structure
    assert isinstance(result, ListTransferAssetWithBalanceResponseModel)
    assert result.transfers == mocked_data_list_transaction_type_send.transfers
    assert result.asset_balance == mocked_data_list_transaction_type_send.asset_balance


def test_transaction_type_receive_blind(mock_list_transfers, mock_get_asset_balance):
    """case 2: When transaction type receive blind"""
    list_transaction_mock_object = mock_list_transfers(
        mocked_data_list_when_transaction_type_receive_blind.transfers,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )
    result = AssetDetailPageService.get_asset_transactions(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )

    # Verify the result structure
    assert isinstance(result, ListTransferAssetWithBalanceResponseModel)
    assert result.transfers == mocked_data_list_transaction_type_receive_blind.transfers
    assert result.asset_balance == mocked_data_list_transaction_type_receive_blind.asset_balance


def test_transaction_type_receive_witness(mock_list_transfers, mock_get_asset_balance):
    """case 2: When transaction type receive witness"""
    list_transaction_mock_object = mock_list_transfers(
        mocked_data_list_when_transaction_type_receive_witness.transfers,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )
    result = AssetDetailPageService.get_asset_transactions(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )

    # Verify the result structure
    assert isinstance(result, ListTransferAssetWithBalanceResponseModel)
    assert result.transfers == mocked_data_list_transaction_type_receive_witness.transfers
    assert result.asset_balance == mocked_data_list_transaction_type_receive_witness.asset_balance


def test_transaction_type_receive_issuence(mock_list_transfers, mock_get_asset_balance):
    """case 2: When transaction type receive issuance"""
    list_transaction_mock_object = mock_list_transfers(
        mocked_data_list_when_transaction_type_issuance.transfers,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )
    result = AssetDetailPageService.get_asset_transactions(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )

    # Verify the result structure
    assert isinstance(result, ListTransferAssetWithBalanceResponseModel)
    assert result.transfers == mocked_data_list_transaction_type_issuance.transfers
    assert result.asset_balance == mocked_data_list_transaction_type_issuance.asset_balance


def test_transaction_type_invalid(mock_list_transfers, mock_get_asset_balance):
    """case 6: When transaction type not valid"""
    # Configure mock_list_payment to raise exception before it's called

    list_transaction_mock_object = mock_list_transfers(
        mocked_data_list_when_transaction_type_inValid.transfers,
    )
    asset_balance_mock_object = mock_get_asset_balance(
        mocked_data_asset_balance,
    )

    # Execute the function under test and expect CommonException instead
    with pytest.raises(CommonException) as exc_info:
        AssetDetailPageService.get_asset_transactions(
            ListTransfersRequestModel(asset_id=mocked_data_asset_id),
        )

    list_transaction_mock_object.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )
    asset_balance_mock_object.assert_called_once_with(
        AssetIdModel(asset_id=mocked_data_asset_id),
    )

    # Assert the exception message is as expected
    assert str(exc_info.value) == 'Unknown transaction type'


def test_list_transfers_error(mocker, mock_rgb_repository):
    """case 7: When RgbRepository.list_transfers raises an error"""
    # Configure mock to raise an exception
    mock_rgb_repository.list_transfers.side_effect = ServiceOperationException(
        'Test error',
    )

    # Execute the function under test and expect CommonException
    with pytest.raises(CommonException) as exc_info:
        AssetDetailPageService.get_asset_transactions(
            ListTransfersRequestModel(asset_id=mocked_data_asset_id),
        )

    # Verify the mock was called
    mock_rgb_repository.list_transfers.assert_called_once_with(
        ListTransfersRequestModel(asset_id=mocked_data_asset_id),
    )

    # Verify other mocks were not called
    mock_rgb_repository.get_asset_balance.assert_not_called()

    # Assert the exception message
    assert str(exc_info.value) == 'Test error'
