"""High level game management helpers."""

from engine.chess_logic import ChessLogic
from engine.constants import BLACK

class Game:
    """Wrap ``ChessLogic`` and expose helpers for the UI layer."""
    def __init__(self):
        self.chess = ChessLogic()
        self.board_state = self.chess.get_chess_board()
        self.is_beginning = True
        self.end = False
        self.moves = [0] * 64
        
    def start(self, side = 'white'):
        """Start a new game.

        If ``side`` is ``"black"`` the engine will immediately play the
        opening move.  ``start`` only performs work the first time it is
        called for a particular game instance.
        """
        if self.is_beginning:
            if side == 'white':
                self.get_moves()
            else:
                self.chess.side = BLACK
                move = self.chess.get_best_move()
                self.chess.push(move)
                self.board_state = self.chess.get_chess_board()
                self.get_moves()
            self.is_beginning = False
            
        
    def get_moves(self):
        """Refresh ``self.moves`` from the underlying logic."""
        moves_bb = self.chess.find_available_moves()
        self.moves = self.chess.moves_to_data(moves_bb)
        
    def reset(self):
        """Return the game back to its initial state."""
        self.chess.restart()
        self.board_state = self.chess.get_chess_board()
        self.is_beginning = True
        self.end = False
        self.moves = [0] * 64
