# pylint: disable=redefined-outer-name,unused-argument, protected-access, invalid-name
"""Unit tests for `BroadcastTransactionService`.

Structured similarly to other service tests, focusing on logic coverage and
expected behaviors rather than just basic structural mocking.
"""
from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch
from rgb_lib import Operation
from src.data.service.broadcast_transaction_service import BroadcastTransactionService
from src.model.broadcast_transaction_model import PsbtDraftItem
from src.model.broadcast_transaction_model import PsbtParsed


def test_list_psbt_drafts_handles_missing_session_and_filters_invalid(mocker):
    """list_psbt_drafts should gracefully return [] if no session, or filter invalid rows otherwise."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )

    # Path 1: No session
    mock_get_session.return_value = None
    assert not BroadcastTransactionService.list_psbt_drafts(True)

    # Path 2: Valid session with mixed rows
    mock_session = MagicMock()
    mock_session.list_psbt.return_value = [
        {
            'id': 'valid_id', 'psbt': 'valid_psbt',
            'signed': 1, 'purpose': 'send_asset',
        },
        'invalid_row_type',
        {'id': 'another', 'psbt': 'another_psbt', 'signed': 0, 'purpose': None},
    ]
    mock_get_session.return_value = mock_session

    items = BroadcastTransactionService.list_psbt_drafts(True)
    assert len(items) == 2
    assert items[0].id == 'valid_id' and items[0].signed is True
    assert items[1].id == 'another' and items[1].signed is False


def test_selector_titles_formats_correctly():
    """selector_titles should correctly format titles with purpose and truncated IDs."""
    items = [
        PsbtDraftItem(
            id='1234567890123', psbt='x',
            signed=False, purpose='send_asset',
        ),
        PsbtDraftItem(id='', psbt='y', signed=True, purpose='inflation'),
        PsbtDraftItem(id='abc', psbt='z', signed=False, purpose=None),
    ]
    titles = BroadcastTransactionService.selector_titles(items)

    assert titles[0] == 'send_asset (12345678)'
    assert titles[1] == 'inflation'
    assert titles[2] == 'psbt (abc)'


def test_parse_psbt_input_normalization():
    """parse_psbt_input should accurately strip prefixes, purpose, and normalize whitespaces."""
    # Empty paths
    assert BroadcastTransactionService.parse_psbt_input(None).psbt == ''
    assert BroadcastTransactionService.parse_psbt_input('   ').purpose is None

    # Prefix without purpose
    p1 = BroadcastTransactionService.parse_psbt_input('psbt:cHNi...')
    assert p1.psbt == 'cHNi...' and p1.purpose is None

    # Prefix with purpose
    p2 = BroadcastTransactionService.parse_psbt_input(
        'psbt:send_asset:cHNi...',
    )
    assert p2.psbt == 'cHNi...' and p2.purpose == 'send_asset'

    # Multiline / space formatting
    p3 = BroadcastTransactionService.parse_psbt_input(' psbt:abc : cH \n Ni ')
    assert p3.psbt == 'cHNi' and p3.purpose == 'abc '


def test_resolve_purpose_precedence():
    """resolve_purpose should prioritize parsed purpose over selector fallback."""
    assert BroadcastTransactionService.resolve_purpose(
        PsbtParsed(
            psbt='', purpose='parsed_purpose',
        ), 'selector',
    ) == 'parsed_purpose'
    assert BroadcastTransactionService.resolve_purpose(
        PsbtParsed(psbt='', purpose=None), 'selector',
    ) == 'selector'
    assert BroadcastTransactionService.resolve_purpose(
        PsbtParsed(psbt='', purpose=None), None,
    ) is None


def test_action_key_resolves_correct_mode():
    """action_key should return 'sign' if broadcast is not allowed, or map purpose to keys."""
    assert BroadcastTransactionService.action_key(
        False, 'send_asset',
    ) == 'sign'
    assert BroadcastTransactionService.action_key(
        True, 'send_btc',
    ) == 'send_btc'
    assert BroadcastTransactionService.action_key(
        True, 'send_asset',
    ) == 'send_asset'
    assert BroadcastTransactionService.action_key(
        True, 'inflate_asset',
    ) == 'inflation'
    assert BroadcastTransactionService.action_key(
        True, 'inflation',
    ) == 'inflation'
    assert BroadcastTransactionService.action_key(
        True, 'random_purpose',
    ) == 'create_utxos'


def test_selected_purpose_bounds_check():
    """selected_purpose should guard against out-of-bounds indices."""
    items = [PsbtDraftItem(id='1', psbt='x', signed=False, purpose='test')]
    assert BroadcastTransactionService.selected_purpose(items, -1) is None
    assert BroadcastTransactionService.selected_purpose(items, 1) is None
    assert BroadcastTransactionService.selected_purpose(items, 0) == 'test'


def test_receive_page_name_for_signed_psbt(mocker):
    """receive_page_name_for_signed_psbt should resolve IEA secondary issuance if applicable."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )

    # Missing session fallback
    mock_get_session.return_value = None
    assert BroadcastTransactionService.receive_page_name_for_signed_psbt(
        'psbt',
    ) == 'NIA page'

    # Match in DB
    mock_session = MagicMock()
    mock_session.list_psbt.return_value = [
        'bad_row',
        {'psbt': 'psbt1', 'purpose': 'send_asset'},
        {'psbt': 'psbt2', 'purpose': 'inflate_asset'},
    ]
    mock_get_session.return_value = mock_session

    assert BroadcastTransactionService.receive_page_name_for_signed_psbt(
        'psbt1',
    ) == 'NIA page'
    assert BroadcastTransactionService.receive_page_name_for_signed_psbt(
        'psbt2',
    ) == 'IFA secondary issuance'
    assert BroadcastTransactionService.receive_page_name_for_signed_psbt(
        'psbt_unused',
    ) == 'NIA page'


