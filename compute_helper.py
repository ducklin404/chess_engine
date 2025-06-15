import os
import pickle

from dataclasses import dataclass
import random
from typing import List, Tuple

INF = 999999999

MASK64 = 0xFFFFFFFFFFFFFFFF


class PRNG:
    def __init__(self, seed: int) -> None:
        self.s = seed & MASK64

    def rand64(self) -> int:
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & MASK64
        x = self.s
        x ^= (x >> 12) & MASK64
        x ^= (x << 25) & MASK64
        x ^= (x >> 27) & MASK64
        return (x * 2685821657736338717) & MASK64

    def sparse_rand(self) -> int:
        return self.rand64() & self.rand64() & self.rand64()


def popcount(x: int) -> int:
    return x.bit_count()


def rank_of(sq: int) -> int:
    return sq >> 3


# === magic search ==========================================================

SEEDS = [               # [is64][rank]  – copied from Stockfish
    [8977, 44560, 54343, 38998,  5731, 95205, 104912, 17020],
    [728, 10316, 55013, 32803, 12281, 15100,  16645,   255],
]


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


@dataclass
class HistoryEntry:
    encoded_move: int        # the 16-bit word you just played
    captured: int            # 0-11 or NO_PIECE
    prev_ep: int | None      # en-passant target before the move
    castle_mask: int         # 4 bits: WK WQ BK BQ
    prev_hash: int


def pack_castle(wk, qk, bk, bq) -> int:
    return (wk << 0) | (qk << 1) | (bk << 2) | (bq << 3)
PAWN_ADVANCE = [0, 4, 7, 10, 18, 30, 60, 0]   
PASSED_BONUS = 15               
MATE = 1_000_000       
def unpack_castle(mask: int):
    return bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)

init_fen = "8/8/8/8/1q6/8/8/K1k5 w - - 0 1"

RANK_1 = 0x00000000000000FF
RANK_8 = 0xFF00000000000000

RANK_4 = 0x00000000FF000000
RANK_5 = 0x000000FF00000000

RANK_2 = 0x000000000000FF00
RANK_7 = 0x00FF000000000000

FILE_A = 0x0101010101010101  # bits a1, a2, …, a8
FILE_B = 0x0202020202020202  # bits b1, b2, …, b8
FILE_C = 0x0404040404040404  # bits c1, c2, …, c8
FILE_D = 0x0808080808080808  # bits d1, d2, …, d8
FILE_E = 0x1010101010101010  # bits e1, e2, …, e8
FILE_F = 0x2020202020202020  # bits f1, f2, …, f8
FILE_G = 0x4040404040404040  # bits g1, g2, …, g8
FILE_H = 0x8080808080808080  # bits h1, h2, …, h8

FILE_MASKS = [
    FILE_A,
    FILE_B,
    FILE_C,
    FILE_D,
    FILE_E,
    FILE_F,
    FILE_G,
    FILE_H,
]

SQ_MASK = [1 << i for i in range(64)]

NO_PIECE = -1

WHITE_PAWN = 0
WHITE_KNIGHT = 1
WHITE_BISHOP = 2
WHITE_ROOK = 3
WHITE_QUEEN = 4
WHITE_KING = 5

BLACK_PAWN = 6
BLACK_KNIGHT = 7
BLACK_BISHOP = 8
BLACK_ROOK = 9
BLACK_QUEEN = 10
BLACK_KING = 11

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(6)


PAWN_VALUE = 100
KNIGHT_VALUE = 300
BISHOP_VALUE = 300
ROOK_VALUE = 500
QUEEN_VALUE = 900
KING_VALUE = 20000

PIECE_VALUES = [
    1,    # WHITE_PAWN
    3,    # WHITE_KNIGHT
    3,    # WHITE_BISHOP
    5,    # WHITE_ROOK
    9,    # WHITE_QUEEN
    1000,  # WHITE_KING
    1,    # BLACK_PAWN
    3,    # BLACK_KNIGHT
    3,    # BLACK_BISHOP
    5,    # BLACK_ROOK
    9,    # BLACK_QUEEN
    1000,  # BLACK_KING
]

WHITE = 0
BLACK = 1

QUIET = 0x0     # normal non-capture
DOUBLE_PUSH = 0x1     # pawn two-square advance
CASTLE_KING = 0x2
CASTLE_QUEEN = 0x3

CAPTURE = 0x4     # ordinary capture           (flag | 4)
EN_PASSANT = 0x5     # pawn takes en-passant

