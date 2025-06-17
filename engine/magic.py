"""Find magic numbers"""

import os
from typing import List, Tuple
import pickle

from engine.constants import MAGIC_FILENAME
from engine.bitboard_utils import popcount, submasks, rank_of, rook_mask, bishop_mask, rook_attack, bishop_attack
from engine.constants import MASK64, SEEDS
from engine.prng import PRNG


def find_magic(
    sq: int,
    is_rook: bool,
    mask: int,
    bits: int,
    reference: List[int]
) -> int:
    """Search for a magic that is collision-free for *sq*."""
    size = 1 << bits
    shifts = 64 - bits
    table = [0] * size
    occs = list(submasks(mask))
    rng = PRNG(SEEDS[1][rank_of(sq)])   # use 32-bit seeds row (like Stockfish)

    while True:
        magic = rng.sparse_rand()
        # Reject obviously bad candidates (6 MSBs test – same as Stockfish)
        if popcount((magic * mask) & 0xFF00000000000000) < 6:
            continue

        table[:] = [0] * size
        fail = False
        for occ, ref in zip(occs, reference):
            idx = ((occ * magic) & MASK64) >> shifts
            if table[idx] == 0:
                table[idx] = ref
            elif table[idx] != ref:
                fail = True
                break
        if not fail:
            return magic
        
def get_magic_index(occ: int, magic: int, shift: int):
    prod = (occ * magic) & 0xFFFFFFFFFFFFFFFF
    return 0 if shift == 0 else prod >> (64 - shift)

def build_piece_tables(is_rook: bool) -> Tuple[
    List[int], List[int], List[int], List[List[int]]
]:
    MASK_FN = rook_mask if is_rook else bishop_mask
    ATT_FN = rook_attack if is_rook else bishop_attack
    name = "ROOK" if is_rook else "BISHOP"

    relevant_mask: List[int] = []
    relevant_bits: List[int] = []
    magic_numbers: List[int] = []
    attack_tables: List[List[int]] = []

    for sq in range(64):
        mask = MASK_FN(sq)
        bits = popcount(mask)

        # Pre-compute reference attacks for every subset
        ref = [ATT_FN(sq, occ) for occ in submasks(mask)]

        magic = find_magic(sq, is_rook, mask, bits, ref)

        # Build final table using the found magic
        size = 1 << bits
        shifts = 64 - bits
        table = [0] * size
        for occ, atk in zip(submasks(mask), ref):
            idx = ((occ * magic) & MASK64) >> shifts
            table[idx] = atk

        relevant_mask.append(mask)
        relevant_bits.append(bits)
        magic_numbers.append(magic)
        attack_tables.append(table)

    print(f"[{name}]   finished, worst table size = {max(len(t) for t in attack_tables):,}")
    return relevant_bits, relevant_mask, magic_numbers, attack_tables

def generate_and_save_tables():
    rook_bits, rook_masks, rook_magics, rook_tables = build_piece_tables(
        is_rook=True)
    bishop_bits, bishop_masks, bishop_magics, bishop_tables = build_piece_tables(
        is_rook=False)
    data = {
        'rook_bits': rook_bits,
        'rook_masks': rook_masks,
        'rook_magics': rook_magics,
        'rook_tables': rook_tables,
        'bishop_bits': bishop_bits,
        'bishop_masks': bishop_masks,
        'bishop_magics': bishop_magics,
        'bishop_tables': bishop_tables,
    }
    with open(MAGIC_FILENAME, 'wb') as f:
        pickle.dump(data, f)
    return data


def load_or_create_tables():
    if os.path.exists(MAGIC_FILENAME):
        with open(MAGIC_FILENAME, 'rb') as f:
            data = pickle.load(f)
        print("Loaded magic tables from file.")
    else:
        print("Building magic tables, please wait...")
        data = generate_and_save_tables()
        print("Saved magic tables to file.")
    return data