# pylint: disable=redefined-outer-name,unused-argument, protected-access
"""Unit tests for `MultisigSetupService`."""
from __future__ import annotations

from unittest.mock import MagicMock

from src.data.service.multisig_setup_service import MultisigSetupService
from src.model.common_operation_model import CosignerDataResult
from src.model.common_operation_model import ThresholdValidationResult
from src.model.enums.enums_model import KeyStorageType


def test_validate_threshold_valid():
    """validate_threshold should return valid result for correct values."""
    result = MultisigSetupService.validate_threshold(required=2, total=3)
    assert result.is_valid is True
    assert result.required == 2
    assert result.total == 3
    assert result.error_message is None


def test_validate_threshold_total_too_low():
    """validate_threshold should fail when total < 2."""
    result = MultisigSetupService.validate_threshold(required=1, total=1)
    assert result.is_valid is False
    assert result.error_message == 'Total signers must be between 2 and 15'


def test_validate_threshold_total_too_high():
    """validate_threshold should fail when total > 15."""
    result = MultisigSetupService.validate_threshold(required=2, total=16)
    assert result.is_valid is False
    assert result.error_message == 'Total signers must be between 2 and 15'


def test_validate_threshold_required_too_low():
    """validate_threshold should fail when required < 2."""
    result = MultisigSetupService.validate_threshold(required=1, total=3)
    assert result.is_valid is False
    assert result.error_message == 'Required signatures must be between 2 and 3'


def test_validate_threshold_required_exceeds_total():
    """validate_threshold should fail when required > total."""
    result = MultisigSetupService.validate_threshold(required=4, total=3)
    assert result.is_valid is False
    assert result.error_message == 'Required signatures must be between 2 and 3'


def test_validate_threshold_boundary_values():
    """validate_threshold should accept boundary values (2, 2) and (15, 15)."""
    result_min = MultisigSetupService.validate_threshold(required=2, total=2)
    assert result_min.is_valid is True

    result_max = MultisigSetupService.validate_threshold(required=15, total=15)
    assert result_max.is_valid is True


def test_parse_cosigner_string_empty():
    """parse_cosigner_string should return invalid for empty string."""
    result = MultisigSetupService.parse_cosigner_string('')
    assert result.is_valid is False
    assert result.master_fingerprint == ''
    assert result.account_xpub_vanilla == ''
    assert result.account_xpub_colored == ''


def test_parse_cosigner_string_whitespace():
    """parse_cosigner_string should handle whitespace-only input."""
    result = MultisigSetupService.parse_cosigner_string('   ')
    assert result.is_valid is False


def test_parse_cosigner_string_invalid_format(mocker):
    """parse_cosigner_string should return invalid for malformed string."""
    mock_cosigner = mocker.patch(
        'src.data.service.multisig_setup_service.Cosigner',
    )
    mock_cosigner.side_effect = Exception('Invalid format')

    result = MultisigSetupService.parse_cosigner_string('invalid_string')
    assert result.is_valid is False


def test_parse_cosigner_string_valid(mocker):
    """parse_cosigner_string should parse valid cosigner string."""
    mock_data = MagicMock()
    mock_data.master_fingerprint = 'ABCD1234'
    mock_data.account_xpub_vanilla = 'xpub_vanilla_test'
    mock_data.account_xpub_colored = 'xpub_colored_test'
    mock_data.vanilla_keychain = 0

    mock_cosigner = mocker.patch(
        'src.data.service.multisig_setup_service.Cosigner',
    )
    mock_cosigner.return_value.cosigner_data.return_value = mock_data

    result = MultisigSetupService.parse_cosigner_string(
        'valid_cosigner_string',
    )
    assert result.is_valid is True
    assert result.master_fingerprint == 'ABCD1234'
    assert result.account_xpub_vanilla == 'xpub_vanilla_test'
    assert result.account_xpub_colored == 'xpub_colored_test'
    assert result.vanilla_keychain == 0


