def popcount(x: int) -> int:
    return x.bit_count()


def rank_of(sq: int) -> int:
    return sq >> 3

def submasks(mask: int):
    """Yield all subsets of `mask`, including 0."""
    sub = mask
    while True:
        yield sub
        if sub == 0:
            break
        sub = (sub - 1) & mask

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