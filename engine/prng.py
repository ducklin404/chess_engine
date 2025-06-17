"""Pseudo random number generator used for magic number search."""

from engine.constants import MASK64


class PRNG:
    """Simple xorshift based PRNG."""
    
    def __init__(self, seed: int) -> None:
        """Create a new generator with ``seed``."""
        self.s = seed & MASK64

    def rand64(self) -> int:
        """Return the next 64-bit pseudo random number."""
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & MASK64
        x = self.s
        x ^= (x >> 12) & MASK64
        x ^= (x << 25) & MASK64
        x ^= (x >> 27) & MASK64
        return (x * 2685821657736338717) & MASK64

    def sparse_rand(self) -> int:
        """Return a sparse random bitboard."""
        return self.rand64() & self.rand64() & self.rand64()