def test_cleanup_secondary_draft_if_any_execution_paths(mocker):
    """cleanup_secondary_draft_if_any should appropriately target IFA secondary drafts."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_get_session.return_value = None

    # Fail early without session
    BroadcastTransactionService.cleanup_secondary_draft_if_any(
        'psbt', 'inflate_asset',
    )

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Bypass non-inflation
    BroadcastTransactionService.cleanup_secondary_draft_if_any(
        'psbt', 'send_asset',
    )
    mock_session.delete_secondary_draft_by_psbt.assert_not_called()

    # Delete by exact psbt match
    mock_session.delete_secondary_draft_by_psbt.return_value = True
    BroadcastTransactionService.cleanup_secondary_draft_if_any(
        'my_psbt', 'inflate_asset',
    )
    mock_session.delete_secondary_draft_by_psbt.assert_called_once_with(
        'my_psbt',
    )
    mock_session.get_latest_active_secondary_draft.assert_not_called()

    # Fallback to latest drafted ID
    mock_session.reset_mock()
    mock_session.delete_secondary_draft_by_psbt.return_value = False
    mock_session.get_latest_active_secondary_draft.return_value = {'id': '99'}

    BroadcastTransactionService.cleanup_secondary_draft_if_any(
        'psbt:inflation:my_psbt', None,
    )
    mock_session.delete_ifa_secondary_draft.assert_called_once_with(99)

    # Fallback with no active draft
    mock_session.reset_mock()
    mock_session.delete_secondary_draft_by_psbt.return_value = False
    mock_session.get_latest_active_secondary_draft.return_value = None
    BroadcastTransactionService.cleanup_secondary_draft_if_any(
        'my_psbt', 'inflate_asset',
    )
    mock_session.delete_ifa_secondary_draft.assert_not_called()


def test_multisig_pending_context_evaluates_initiator(mocker):
    """multisig_pending_context should verify initiator status properly."""
    _mock_get_val = mocker.patch(
        'src.data.service.broadcast_transaction_service.local_store.get_value', return_value='local_xpub',
    )

    assert BroadcastTransactionService.multisig_pending_context(None) is None

    mock_info = MagicMock()
    mock_info.operation = None
    assert BroadcastTransactionService.multisig_pending_context(
        mock_info,
    ) is None

    mock_operation = MagicMock(spec=Operation)
    mock_info.operation = mock_operation
    mock_info.operation.psbt = ''
    assert BroadcastTransactionService.multisig_pending_context(
        mock_info,
    ) is None

    # Mismatched initiator
    mock_info.operation.psbt = 'psbt'
    mock_info.initiator_xpub = 'different_xpub'
    ctx = BroadcastTransactionService.multisig_pending_context(mock_info)
    assert ctx.psbt == 'psbt'
    assert ctx.is_initiator is False

    # Matched initiator
    mock_info.initiator_xpub = 'local_xpub'
    ctx2 = BroadcastTransactionService.multisig_pending_context(mock_info)
    assert ctx2.is_initiator is True


def test_match_pending_operation_psbt_comparison(mocker):
    """match_pending_operation and match_pending_operation_by_txid behave identically for context mapping."""
    mock_multi = mocker.patch(
        'src.data.service.broadcast_transaction_service.BroadcastTransactionService.multisig_pending_context',
    )

    # Null checks
    assert BroadcastTransactionService.match_pending_operation(
        None, 'psbt',
    ) is None
    assert BroadcastTransactionService.match_pending_operation(
        MagicMock(), '',
    ) is None
    assert BroadcastTransactionService.match_pending_operation_by_txid(
        None, 'txid',
    ) is None
    assert BroadcastTransactionService.match_pending_operation_by_txid(
        MagicMock(), '',
    ) is None

    ctx = MagicMock()
    ctx.psbt = 'parsed_psbt'
    mock_multi.return_value = ctx

    # match_pending_operation matches exact parsed PSBT
    assert BroadcastTransactionService.match_pending_operation(
        MagicMock(), 'psbt_mismatch',
    ) is None
    assert BroadcastTransactionService.match_pending_operation(
        MagicMock(), 'psbt:purpose:parsed_psbt',
    ) == ctx

    # by_txid blindly matches if context returns (transaction matching is handled upstream)
    assert BroadcastTransactionService.match_pending_operation_by_txid(
        MagicMock(), 'txid',
    ) == ctx


def test_global_pending_operation_state_lifecycle():
    """State should persist across the class variables securely."""
    BroadcastTransactionService.set_pending_operation_state(
        'my_info', 'my_txid',
    )
    info, txid = BroadcastTransactionService.get_pending_operation_state()
    assert info == 'my_info'
    assert txid == 'my_txid'

    BroadcastTransactionService.set_pending_operation_state(None, None)


def test_operation_transfer_type_key_mappings():
    """operation_transfer_type_key properly isolates type checks."""
    op = MagicMock()

    op.is_INFLATION_TO_REVIEW.return_value = True
    assert BroadcastTransactionService.operation_transfer_type_key(
        op,
    ) == 'inflate_asset'

    op.is_INFLATION_TO_REVIEW.return_value = False
    op.is_SEND_TO_REVIEW.return_value = True
    assert BroadcastTransactionService.operation_transfer_type_key(
        op,
    ) == 'send_asset'

    op.is_SEND_TO_REVIEW.return_value = False
    op.is_SEND_BTC_TO_REVIEW.return_value = True
    assert BroadcastTransactionService.operation_transfer_type_key(
        op,
    ) == 'send_btc'

    op.is_SEND_BTC_TO_REVIEW.return_value = False
    op.is_CREATE_UTXOS_TO_REVIEW.return_value = True
    assert BroadcastTransactionService.operation_transfer_type_key(
        op,
    ) == 'create_utxos'

    op.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    assert BroadcastTransactionService.operation_transfer_type_key(op) is None


def test_is_rgb_purpose_checks():
    """Verify RGB purpose determinations."""
    assert BroadcastTransactionService.is_rgb_purpose('send_asset') is True
    assert BroadcastTransactionService.is_rgb_purpose('inflate_asset') is True
    assert BroadcastTransactionService.is_rgb_purpose('inflation') is True
    assert BroadcastTransactionService.is_rgb_purpose('send_btc') is False
    assert BroadcastTransactionService.is_rgb_purpose(None) is False


def test_set_rgb_mode_for_purpose(mocker):
    """set_rgb_mode_for_purpose directly propagates to the store."""
    mock_store = mocker.patch(
        'src.data.service.broadcast_transaction_service.hardware_client_store',
    )
    BroadcastTransactionService.set_rgb_mode_for_purpose('send_asset')
    mock_store.set_rgb_mode.assert_called_once_with(True)


def test_get_transfer_type_label_localization(mocker):
    """Translations verify correct labels fallback successfully."""
    mock_trans = mocker.patch(
        'src.data.service.broadcast_transaction_service.QCoreApplication.translate',
    )

    # Null cases
    assert BroadcastTransactionService.get_transfer_type_label(None) == ''

    # Translated match
    mock_trans.return_value = 'Translated String'
    assert BroadcastTransactionService.get_transfer_type_label(
        'btc_transfer',
    ) == 'Translated String'

    # Fallback checks (when translate returns identical key)
    mock_trans.return_value = 'btc_transfer'
    assert BroadcastTransactionService.get_transfer_type_label(
        'btc_transfer',
    ) == 'BTC transfer'

    mock_trans.return_value = 'unknown_key'
    assert BroadcastTransactionService.get_transfer_type_label(
        'unknown_key',
    ) == 'unknown_key'


def test_rgb_transfer_inspection_summary_extraction():
    """Ensure amounts and asset identifiers are aggregated safely from dynamic inspection payload."""
    res_none = BroadcastTransactionService.rgb_transfer_inspection_summary(
        None, 'preset_key',
    )
    assert res_none.amount == 0 and res_none.transfer_type_key == 'preset_key'

    # Build complete mock
    assign_send = MagicMock()
    assign_send.is_FUNGIBLE.return_value = True
    assign_send.amount = 100

    assign_inflate = MagicMock()
    assign_inflate.is_FUNGIBLE.return_value = True
    assign_inflate.amount = 200

    out_send = MagicMock()
    out_send.assignment = assign_send
    out_send.is_ours = False

    out_inflate = MagicMock()
    out_inflate.assignment = assign_inflate
    out_inflate.is_ours = True

    trans_send = MagicMock()
    trans_send.outputs = [out_send]

    trans_inflate = MagicMock()
    trans_inflate.outputs = [out_inflate]

    op = MagicMock()
    op.asset_id = 'ASSET123'
    op.transitions = [trans_send]

    rgb_details = MagicMock()
    rgb_details.operations = [op]

    # Test send logic
    summary_send = BroadcastTransactionService.rgb_transfer_inspection_summary(
        rgb_details, None,
    )
    assert summary_send.asset_id == 'ASSET123'
    assert summary_send.amount == 100
    assert summary_send.transfer_type_key == 'asset_transfer'

    # Test inflation logic
    op.transitions = [trans_inflate]
    summary_inflate = BroadcastTransactionService.rgb_transfer_inspection_summary(
        rgb_details, None,
    )
    assert summary_inflate.amount == 200
    assert summary_inflate.transfer_type_key == 'inflation'

    # Test exception suppression
    rgb_details.operations = property(
        lambda: (_ for _ in ()).throw(Exception('boom')),
    )
    summary_err = BroadcastTransactionService.rgb_transfer_inspection_summary(
        rgb_details, None,
    )
    assert summary_err.amount == 0


def test_get_psbt_purpose_from_storage(mocker):
    """Storage fallback safely fetches purpose strings from local db."""
    assert BroadcastTransactionService.get_psbt_purpose_from_storage(
        '',
    ) is None

    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_get_session.return_value = None
    assert BroadcastTransactionService.get_psbt_purpose_from_storage(
        'psbt',
    ) is None

    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    # Missing execution mock
    mock_cursor = MagicMock()
    mock_session.conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [None, ('stored_purpose',)]

    assert BroadcastTransactionService.get_psbt_purpose_from_storage(
        'my_psbt',
    ) == 'stored_purpose'

    # Exception suppression
    mock_cursor.execute.side_effect = Exception('boom')
    assert BroadcastTransactionService.get_psbt_purpose_from_storage(
        'my_psbt',
    ) is None


def test_resolve_transfer_type(mocker):
    """Resolve transfer type delegates to parsed prefix, explicit string, or db layer."""
    assert BroadcastTransactionService.resolve_transfer_type(
        'psbt', False, is_inflation=True,
    ) == 'inflation'
    assert BroadcastTransactionService.resolve_transfer_type(
        'psbt', False, explicit_type='explicit',
    ) == 'explicit'
    assert BroadcastTransactionService.resolve_transfer_type(
        'psbt', False,
    ) is None

    # Multisig active
    assert BroadcastTransactionService.resolve_transfer_type(
        'psbt:send_asset:abc', True,
    ) == 'send_asset'

    mocker.patch(
        'src.data.service.broadcast_transaction_service.BroadcastTransactionService.get_psbt_purpose_from_storage',
        return_value='db_purpose',
    )
    assert BroadcastTransactionService.resolve_transfer_type(
        'psbt_xyz', True,
    ) == 'db_purpose'


def test_can_enable_primary_and_reject_actions():
    """Business rule enforcement for primary 'Sign' / 'Broadcast' / 'Reject' features."""
    # Reject validations
    assert BroadcastTransactionService.can_enable_reject_action(
        False, False, True, True, False,
    ) is False
    assert BroadcastTransactionService.can_enable_reject_action(
        True, True, True, True, True,
    ) is True  # watch only
    assert BroadcastTransactionService.can_enable_reject_action(
        False, True, False, True, False,
    ) is True

    # Primary validations
    # Base fail
    assert BroadcastTransactionService.can_enable_primary_action(
        '', True, False, False, False, False, 0, False, False, 5,
    ) is False

    # Broadcast Flow: valid selection
    assert BroadcastTransactionService.can_enable_primary_action(
        'abcde', True, False, False, False, False, 0, True, False, 5,
    ) is True
    assert BroadcastTransactionService.can_enable_primary_action(
        'abcde', True, False, False, False, False, -1, True, False, 5,
    ) is False

    # Broadcast Flow: multisig watch-only
    assert BroadcastTransactionService.can_enable_primary_action(
        'abcde', True, True, True, True, True, 0, False, False, 5,
    ) is True

    # Signer Flow: Offline
    assert BroadcastTransactionService.can_enable_primary_action(
        'psbt:purpose:abcde', False, True, False, False, False, 0, False, True, 5,
    ) is True
    assert BroadcastTransactionService.can_enable_primary_action(
        'abcde', False, True, True, True, False, 0, False, False, 5,
    ) is True


def test_psbts_loaded_data():
    """Prepares structured responses for dropdown selectors."""
    assert BroadcastTransactionService.psbts_loaded_data([], True) == {
        'has_items': False,
    }

    i1 = PsbtDraftItem(id='1', psbt='x', signed=True, purpose=None)
    assert BroadcastTransactionService.psbts_loaded_data(
        [i1], True,
    ) == {'has_items': True, 'is_single': True, 'psbt': 'x'}

    i2 = PsbtDraftItem(id='2', psbt='y', signed=True, purpose='purpose')
    res = BroadcastTransactionService.psbts_loaded_data([i1, i2], False)
    assert res['has_items'] is True
    assert res['is_single'] is False
    assert res['label_key'] == 'select_psbt_for_sign'
    assert len(res['titles']) == 2


def test_receive_asset_model_for_signed_psbt(mocker):
    """Maps to a standard ReceiveAssetModel response object."""
    mocker.patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.receive_page_name_for_signed_psbt', return_value='PAGE_NAME')
    model = BroadcastTransactionService.receive_asset_model_for_signed_psbt(
        'test',
    )
    assert model.page_name == 'PAGE_NAME'
    assert model.address_info == 'psbt_info'
    assert model.psbt == 'test'
    assert model.is_signed is True


def test_multisig_sign_loading_data(mocker):
    """Safely extracts loading states from a dynamically passed un-typified object."""
    mock_multi = mocker.patch(
        'src.data.service.broadcast_transaction_service.BroadcastTransactionService.multisig_pending_context',
    )
    mock_multi.return_value = None
    assert BroadcastTransactionService.multisig_sign_loading_data(None) == {
        'has_pending': False,
    }

    mock_pending = MagicMock()
    mock_pending.is_initiator = True
    mock_pending.psbt = 'my_psbt'
    mock_pending.operation = 'my_op'
    mock_multi.return_value = mock_pending
    res = BroadcastTransactionService.multisig_sign_loading_data(MagicMock())
    assert res['has_pending'] is True
    assert res['is_initiator'] is True
    assert res['psbt'] == 'my_psbt'
    assert res['operation'] == 'my_op'


def test_should_enable_action_conditional_gates():
    """Gate checks for main logic buttons."""
    # Action checks
    assert BroadcastTransactionService.should_enable_action(
        has_input=False, is_multisig=True, is_psbt_validated=True, pending_operation_present=True,
    ) is False
    assert BroadcastTransactionService.should_enable_action(
        has_input=True, is_multisig=False, is_psbt_validated=False, pending_operation_present=False,
    ) is True
    assert BroadcastTransactionService.should_enable_action(
        has_input=True, is_multisig=True, is_psbt_validated=True, pending_operation_present=True,
    ) is True
    assert BroadcastTransactionService.should_enable_action(
        has_input=True, is_multisig=True, is_psbt_validated=False, pending_operation_present=True,
    ) is False


def test_process_pending_operation_match_and_inspection(mocker):
    """Heavy logic path checks for matching operations onto UI payloads."""
    # Testing process_pending_operation_match
    assert BroadcastTransactionService.process_pending_operation_match(
        None, None, False,
    ) is None

    mock_pending = MagicMock()
    mock_pending.is_initiator = True

    # Create a proper mock Operation with spec
    mock_operation = MagicMock(spec=Operation)
    mock_operation.is_SEND_TO_REVIEW.return_value = True
    mock_operation.is_INFLATION_TO_REVIEW.return_value = False
    mock_operation.is_SEND_BTC_TO_REVIEW.return_value = False
    mock_operation.is_CREATE_UTXOS_TO_REVIEW.return_value = False
    mock_operation.status = None
    mock_operation.details = MagicMock(fascia_path='test_path', entropy=123)

    mock_pending.operation = mock_operation

    res = BroadcastTransactionService.process_pending_operation_match(
        mock_pending, 'raw_info', False,
    )
    assert res.transfer_type == 'send_asset'
    assert res.is_inflation is False
    assert res.is_initiator is True
    assert res.pending_operation == 'raw_info'


def test_resolve_inspection_context(mocker):
    """Verifies rules corresponding to whether a payload requires rgb_lib inspection logic."""
    mocker.patch(
        'src.data.service.broadcast_transaction_service.BroadcastTransactionService.get_psbt_purpose_from_storage',
        return_value='inflate_asset',
    )

    # Operation available overrides everything
    op = MagicMock()
    op.is_INFLATION_TO_REVIEW.return_value = True
    op.is_SEND_TO_REVIEW.return_value = False

    ctx = BroadcastTransactionService.resolve_inspection_context(
        op, None, 'psbt', False,
    )
    assert ctx.is_inflation is True
    assert ctx.rgb_expected is True

    # Missing operation, fetches from purpose
    ctx2 = BroadcastTransactionService.resolve_inspection_context(
        None, 'send_asset', 'psbt', False,
    )
    assert ctx2.is_inflation is False
    assert ctx2.rgb_expected is True

    # Fallback to storage
    ctx3 = BroadcastTransactionService.resolve_inspection_context(
        None, None, 'psbt', False,
    )
    assert ctx3.is_inflation is True
    assert ctx3.rgb_expected is True


def test_resolve_purpose_for_signing(mocker):
    """Signing purpose prioritization chain."""
    mocker.patch(
        'src.data.service.broadcast_transaction_service.BroadcastTransactionService.operation_transfer_type_key', return_value='op_key',
    )
    mocker.patch('src.data.service.broadcast_transaction_service.BroadcastTransactionService.get_psbt_purpose_from_storage', return_value='db_key')

    assert BroadcastTransactionService.resolve_purpose_for_signing(
        'parsed', None, '',
    ) == 'parsed'
    assert BroadcastTransactionService.resolve_purpose_for_signing(
        None, 'op_inst', '',
    ) == 'op_key'
    assert BroadcastTransactionService.resolve_purpose_for_signing(
        None, None, '',
    ) == 'db_key'


def test_prepare_state_contexts():
    """Validation of UI structural contexts and their property configurations."""
    # psbt text
    ctx1 = BroadcastTransactionService.prepare_psbt_text_changed_state(
        'psbt:send_asset:abc', 'abc', 3,
    )
    assert ctx1.is_same_as_last is True
    assert ctx1.should_inspect is True
    assert ctx1.purpose == 'send_asset'
    assert ctx1.is_rgb is True

    # render inspect - updated signature: (psbt_details, is_offline_wallet, current_psbt, min_psbt_len)
    ctx2 = BroadcastTransactionService.prepare_render_inspection_state(
        None,      # psbt_details
        False,     # is_multisig_rgb_expected
        None,      # rgb_details
        False,     # is_offline_wallet
        '',        # current_psbt
        80,        # min_psbt_len
    )
    assert ctx2.should_render is False

    ctx3 = BroadcastTransactionService.prepare_render_inspection_state(
        MagicMock(),
        False,
        MagicMock(),
        False,
        'abc' + 'x' * 80,
        80,
    )

    assert ctx3.should_render is True
    assert ctx3.should_show_sign_status is True

    ctx4 = BroadcastTransactionService.prepare_render_inspection_state(
        MagicMock(),
        True,
        MagicMock(),
        True,
        'abc' + 'x' * 80,
        80,
    )
    assert ctx4.should_render is True
    assert ctx4.should_show_sign_status is False  # offline wallet

    # signature progress
    op = MagicMock()
    op.psbt = 'my_psbt'
    ctx5 = BroadcastTransactionService.prepare_signature_progress_ui_state(
        'my_psbt', 5, op,
    )
    assert ctx5.has_valid_psbt is True
    assert ctx5.should_trigger_direct is True


@patch('src.data.service.broadcast_transaction_service.QCoreApplication.translate')
def test_get_retranslate_data(mock_translate):
    """UI contextual translations."""
    mock_translate.side_effect = lambda ctx, key: f"T({key})"

    # Broadcast logic
    d1 = BroadcastTransactionService.get_retranslate_data(True, False, False)
    assert d1['title'] == 'T(broadcast_transaction)'

    # Respond logic
    d2 = BroadcastTransactionService.get_retranslate_data(False, True, True)
    assert d2['title'] == 'T(respond_to_multisig)'
    assert d2['subtitle'] == 'T(paste_or_import_psbt)'

    # Default
    d3 = BroadcastTransactionService.get_retranslate_data(False, False, False)
    assert d3['title'] == 'T(sign_psbt)'


def test_get_psbt_rgb_context_missing_session(mocker):
    """get_psbt_rgb_context should return None when no session available."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_get_session.return_value = None

    result = BroadcastTransactionService.get_psbt_rgb_context('any_psbt')
    assert result is None