def test_parse_cosigner_string_with_keychain(mocker):
    """parse_cosigner_string should handle non-zero keychain."""
    mock_data = MagicMock()
    mock_data.master_fingerprint = 'ABCD1234'
    mock_data.account_xpub_vanilla = 'xpub_vanilla_test'
    mock_data.account_xpub_colored = 'xpub_colored_test'
    mock_data.vanilla_keychain = 1

    mock_cosigner = mocker.patch(
        'src.data.service.multisig_setup_service.Cosigner',
    )
    mock_cosigner.return_value.cosigner_data.return_value = mock_data

    result = MultisigSetupService.parse_cosigner_string(
        'valid_cosigner_string',
    )
    assert result.vanilla_keychain == 1


def test_generate_cosigner_string_missing_fields():
    """generate_cosigner_string should return None if required fields missing."""
    result = MultisigSetupService.generate_cosigner_string(
        master_fp='',
        account_xpub_vanilla='xpub_v',
        account_xpub_colored='xpub_c',
    )
    assert result is None

    result = MultisigSetupService.generate_cosigner_string(
        master_fp='fp',
        account_xpub_vanilla='',
        account_xpub_colored='xpub_c',
    )
    assert result is None


def test_generate_cosigner_string_success(mocker):
    """generate_cosigner_string should generate valid string."""
    mock_cosigner = mocker.patch(
        'src.data.service.multisig_setup_service.Cosigner',
    )
    mock_cosigner.from_data.return_value.cosigner_string.return_value = 'generated_cosigner_string'

    result = MultisigSetupService.generate_cosigner_string(
        master_fp='ABCD1234',
        account_xpub_vanilla='xpub_vanilla',
        account_xpub_colored='xpub_colored',
        keychain=0,
    )
    assert result == 'generated_cosigner_string'


def test_generate_cosigner_string_exception(mocker):
    """generate_cosigner_string should return None on exception."""
    mock_cosigner = mocker.patch(
        'src.data.service.multisig_setup_service.Cosigner',
    )
    mock_cosigner.from_data.side_effect = Exception('Generation failed')

    result = MultisigSetupService.generate_cosigner_string(
        master_fp='ABCD1234',
        account_xpub_vanilla='xpub_vanilla',
        account_xpub_colored='xpub_colored',
    )
    assert result is None


def test_truncate_text_short():
    """truncate_text should return original text if under max length."""
    text = 'short text'
    result = MultisigSetupService.truncate_text(text, max_length=40)
    assert result == text


def test_truncate_text_long():
    """truncate_text should truncate long text with ellipsis."""
    text = 'a' * 50
    result = MultisigSetupService.truncate_text(text, max_length=40)
    assert len(result) == 53  # 25 + 3 + 25
    assert '...' in result


def test_truncate_text_empty():
    """truncate_text should handle empty string."""
    result = MultisigSetupService.truncate_text('', max_length=40)
    assert result == ''


def test_check_duplicate_cosigners_no_duplicates():
    """check_duplicate_cosigners should return False when no duplicates."""
    rows = [
        {'index': 0, 'vanilla_xpub_str': 'xpub1'},
        {'index': 1, 'vanilla_xpub_str': 'xpub2'},
    ]
    has_dup, dup_idx = MultisigSetupService.check_duplicate_cosigners(rows)
    assert has_dup is False
    assert dup_idx is None


def test_check_duplicate_cosigners_with_duplicates():
    """check_duplicate_cosigners should detect duplicates."""
    rows = [
        {'index': 0, 'vanilla_xpub_str': 'xpub1'},
        {'index': 1, 'vanilla_xpub_str': 'xpub1'},
    ]
    has_dup, dup_idx = MultisigSetupService.check_duplicate_cosigners(rows)
    assert has_dup is True
    assert dup_idx == 1


