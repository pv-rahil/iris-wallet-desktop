"""Unit tests for PsbtRepository."""
# pylint: disable=redefined-outer-name, unused-argument, protected-access
from __future__ import annotations

import hashlib
import sqlite3

import pytest

from src.data.repository.psbt_repository import PsbtRepository
from src.model.common_operation_model import PsbtData


@pytest.fixture
def mock_conn():
    """Fixture for SQLite connection with in-memory database."""
    conn = sqlite3.connect(':memory:')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS psbt (
            id TEXT PRIMARY KEY,
            psbt TEXT NOT NULL,
            signed INTEGER DEFAULT 0,
            purpose TEXT,
            fascia_path TEXT,
            entropy TEXT,
            min_confirmations INTEGER
        )
    ''')
    yield conn
    conn.close()


def test_psbt_id_generates_consistent_hash():
    """Test _psbt_id generates consistent SHA256 hash."""
    # Setup
    psbt_base64 = 'cHNidP8BAKACAAAAAqsLMQ'
    expected = hashlib.sha256(psbt_base64.encode('utf-8')).hexdigest()

    # Execute
    result = PsbtRepository._psbt_id(psbt_base64)

    # Assert
    assert result == expected


def test_psbt_id_normalizes_whitespace():
    """Test _psbt_id normalizes whitespace in PSBT string."""
    # Setup
    psbt_with_spaces = 'cHNidP8 BAKACAAAA AqsLMQ'
    psbt_without_spaces = 'cHNidP8BAKACAAAAAqsLMQ'

    # Execute
    result_with_spaces = PsbtRepository._psbt_id(psbt_with_spaces)
    result_without_spaces = PsbtRepository._psbt_id(psbt_without_spaces)

    # Assert
    assert result_with_spaces == result_without_spaces


def test_add_psbt_inserts_new_record(mock_conn):
    """Test add_psbt inserts a new PSBT record."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test_purpose',
        fascia_path='/test/path',
        entropy=12345,
        min_confirmations=6,
    )

    # Execute
    result = PsbtRepository.add_psbt(mock_conn, psbt_data)

    # Assert
    assert result is not None
    assert len(result) == 64
    cur = mock_conn.cursor()
    cur.execute('SELECT * FROM psbt WHERE id = ?', (result,))
    row = cur.fetchone()
    assert row is not None
    assert row[2] == 0


def test_add_psbt_inserts_signed_record(mock_conn):
    """Test add_psbt inserts a signed PSBT record."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=True,
        purpose='test',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )

    # Execute
    result = PsbtRepository.add_psbt(mock_conn, psbt_data)

    # Assert
    cur = mock_conn.cursor()
    cur.execute('SELECT signed FROM psbt WHERE id = ?', (result,))
    row = cur.fetchone()
    assert row[0] == 1


def test_add_psbt_replaces_existing_record(mock_conn):
    """Test add_psbt replaces existing PSBT with same ID."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    first_id = PsbtRepository.add_psbt(mock_conn, psbt_data)
    updated_psbt = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=True,
        purpose='updated_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )

    # Execute
    second_id = PsbtRepository.add_psbt(mock_conn, updated_psbt)

    # Assert
    assert first_id == second_id
    cur = mock_conn.cursor()
    cur.execute('SELECT signed, purpose FROM psbt WHERE id = ?', (first_id,))
    row = cur.fetchone()
    assert row[0] == 1
    assert row[1] == 'updated_purpose'


def test_mark_psbt_signed_updates_record(mock_conn):
    """Test mark_psbt_signed updates unsigned PSBT to signed."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test_purpose',
        fascia_path='/test/path',
        entropy=12345,
        min_confirmations=6,
    )
    unsigned_id = PsbtRepository.add_psbt(mock_conn, psbt_data)
    signed_psbt = 'cHNidP8BAKACAAAAAqsLMQSigned'

    # Execute
    result = PsbtRepository.mark_psbt_signed(
        mock_conn, psbt_data.psbt_base64, signed_psbt,
    )

    # Assert
    assert result is not None
    assert result != unsigned_id
    cur = mock_conn.cursor()
    cur.execute('SELECT signed FROM psbt WHERE id = ?', (result,))
    row = cur.fetchone()
    assert row[0] == 1


def test_mark_psbt_signed_preserves_metadata(mock_conn):
    """Test mark_psbt_signed preserves purpose, fascia_path, entropy."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test_purpose',
        fascia_path='/test/path',
        entropy=12345,
        min_confirmations=6,
    )
    PsbtRepository.add_psbt(mock_conn, psbt_data)
    signed_psbt = 'cHNidP8BAKACAAAAAqsLMQSigned'

    # Execute
    result = PsbtRepository.mark_psbt_signed(
        mock_conn, psbt_data.psbt_base64, signed_psbt,
    )

    # Assert
    cur = mock_conn.cursor()
    cur.execute(
        'SELECT purpose, fascia_path, entropy, min_confirmations FROM psbt WHERE id = ?',
        (result,),
    )
    row = cur.fetchone()
    assert row[0] == psbt_data.purpose
    assert row[1] == psbt_data.fascia_path
    assert int(row[2]) == psbt_data.entropy
    assert row[3] == psbt_data.min_confirmations


def test_delete_psbt_removes_record(mock_conn):
    """Test delete_psbt removes the PSBT record."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    PsbtRepository.add_psbt(mock_conn, psbt_data)

    # Execute
    result = PsbtRepository.delete_psbt(mock_conn, psbt_data.psbt_base64)

    # Assert
    assert result is True
    cur = mock_conn.cursor()
    cur.execute(
        'SELECT * FROM psbt WHERE id = ?',
        (PsbtRepository._psbt_id(psbt_data.psbt_base64),),
    )
    row = cur.fetchone()
    assert row is None


def test_delete_psbt_returns_false_for_nonexistent(mock_conn):
    """Test delete_psbt returns False for nonexistent PSBT."""
    # Execute
    result = PsbtRepository.delete_psbt(mock_conn, 'nonexistent_psbt')

    # Assert
    assert result is False


def test_update_psbt_rgb_context_updates_fields(mock_conn):
    """Test update_psbt_rgb_context updates RGB context fields."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test',
        fascia_path='/test',
        entropy=100,
        min_confirmations=6,
    )
    PsbtRepository.add_psbt(mock_conn, psbt_data)

    # Execute
    result = PsbtRepository.update_psbt_rgb_context(
        mock_conn,
        psbt_data.psbt_base64,
        fascia_path='/updated/path',
        entropy=99999,
        min_confirmations=12,
    )

    # Assert
    assert result is True
    cur = mock_conn.cursor()
    cur.execute(
        'SELECT fascia_path, entropy, min_confirmations FROM psbt WHERE id = ?',
        (PsbtRepository._psbt_id(psbt_data.psbt_base64),),
    )
    row = cur.fetchone()
    assert row[0] == '/updated/path'
    assert int(row[1]) == 99999
    assert row[2] == 12


def test_get_psbt_rgb_context_returns_dict(mock_conn):
    """Test get_psbt_rgb_context returns context dictionary."""
    # Setup
    psbt_data = PsbtData(
        psbt_base64='cHNidP8BAKACAAAAAqsLMQ',
        signed=False,
        purpose='test',
        fascia_path='/test/path',
        entropy=12345,
        min_confirmations=6,
    )
    PsbtRepository.add_psbt(mock_conn, psbt_data)

    # Execute
    result = PsbtRepository.get_psbt_rgb_context(
        mock_conn, psbt_data.psbt_base64,
    )

    # Assert
    assert result is not None
    assert result['fascia_path'] == psbt_data.fascia_path
    assert result['entropy'] == psbt_data.entropy
    assert result['min_confirmations'] == psbt_data.min_confirmations


def test_get_psbt_rgb_context_returns_none_for_nonexistent(mock_conn):
    """Test get_psbt_rgb_context returns None for nonexistent PSBT."""
    # Execute
    result = PsbtRepository.get_psbt_rgb_context(mock_conn, 'nonexistent_psbt')

    # Assert
    assert result is None


def test_list_psbt_returns_signed_psbts(mock_conn):
    """Test list_psbt returns only signed PSBTs when signed=True."""
    # Setup
    signed_psbt = PsbtData(
        psbt_base64='signed_psbt_base64',
        signed=True,
        purpose='signed_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    unsigned_psbt = PsbtData(
        psbt_base64='unsigned_psbt_base64',
        signed=False,
        purpose='unsigned_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    PsbtRepository.add_psbt(mock_conn, signed_psbt)
    PsbtRepository.add_psbt(mock_conn, unsigned_psbt)

    # Execute
    result = PsbtRepository.list_psbt(mock_conn, signed=True)

    # Assert
    assert len(result) == 1
    assert result[0]['signed'] is True


def test_list_psbt_returns_unsigned_psbts(mock_conn):
    """Test list_psbt returns only unsigned PSBTs when signed=False."""
    # Setup
    signed_psbt = PsbtData(
        psbt_base64='signed_psbt_base64',
        signed=True,
        purpose='signed_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    unsigned_psbt = PsbtData(
        psbt_base64='unsigned_psbt_base64',
        signed=False,
        purpose='unsigned_purpose',
        fascia_path=None,
        entropy=None,
        min_confirmations=None,
    )
    PsbtRepository.add_psbt(mock_conn, signed_psbt)
    PsbtRepository.add_psbt(mock_conn, unsigned_psbt)

    # Execute
    result = PsbtRepository.list_psbt(mock_conn, signed=False)

    # Assert
    assert len(result) == 1
    assert result[0]['signed'] is False


def test_list_psbt_returns_empty_list_for_no_matches(mock_conn):
    """Test list_psbt returns empty list when no matches."""
    # Execute
    result = PsbtRepository.list_psbt(mock_conn, signed=True)

    # Assert
    assert result == []
