"""Random Zobrist hashing keys."""

import random

random.seed(42)
def rand64():
    """Return a random 64-bit integer."""
    return random.getrandbits(64)

H_PIECE =  [[[rand64() for _ in range(64)]
                  for _ in range(6)]
                  for _ in range(2)]
H_CASTLE = [rand64() for _ in range(4)]
H_EN_PASSANT = [rand64() for _ in range(8)]
H_BLACK_TO_MOVE = rand64()