def test_check_duplicate_cosigners_empty():
    """check_duplicate_cosigners should handle empty list."""
    has_dup, dup_idx = MultisigSetupService.check_duplicate_cosigners([])
    assert has_dup is False
    assert dup_idx is None


def test_get_card_size_for_signers_two():
    """get_card_size_for_signers should return larger size for 2 signers."""
    min_size, max_size = MultisigSetupService.get_card_size_for_signers(2)
    assert min_size == 770
    assert max_size == 520


def test_get_card_size_for_signers_more():
    """get_card_size_for_signers should return smaller size for >2 signers."""
    min_size, max_size = MultisigSetupService.get_card_size_for_signers(3)
    assert min_size == 770
    assert max_size == 640


def test_save_watch_only_data_missing_fields():
    """save_watch_only_data should return False if required fields missing."""
    result = MultisigSetupService.save_watch_only_data(
        fp='', keychain='0', vanilla='xpub_v', colored='xpub_c',
    )
    assert result is False


def test_save_watch_only_data_success(mocker):
    """save_watch_only_data should save data to local_store."""
    mock_local_store = mocker.patch(
        'src.data.service.multisig_setup_service.local_store',
    )

    result = MultisigSetupService.save_watch_only_data(
        fp='ABCD1234',
        keychain='0',
        vanilla='xpub_vanilla',
        colored='xpub_colored',
    )
    assert result is True
    assert mock_local_store.set_value.call_count == 4


def test_get_wallet_review_data(mocker):
    """get_wallet_review_data should return dict from local_store."""
    mock_local_store = mocker.patch(
        'src.data.service.multisig_setup_service.local_store',
    )
    mock_local_store.get_value.side_effect = ['FP', 'vanilla', 'colored', '0']

    result = MultisigSetupService.get_wallet_review_data()
    assert result['master_fingerprint'] == 'FP'
    assert result['account_xpub_vanilla'] == 'vanilla'
    assert result['account_xpub_colored'] == 'colored'
    assert result['keychain'] == '0'


def test_get_wallet_review_data_empty(mocker):
    """get_wallet_review_data should handle None values."""
    mock_local_store = mocker.patch(
        'src.data.service.multisig_setup_service.local_store',
    )
    mock_local_store.get_value.return_value = None

    result = MultisigSetupService.get_wallet_review_data()
    assert result['master_fingerprint'] == ''
    assert result['account_xpub_vanilla'] == ''
    assert result['keychain'] == '0'


def test_is_hardware_wallet_true(mocker):
    """is_hardware_wallet should return True when hardware wallet."""
    mock_setting = mocker.patch(
        'src.data.service.multisig_setup_service.SettingRepository',
    )
    mock_setting.get_key_storage_type.return_value = KeyStorageType.HARDWARE_WALLET

    result = MultisigSetupService.is_hardware_wallet()
    assert result is True


def test_is_hardware_wallet_false(mocker):
    """is_hardware_wallet should return False when not hardware wallet."""
    mock_setting = mocker.patch(
        'src.data.service.multisig_setup_service.SettingRepository',
    )
    mock_setting.get_key_storage_type.return_value = KeyStorageType.ON_DEVICE

    result = MultisigSetupService.is_hardware_wallet()
    assert result is False


def test_threshold_validation_result_model():
    """ThresholdValidationResult should work as pydantic model."""
    result = ThresholdValidationResult(
        is_valid=True,
        required=2,
        total=3,
        error_message=None,
    )
    assert result.is_valid is True
    assert result.model_dump() == {
        'is_valid': True,
        'required': 2,
        'total': 3,
        'error_message': None,
    }


def test_cosigner_data_result_model():
    """CosignerDataResult should work as pydantic model."""
    result = CosignerDataResult(
        master_fingerprint='ABCD',
        account_xpub_vanilla='xpub_v',
        account_xpub_colored='xpub_c',
        vanilla_keychain=0,
        is_valid=True,
    )
    assert result.is_valid is True
    assert result.model_dump()['master_fingerprint'] == 'ABCD'


