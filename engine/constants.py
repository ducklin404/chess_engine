"""Core constants used throughout the engine."""

from ui.config import init_fen


SQ_MASK = [1 << i for i in range(64)]

INF = 999999999
SEEDS = [               # [is64][rank]  – copied from Stockfish
    [8977, 44560, 54343, 38998,  5731, 95205, 104912, 17020],
    [728, 10316, 55013, 32803, 12281, 15100,  16645,   255],
]

MAGIC_FILENAME = "magic_tables.pkl"

PAWN_ADVANCE = [0, 4, 7, 10, 18, 30, 60, 0]   
PASSED_BONUS = 15               
CHECK_BONUS = 800      
MATE = 1_000_000   
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

PIECE_TO_PST = [
    PAWN_PST,
    KNIGHT_PST,
    BISHOP_PST,
    ROOK_PST,
    QUEEN_PST,
    KING_PST_MG,
    KING_PST_EG
]




MASK64 = 0xFFFFFFFFFFFFFFFF
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


MIDDLE_GAME = 0
END_GAME = 1

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

INITIAL_PIECE_AT = [
    WHITE_ROOK,   WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK,
    WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,  WHITE_PAWN, WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 6th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 5th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 4th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 3rd rank
    BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,  BLACK_PAWN, BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   # 7th rank
    BLACK_ROOK,   BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK
]

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

EXACT, LOWER, UPPER = 0, 1, 2

WHITE_KING_EMPTY = 0x0000000000000060  # f1, g1
WHITE_QUEEN_EMPTY = 0x000000000000000E  # b1, c1, d1
BLACK_KING_EMPTY = 0x6000000000000000  # f8, g8
BLACK_QUEEN_EMPTY = 0x0E00000000000000  # b8, c8, d8

