"""
Repository for PSBT-related database operations.
"""
from __future__ import annotations

import hashlib
import sqlite3

from src.model.common_operation_model import PsbtData
from src.utils.logging import logger


class PsbtRepository:
    """Handles all SQLite operations for the psbt table."""

    @staticmethod
    def _psbt_id(psbt_base64: str) -> str:
        """Deterministic id for a PSBT payload (sha256 of normalized base64 string)."""
        normalized = ''.join(psbt_base64.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def add_psbt(conn: sqlite3.Connection, psbt_data: PsbtData) -> str:
        """Insert or replace a PSBT."""
        normalized_psbt = ''.join(psbt_data.psbt_base64.split())
        psbt_id = PsbtRepository._psbt_id(normalized_psbt)
        entropy_str = str(
            psbt_data.entropy,
        ) if psbt_data.entropy is not None else None

        try:
            conn.execute(
                'INSERT OR REPLACE INTO psbt (id, psbt, signed, purpose, fascia_path, entropy, min_confirmations) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    psbt_id, normalized_psbt, 1 if psbt_data.signed else 0,
                    psbt_data.purpose, psbt_data.fascia_path, entropy_str, psbt_data.min_confirmations,
                ),
            )
            return psbt_id
        except sqlite3.Error as exc:
            logger.error('PsbtRepository: add_psbt failed: %s', exc)
            raise

    @staticmethod
    def mark_psbt_signed(conn: sqlite3.Connection, unsigned_psbt_base64: str, signed_psbt_base64: str) -> str:
        """Replace an unsigned PSBT with its signed version."""
        unsigned_id = PsbtRepository._psbt_id(unsigned_psbt_base64)
        normalized_signed_psbt = ''.join((signed_psbt_base64 or '').split())
        signed_id = PsbtRepository._psbt_id(normalized_signed_psbt)

        try:
            cur = conn.execute(
                'SELECT purpose, fascia_path, entropy, min_confirmations FROM psbt WHERE id = ?', (
                    unsigned_id,
                ),
            )
            row = cur.fetchone()
            purpose = row[0] if row is not None else None
            fascia_path = row[1] if row is not None and len(row) > 1 else None
            entropy = row[2] if row is not None and len(row) > 2 else None
            min_confirmations = row[3] if row is not None and len(
                row,
            ) > 3 else None

            conn.execute('DELETE FROM psbt WHERE id = ?', (unsigned_id,))
            conn.execute(
                'INSERT OR REPLACE INTO psbt (id, psbt, signed, purpose, fascia_path, entropy, min_confirmations) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
                    signed_id, normalized_signed_psbt, 1, purpose,
                    fascia_path, entropy, min_confirmations,
                ),
            )
            return signed_id
        except sqlite3.Error as exc:
            logger.error('PsbtRepository: mark_psbt_signed failed: %s', exc)
            raise

    @staticmethod
    def delete_psbt(conn: sqlite3.Connection, psbt_base64: str) -> bool:
        """Delete targeted PSBT."""
        psbt_id = PsbtRepository._psbt_id(psbt_base64)
        try:
            cur = conn.execute('DELETE FROM psbt WHERE id = ?', (psbt_id,))
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error('PsbtRepository: delete_psbt failed: %s', exc)
            raise

    @staticmethod
    def update_psbt_rgb_context(
        conn: sqlite3.Connection,
        psbt_base64: str,
        fascia_path: str | None = None,
        entropy: int | None = None,
        min_confirmations: int | None = None,
    ) -> bool:
        """Update RGB context fields."""
        psbt_id = PsbtRepository._psbt_id(psbt_base64)
        entropy_str = str(entropy) if entropy is not None else None
        try:
            cur = conn.execute(
                'UPDATE psbt SET fascia_path = ?, entropy = ?, min_confirmations = ? WHERE id = ?',
                (fascia_path, entropy_str, min_confirmations, psbt_id),
            )
            return cur.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(
                'PsbtRepository: update_psbt_rgb_context failed: %s', exc,
            )
            raise

    @staticmethod
    def get_psbt_rgb_context(conn: sqlite3.Connection, psbt_base64: str) -> dict | None:
        """Get RGB context."""
        psbt_id = PsbtRepository._psbt_id(psbt_base64)
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT fascia_path, entropy, min_confirmations FROM psbt WHERE id = ?', (
                    psbt_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                'fascia_path': row[0],
                'entropy': int(row[1]) if row[1] is not None else None,
                'min_confirmations': row[2],
            }
        except sqlite3.Error as exc:
            logger.error(
                'PsbtRepository: get_psbt_rgb_context failed: %s', exc,
            )
            raise

    @staticmethod
    def list_psbt(conn: sqlite3.Connection, signed: bool) -> list[dict]:
        """List PSBTs."""
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT id, psbt, signed, purpose, fascia_path, entropy, min_confirmations FROM psbt WHERE signed = ?',
                (1 if signed else 0,),
            )
            rows = cur.fetchall()
            return [
                {
                    'id': r[0],
                    'psbt': r[1],
                    'signed': bool(r[2]),
                    'purpose': r[3] if len(r) > 3 else None,
                    'fascia_path': r[4] if len(r) > 4 else None,
                    'entropy': int(r[5]) if len(r) > 5 and r[5] is not None else None,
                    'min_confirmations': r[6] if len(r) > 6 else None,
                }
                for r in rows
            ]
        except sqlite3.Error as exc:
            logger.error('PsbtRepository: list_psbt failed: %s', exc)
            raise