def test_generate_wallet_keys_already_exists(mocker):
    """generate_wallet_keys should skip if mnemonic file exists."""
    mock_os = mocker.patch(
        'src.data.service.multisig_setup_service.os.path.exists',
    )
    mock_os.return_value = True

    result = MultisigSetupService.generate_wallet_keys('password123')
    assert result == {'exists': True}


def test_generate_wallet_keys_success(mocker):
    """generate_wallet_keys should generate and save keys."""
    mock_os = mocker.patch(
        'src.data.service.multisig_setup_service.os.path.exists',
    )
    mock_os.return_value = False

    mock_keys = MagicMock()
    mock_keys.master_fingerprint = 'FP1234'
    mock_keys.xpub = 'xpub_test'
    mock_keys.account_xpub_vanilla = 'vanilla_xpub'
    mock_keys.account_xpub_colored = 'colored_xpub'
    mock_keys.mnemonic = 'mnemonic words'

    mock_repo = mocker.patch(
        'src.data.service.multisig_setup_service.CommonOperationRepository.init',
    )
    mock_repo.return_value = mock_keys

    mock_setting = mocker.patch(
        'src.data.service.multisig_setup_service.SettingRepository',
    )
    mock_setting.get_wallet_network.return_value = 'regtest'

    mock_mnemonic_store = mocker.patch(
        'src.data.service.multisig_setup_service.mnemonic_store',
    )
    mock_mnemonic_store.encrypt.return_value = 'encrypted_mnemonic'

    result = MultisigSetupService.generate_wallet_keys('password123')

    assert result['exists'] is False
    assert result['master_fingerprint'] == 'FP1234'
    assert result['xpub'] == 'xpub_test'


def test_generate_wallet_keys_exception(mocker):
    """generate_wallet_keys should return None on exception."""
    mock_os = mocker.patch(
        'src.data.service.multisig_setup_service.os.path.exists',
    )
    mock_os.return_value = False

    mock_setting = mocker.patch(
        'src.data.service.multisig_setup_service.SettingRepository',
    )
    mock_setting.get_wallet_network.side_effect = Exception('Network error')

    result = MultisigSetupService.generate_wallet_keys('password123')
    assert result is None


def test_save_cosigners_data_success(mocker):
    """save_cosigners_data should parse and save cosigner data."""
    mock_parse = mocker.patch(
        'src.data.service.multisig_setup_service.MultisigSetupService.parse_cosigner_string',
    )
    mock_parse.return_value = CosignerDataResult(
        master_fingerprint='FP1',
        account_xpub_vanilla='v1',
        account_xpub_colored='c1',
        vanilla_keychain=0,
        is_valid=True,
    )

    mock_setting = mocker.patch(
        'src.data.service.multisig_setup_service.SettingRepository',
    )

    rows = [
        {'index': 0, 'string': 'cosigner_str_1'},
        {'index': 1, 'string': 'cosigner_str_2'},
    ]

    result = MultisigSetupService.save_cosigners_data(rows)
    assert result is True
    mock_setting.set_cosigners.assert_called_once()


def test_save_cosigners_data_empty_string(mocker):
    """save_cosigners_data should return False for empty string."""
    rows = [{'index': 0, 'string': ''}]
    result = MultisigSetupService.save_cosigners_data(rows)
    assert result is False


def test_save_cosigners_data_invalid_cosigner(mocker):
    """save_cosigners_data should return False for invalid cosigner."""
    mock_parse = mocker.patch(
        'src.data.service.multisig_setup_service.MultisigSetupService.parse_cosigner_string',
    )
    mock_parse.return_value = CosignerDataResult(
        master_fingerprint='',
        account_xpub_vanilla='',
        account_xpub_colored='',
        vanilla_keychain=0,
        is_valid=False,
    )

    rows = [{'index': 0, 'string': 'invalid_str'}]
    result = MultisigSetupService.save_cosigners_data(rows)
    assert result is False
