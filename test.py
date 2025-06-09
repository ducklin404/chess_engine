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



print(bin(build_between_diagonal(53, 52)))
