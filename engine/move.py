"""Utility structures and helpers for move representation."""

from dataclasses import dataclass

@dataclass
class HistoryEntry:
    encoded_move: int        # the 16-bit word you just played
    captured: int            # 0-11 or NO_PIECE
    prev_ep: int | None      # en-passant target before the move
    castle_mask: int         # 4 bits: WK WQ BK BQ
    prev_hash: int

@dataclass
class TTEntry:
    key:  int
    depth: int
    flag:  int        # EXACT / LOWER / UPPER
    score: int
    move:  int 


def encode_move(from_sq: int, to_sq: int, flag: int = 0) -> int:
    """Return 16-bit move word (0 ≤ flag ≤ 15)."""
    return (from_sq & 0x3F) | ((to_sq & 0x3F) << 6) | ((flag & 0xF) << 12)


def decode_move(move: int):
    """Return tuple (from_sq, to_sq, flag) from 16-bit word."""
    from_sq = move & 0x3F
    to_sq = (move >> 6) & 0x3F
    flag = move >> 12        # already only 4 bits
    return from_sq, to_sq, flag


def pack_castle(wk, qk, bk, bq) -> int:
    """Pack individual castling rights into a 4-bit mask."""
    return (wk << 0) | (qk << 1) | (bk << 2) | (bq << 3)

def unpack_castle(mask: int):
    """Unpack individual castling rights from a 4-bit mask."""
    return bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)