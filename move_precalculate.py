BISHOP_RELEVEANT_BITS = [
    6, 5, 5, 5, 5, 5, 5, 6,
    5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 7, 7, 7, 7, 5, 5,
    5, 5, 7, 9, 9, 7, 5, 5,
    5, 5, 7, 9, 9, 7, 5, 5,
    5, 5, 7, 7, 7, 7, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5,
    6, 5, 5, 5, 5, 5, 5, 6,
]

ROOK_RELEVEANT_BITS = [
    12, 11, 11, 11, 11, 11, 11, 12,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    11, 10, 10, 10, 10, 10, 10, 11,
    12, 11, 11, 11, 11, 11, 11, 12,
]


ROOK_MAGIC = [
    0x8A80104000800020, 0x0140002000100040, 0x02801880A0017001,
    0x0100081001000420, 0x0200020010080420, 0x03001C0002010008,
    0x0848000800200010, 0x0208008800440290,
    0x0008000982040000, 0x0202440100020004, 0x0010080200080100,
    0x0120800800801000, 0x0208808088000400, 0x0280220080040000,
    0x0220080010002008, 0x0801000060821100,
    0x0800440064220000, 0x0010080802000400, 0x0121080A00102042,
    0x0140848010000802, 0x0481828014002800, 0x0809400400200410,
    0x0401004001001082, 0x0002000088061040,
    0x0100400080208000, 0x0204000212008100, 0x0212006801000081,
    0x0201000800800080, 0x02000A0020040100, 0x0002008080040000,
    0x0800884001001020, 0x0800046000428810,
    0x0404000804080002, 0x0440003000200801, 0x0420001100450000,
    0x0188020010100100, 0x0148004018028000, 0x0208004008080020,
    0x0124080204001001, 0x0200046502000484, 0x0480400080088020,
    0x0100042201003400, 0x0302001001100040, 0x0001000210100009,
    0x0200208010011004, 0x0202008004008002, 0x0200200040101000,
    0x0204844004082001, 0x0101002200408200, 0x0408020004010800,
    0x0400814200441010, 0x02060820C0120200, 0x0001001004080100,
    0x020C020080040080, 0x0293561083002240, 0x0444400410092000,
    0x0280001040802101, 0x0210019004000208, 0x080C008410010200,
    0x0402408100100042, 0x00020030A0244872, 0x0001200100841440,
    0x02006104900A0804, 0x0001004081002402,
]

