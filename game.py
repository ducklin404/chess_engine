from chess_logic import ChessLogic

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
        self.board_state = INITIAL_POSITION
        self.get_moves()
        self.end = False
        
    def get_moves(self):
        moves_bb = self.chess.find_available_moves()
        self.moves = self.chess.moves_to_data(moves_bb)
        
    def reset(self):
        self.board_state = INITIAL_POSITION
        self.get_moves()
        self.end = False