from engine.magic import load_or_create_tables, get_magic_index
from engine.constants import SQ_MASK, RANK_2, RANK_7
from engine.bitboard_utils import bishop_mask, rook_mask, submasks, build_between_diagonal, build_between_line, rook_attack, bishop_attack


def precompute_king_attacks(position):
    row = position // 8
    col = position % 8
    mask = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if 0 <= row + i < 8 and 0 <= col + j < 8 and not (i == 0 and j == 0):
                mask |= 1 << (row + i) * 8 + (col + j)

    return mask

def precompute_knight_attacks(position):
    row = position // 8
    col = position % 8
    mask = 0
    for i in range(-2, 3):
        if i == 2 or i == -2:
            for j in (1, -1):
                if 0 <= row + i < 8 and 0 <= col + j < 8:
                    mask |= 1 << (row + i) * 8 + (col + j)
        elif i == 1 or i == -1:
            for j in (2, -2):
                if 0 <= row + i < 8 and 0 <= col + j < 8:
                    mask |= 1 << (row + i) * 8 + (col + j)
    return mask

def precompute_pawn_attacks(position, side="white"):
    row, col = divmod(position, 8)
    mask = 0

    if side == 'white':
        if row < 7:
            if col + 1 < 8:
                mask |= 1 << (row + 1) * 8 + (col + 1)
            if col - 1 >= 0:
                mask |= 1 << (row + 1) * 8 + (col-1)
    else:
        if row > 0:
            if col + 1 < 8:
                mask |= 1 << (row - 1) * 8 + (col + 1)
            if col - 1 >= 0:
                mask |= 1 << (row - 1) * 8 + (col-1)

    return mask

def build_double_push_mask(sq):
    if SQ_MASK[sq] & RANK_2:
        return SQ_MASK[sq+8] | SQ_MASK[sq + 16]
    elif SQ_MASK[sq] & RANK_7:
        return SQ_MASK[sq-8] | SQ_MASK[sq - 16]
    else:
        return 0


    
def build_rook_table(square: int) -> list[int]:
    mask = rook_mask(square)
    rbits = ROOK_RELEVEANT_BITS[square]
    size = 1 << rbits
    table = [0] * size
    idxs = []
    for occ in submasks(mask):
        idx = get_magic_index(occ, ROOK_MAGIC[square], rbits)
        table[idx] = rook_attack(square, occ)
        if idx in idxs:
            print('duplicate magic rook')
        idxs.append(idx)
    return table


def build_bishop_table(square: int) -> list[int]:
    mask = bishop_mask(square)
    rbits = BISHOP_RELEVEANT_BITS[square]
    size = 1 << rbits
    table = [0] * size
    idxs = []
    for occ in submasks(mask):
        idx = get_magic_index(occ, BISHOP_MAGIC[square], rbits)
        table[idx] = bishop_attack(square, occ)
        if idx in idxs:
            print('duplicate magic bishop')
        idxs.append(idx)
    return table



tables = load_or_create_tables()
ROOK_RELEVEANT_BITS = tables['rook_bits']
ROOK_RELEVANT_MASK = tables['rook_masks']
ROOK_MAGIC = tables['rook_magics']
ROOK_TABLE = tables['rook_tables']
BISHOP_RELEVEANT_BITS = tables['bishop_bits']
BISHOP_RELEVANT_MASK = tables['bishop_masks']
BISHOP_MAGIC = tables['bishop_magics']
BISHOP_TABLE = tables['bishop_tables']


PAWN_DOUBLE_PUSH_TABLE = [
    build_double_push_mask(sq) for sq in range(64)
]
WHITE_PAWN_ATTACK_TABLE = [
    precompute_pawn_attacks(sq, 'white') for sq in range(64)]
BLACK_PAWN_ATTACK_TABLE = [
    precompute_pawn_attacks(sq, 'black') for sq in range(64)]
KING_TABLE = [precompute_king_attacks(sq) for sq in range(64)]
KNIGHT_TABLE = [precompute_knight_attacks(sq) for sq in range(64)]
ROOK_TABLE = [build_rook_table(sq) for sq in range(64)]
BISHOP_TABLE = [build_bishop_table(sq) for sq in range(64)]
BISHOP_BETWEEN_MASK = [
    [build_between_diagonal(b_sq, k_sq) for k_sq in range(64)]
    for b_sq in range(64)
]
ROOK_BETWEEN_MASK = [
    [build_between_line(r_sq, k_sq) for k_sq in range(64)]
    for r_sq in range(64)
]