BISHOP_MAGIC = [
    0x0040040844404084, 0x002004208A004208, 0x0010190041080202,
    0x0108060845042010, 0x0581104180800210, 0x0211208044620001,
    0x0108082082006021, 0x03C0808410220200,
    0x0004050404440404, 0x0000210014200880, 0x024D008080108210,
    0x0001020A0A020400, 0x0004030820004020, 0x0004011002100800,
    0x0004014841041040, 0x0008010104020202,
    0x00400210C3880100, 0x0040402202410820, 0x0008100182002041,
    0x0004002801A02003, 0x0008504082008040, 0x000810102C808880,
    0x0000E90041088480, 0x0008002020480840,
    0x0220200865090201, 0x002010100A020212, 0x0015204840802240,
    0x0002008000208111, 0x0002008610040200, 0x0004804400A0300C,
    0x0000400400410200, 0x0010008040010040,
    0x0044104003501040, 0x0040011A04055100, 0x0004081004C02040,
    0x0040410409000B00, 0x0080801040800000, 0x0001010001040003,
    0x0000401844410000, 0x0002002010484040, 0x0001001048008020,
    0x0004082008080000, 0x00000000200B0400, 0x0000000020181020,
    0x0000020004081820, 0x0002004100040080, 0x0000810200020004,
    0x0000801046008020, 0x0000001020481000, 0x00000030020C0804,
    0x0000001802060080, 0x0006000C01226100, 0x0000010003014400,
    0x000800A600360100, 0x0001000400420000,  # ←-- fixed (was “p000”)
    0x0004010040041000, 0x0000400080100080, 0x0040002040002000,
    0x0000100800200080, 0x0000020080400080, 0x0000100204000200,
    0x0000010080200080, 0x0000200040080010, 0x0000800080010000,
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


def rook_mask(square: int) -> int:
    row, col = divmod(square, 8)
    mask = 0
    # north
    for r in range(row + 1, 7):
        mask |= 1 << (r * 8 + col)
    # south
    for r in range(row - 1, 0, -1):
        mask |= 1 << (r * 8 + col)
    # east
    for c in range(col + 1, 7):
        mask |= 1 << (row * 8 + c)
    # west
    for c in range(col - 1, 0, -1):
        mask |= 1 << (row * 8 + c)
    return mask


def bishop_mask(square: int) -> int:
    row, col = divmod(square, 8)
    mask = 0
    for d_row, d_col in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r, c = row + d_row, col + d_col
        while 0 < r < 7 and 0 < c < 7:
            mask |= 1 << (r * 8 + c)
            r += d_row
            c += d_col
    return mask


def rook_attack(square: int, occ: int):
    row, col = divmod(square, 8)
    atk = 0
    # walk each ray until first blocker
    for r in range(row + 1, 8):
        atk |= 1 << (r * 8 + col)
        if occ & (1 << (r * 8 + col)):
            break
    for r in range(row - 1, -1, -1):
        atk |= 1 << (r * 8 + col)
        if occ & (1 << (r * 8 + col)):
            break
    for c in range(col + 1, 8):
        atk |= 1 << (row * 8 + c)
        if occ & (1 << (row * 8 + c)):
            break
    for c in range(col - 1, -1, -1):
        atk |= 1 << (row * 8 + c)
        if occ & (1 << (row * 8 + c)):
            break
    return atk


def bishop_attack(square: int, occ: int):
    row, col = divmod(square, 8)
    atk = 0

    for d_row, d_col in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r = row + d_row
        c = col + d_col
        while 0 <= r <= 7 and 0 <= c <= 7:
            sq = 1 << r*8 + c
            atk |= sq
            if sq & occ:
                break
            r += d_row
            c += d_col
    return atk


def submasks(mask: int):
    """Yield all subsets of `mask`, including 0."""
    sub = mask
    while True:
        yield sub
        if sub == 0:
            break
        sub = (sub - 1) & mask


def build_rook_table(square: int) -> list[int]:
    mask = rook_mask(square)
    rbits = ROOK_RELEVEANT_BITS[square]
    size = 1 << rbits
    table = [0] * size

    for occ in submasks(mask):
        idx = get_magic_index(occ, ROOK_MAGIC[square], rbits)
        table[idx] = rook_attack(square, occ)

    return table


def build_bishop_table(square: int) -> list[int]:
    mask = bishop_mask(square)
    rbits = BISHOP_RELEVEANT_BITS[square]
    size = 1 << rbits
    table = [0] * size

    for occ in submasks(mask):
        idx = get_magic_index(occ, BISHOP_MAGIC[square], rbits)
        table[idx] = bishop_attack(square, occ)

    return table


def build_between_mask(from_sq, to_sq):
    from_x, from_y = divmod(from_sq, 8)
    to_x, to_y = divmod(to_sq, 8)

WHITE_KING_EMPTY   = 0x0000000000000060  # f1, g1
WHITE_QUEEN_EMPTY  = 0x000000000000000E  # b1, c1, d1
BLACK_KING_EMPTY   = 0x6000000000000000  # f8, g8
BLACK_QUEEN_EMPTY  = 0x0E00000000000000  # b8, c8, d8
WHITE_PAWN_ATTACK_TABLE = [precompute_pawn_attacks(sq, 'white') for sq in range(64)]
BLACK_PAWN_ATTACK_TABLE = [precompute_pawn_attacks(sq, 'black') for sq in range(64)]
ROOK_RELEVANT_MASK = [rook_mask(sq) for sq in range(64)]
BISHOP_RELEVANT_MASK = [bishop_mask(sq) for sq in range(64)]
KING_TABLE = [precompute_king_attacks(sq) for sq in range(64)]
KNIGHT_TABLE = [precompute_knight_attacks(sq) for sq in range(64)]
ROOK_TABLE = [build_rook_table(sq) for sq in range(64)]
BISHOP_TABLE = [build_bishop_table(sq) for sq in range(64)]
# print(ROOK_TABLE)