PROMO_N = 0x8     # promote to knight          (flag | 8)
PROMO_B = 0x9     # promote to bishop
PROMO_R = 0xA     # promote to rook
PROMO_Q = 0xB     # promote to queen
PCAP_N = 0xC     # capture & promote knight   (flag | 0xC)
PCAP_B = 0xD
PCAP_R = 0xE
PCAP_Q = 0xF

# Pawn

DOUBLED_PAWN_PENALTY = 10
ISOLATED_PAWN_PENALTY = 15
PAWN_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5, -10,  0,  0, -10, -5,  5,
    5, 10, 10, -20, -20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

# Knight
KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,  0,  0,  0,  0, -20, -40,
    -30,  0, 10, 15, 15, 10,  0, -30,
    -30,  5, 15, 20, 20, 15,  5, -30,
    -30,  0, 15, 20, 20, 15,  0, -30,
    -30,  5, 10, 15, 15, 10,  5, -30,
    -40, -20,  0,  5,  5,  0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

# Bishop
BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,  0,  0,  0,  0,  0,  0, -10,
    -10,  0,  5, 10, 10,  5,  0, -10,
    -10,  5,  5, 10, 10,  5,  5, -10,
    -10,  0, 10, 10, 10, 10,  0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10,  5,  0,  0,  0,  0,  5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

# Rook
ROOK_ON_OPEN_FILE_BONUS = 10
ROOK_ON_HALF_OPEN_FILE_BONUS = 5
ROOK_PST = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

# Queen
QUEEN_PST = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10,  0,  0,  0,  0,  0,  0, -10,
    -10,  0,  5,  5,  5,  5,  0, -10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0, -10,
    -10,  0,  5,  0,  0,  0,  0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

# King (middlegame)
KING_PST_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

# King (endgame)
KING_PST_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,  0,  0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30,  0,  0,  0,  0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

MIDDLE_GAME = 0
END_GAME = 1

PIECE_TO_PST = [
    PAWN_PST,
    KNIGHT_PST,
    BISHOP_PST,
    ROOK_PST,
    QUEEN_PST,
    KING_PST_MG,
    KING_PST_EG
]

INITIAL_PIECE_AT = [
    WHITE_ROOK,   WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK,
    WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,  WHITE_PAWN, WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,
    # 8th rank

    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 6th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 5th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 4th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 3rd rank
    BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,  BLACK_PAWN, BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   # 7th rank
    BLACK_ROOK,   BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK
    # 2nd rank
    # 1st rank
]


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


def get_magic_index(occ: int, magic: int, shift: int):
    prod = (occ * magic) & 0xFFFFFFFFFFFFFFFF
    return 0 if shift == 0 else prod >> (64 - shift)