def test_get_psbt_rgb_context_success(mocker):
    """get_psbt_rgb_context should return RGB context dict from wallet service."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_session = MagicMock()
    mock_session.get_psbt_rgb_context.return_value = {
        'fascia_path': '/path/to/app/fascia.rgb',
        'entropy': 123456789,
        'min_confirmations': 3,
    }
    mock_get_session.return_value = mock_session

    result = BroadcastTransactionService.get_psbt_rgb_context('test_psbt')
    assert result is not None
    assert result['fascia_path'] == '/path/to/app/fascia.rgb'
    assert result['entropy'] == 123456789
    assert result['min_confirmations'] == 3
    mock_session.get_psbt_rgb_context.assert_called_once_with('test_psbt')


def test_get_psbt_rgb_context_not_found(mocker):
    """get_psbt_rgb_context should return None when PSBT not found."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_session = MagicMock()
    mock_session.get_psbt_rgb_context.return_value = None
    mock_get_session.return_value = mock_session

    result = BroadcastTransactionService.get_psbt_rgb_context(
        'nonexistent_psbt',
    )
    assert result is None


def test_get_psbt_rgb_context_missing_fascia_path(mocker):
    """get_psbt_rgb_context should return dict even with missing fascia_path."""
    mock_get_session = mocker.patch(
        'src.data.service.broadcast_transaction_service.WalletDataService.get_session',
    )
    mock_session = MagicMock()
    mock_session.get_psbt_rgb_context.return_value = {
        'fascia_path': None,
        'entropy': 0,
        'min_confirmations': None,
    }
    mock_get_session.return_value = mock_session

    result = BroadcastTransactionService.get_psbt_rgb_context('psbt_no_fascia')
    assert result is not None
    assert result['fascia_path'] is None


def test_get_psbt_rgb_context_empty_psbt(mocker):
    """get_psbt_rgb_context should handle empty PSBT string."""
    result = BroadcastTransactionService.get_psbt_rgb_context('')
    assert result is None

    result = BroadcastTransactionService.get_psbt_rgb_context(None)
    assert result is None
