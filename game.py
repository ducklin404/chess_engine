from chess_logic import ChessLogic
import copy
from compute_helper import BLACK

INITIAL_POSITION = [
    ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
    ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
    ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
]

class Game:
    def __init__(self):
        self.chess = ChessLogic()
        self.board_state = copy.deepcopy(INITIAL_POSITION)
        self.is_beginning = True
        self.end = False
        self.moves = [0] * 64
        
    def start(self, side = 'white'):
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
        moves_bb = self.chess.find_available_moves()
        self.moves = self.chess.moves_to_data(moves_bb)
        
    def reset(self):
        self.chess.restart()
        self.board_state = copy.deepcopy(INITIAL_POSITION)
        self.is_beginning = True
        self.end = False
        self.moves = [0] * 64