def count_ones_kernighan(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


def rook_mask(sq: int) -> int:
    r, f = divmod(sq, 8)
    mask = 0
    for r_ in range(r + 1, 7):
        mask |= 1 << (r_ * 8 + f)        # north
    for r_ in range(r - 1, 0, -1):
        mask |= 1 << (r_ * 8 + f)     # south
    for f_ in range(f + 1, 7):
        mask |= 1 << (r * 8 + f_)        # east
    for f_ in range(f - 1, 0, -1):
        mask |= 1 << (r * 8 + f_)     # west
    return mask


def bishop_mask(sq: int) -> int:
    r, f = divmod(sq, 8)
    mask = 0
    for dr, df in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r_, f_ = r + dr, f + df
        while 0 < r_ < 7 and 0 < f_ < 7:
            mask |= 1 << (r_ * 8 + f_)
            r_, f_ = r_ + dr, f_ + df
    return mask


ROOK_RELEVANT_MASK = [rook_mask(sq) for sq in range(64)]
BISHOP_RELEVANT_MASK = [bishop_mask(sq) for sq in range(64)]


ROOK_RELEVEANT_BITS = [popcount(m) for m in ROOK_RELEVANT_MASK]
BISHOP_RELEVEANT_BITS = [popcount(m) for m in BISHOP_RELEVANT_MASK]


def rook_attack(sq: int, occ: int) -> int:
    r, f = divmod(sq, 8)
    atk = 0
    for r_ in range(r + 1, 8):
        s = r_ * 8 + f
        atk |= 1 << s
        if occ & (1 << s):
            break
    for r_ in range(r - 1, -1, -1):
        s = r_ * 8 + f
        atk |= 1 << s
        if occ & (1 << s):
            break
    for f_ in range(f + 1, 8):
        s = r * 8 + f_
        atk |= 1 << s
        if occ & (1 << s):
            break
    for f_ in range(f - 1, -1, -1):
        s = r * 8 + f_
        atk |= 1 << s
        if occ & (1 << s):
            break
    return atk


def bishop_attack(sq: int, occ: int) -> int:
    r, f = divmod(sq, 8)
    atk = 0
    for dr, df in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r_, f_ = r + dr, f + df
        while 0 <= r_ <= 7 and 0 <= f_ <= 7:
            s = r_ * 8 + f_
            atk |= 1 << s
            if occ & (1 << s):
                break
            r_, f_ = r_ + dr, f_ + df
    return atk


def submasks(mask: int):
    """Yield all subsets of `mask`, including 0."""
    sub = mask
    while True:
        yield sub
        if sub == 0:
            break
        sub = (sub - 1) & mask


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


MAGIC_FILENAME = "magic_tables.pkl"


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


tables = load_or_create_tables()
ROOK_RELEVEANT_BITS = tables['rook_bits']
ROOK_RELEVANT_MASK = tables['rook_masks']
ROOK_MAGIC = tables['rook_magics']
ROOK_TABLE = tables['rook_tables']
BISHOP_RELEVEANT_BITS = tables['bishop_bits']
BISHOP_RELEVANT_MASK = tables['bishop_masks']
BISHOP_MAGIC = tables['bishop_magics']
BISHOP_TABLE = tables['bishop_tables']

random.seed(42)
def rand64():
    return random.getrandbits(64)

H_PIECE =  [[[rand64() for _ in range(64)]
                  for _ in range(6)]
                  for _ in range(2)]
H_CASTLE = [rand64() for _ in range(4)]
H_EN_PASSANT = [rand64() for _ in range(8)]
H_BLACK_TO_MOVE = rand64()


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


def build_double_push_mask(sq):
    if SQ_MASK[sq] & RANK_2:
        return SQ_MASK[sq+8] | SQ_MASK[sq + 16]
    elif SQ_MASK[sq] & RANK_7:
        return SQ_MASK[sq-8] | SQ_MASK[sq - 16]
    else:
        return 0


def build_between_diagonal(from_sq, to_sq):
    diagonal = 0
    from_row, from_col = divmod(from_sq, 8)
    to_row, to_col = divmod(to_sq, 8)
    offset_row = to_row - from_row
    offset_col = to_col - from_col
    step_row = 1 if offset_row > 0 else -1
    step_col = 1 if offset_col > 0 else -1
    if abs(offset_row) != abs(offset_col):
        return 0
    for i in range(0, abs(offset_row)):
        diagonal |= 1 << (from_row + step_row*i)*8 + (from_col + step_col*i)

    return diagonal


def build_between_line(from_sq, to_sq):
    line = 0
    from_row, from_col = divmod(from_sq, 8)
    to_row, to_col = divmod(to_sq, 8)
    offset_row = to_row - from_row
    offset_col = to_col - from_col
    if offset_row != 0 and offset_col != 0:
        return 0
    if offset_row == 0:
        step_row = 0
        step_col = 1 if offset_col > 0 else -1
    else:
        step_row = 1 if offset_row > 0 else -1
        step_col = 0

    for i in range(0, max(abs(offset_row), abs(offset_col))):
        line |= 1 << (from_row + step_row*i)*8 + (from_col + step_col*i)

    return line


BISHOP_BETWEEN_MASK = [
    [build_between_diagonal(b_sq, k_sq) for k_sq in range(64)]
    for b_sq in range(64)
]
ROOK_BETWEEN_MASK = [
    [build_between_line(r_sq, k_sq) for k_sq in range(64)]
    for r_sq in range(64)
]


def encode_move(from_sq: int, to_sq: int, flag: int = 0) -> int:
    """Return 16-bit move word (0 ≤ flag ≤ 15)."""
    return (from_sq & 0x3F) | ((to_sq & 0x3F) << 6) | ((flag & 0xF) << 12)


def decode_move(move: int):
    """Return tuple (from_sq, to_sq, flag) from 16-bit word."""
    from_sq = move & 0x3F
    to_sq = (move >> 6) & 0x3F
    flag = move >> 12        # already only 4 bits
    return from_sq, to_sq, flag

@dataclass
class TTEntry:
    key:  int
    depth: int
    flag:  int        # EXACT / LOWER / UPPER
    score: int
    move:  int 


EXACT, LOWER, UPPER = 0, 1, 2

WHITE_KING_EMPTY = 0x0000000000000060  # f1, g1
WHITE_QUEEN_EMPTY = 0x000000000000000E  # b1, c1, d1
BLACK_KING_EMPTY = 0x6000000000000000  # f8, g8
BLACK_QUEEN_EMPTY = 0x0E00000000000000  # b8, c8, d8
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
# build_bishop_table(26)
