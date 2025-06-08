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

NO_PIECE = -1

INITIAL_PIECE_AT = [
    BLACK_ROOK,   BLACK_KNIGHT, BLACK_BISHOP, BLACK_QUEEN, BLACK_KING, BLACK_BISHOP, BLACK_KNIGHT, BLACK_ROOK,   # 8th rank
    BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,  BLACK_PAWN, BLACK_PAWN,   BLACK_PAWN,   BLACK_PAWN,   # 7th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 6th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 5th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 4th rank
    NO_PIECE,     NO_PIECE,     NO_PIECE,     NO_PIECE,    NO_PIECE,   NO_PIECE,     NO_PIECE,     NO_PIECE,     # 3rd rank
    WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,  WHITE_PAWN, WHITE_PAWN,   WHITE_PAWN,   WHITE_PAWN,   # 2nd rank
    WHITE_ROOK,   WHITE_KNIGHT, WHITE_BISHOP, WHITE_QUEEN, WHITE_KING, WHITE_BISHOP, WHITE_KNIGHT, WHITE_ROOK    # 1st rank
]



def get_chess_board():
    ui_table = [[] for _ in range(8)]
    index_to_char = {
        NO_PIECE:     '--', 
        WHITE_PAWN:   'wp',
        WHITE_ROOK:   'wr',
        WHITE_KNIGHT: 'wn',
        WHITE_BISHOP: 'wb',
        WHITE_QUEEN:  'wq',
        WHITE_KING:   'wk',
        BLACK_PAWN:   'bp',
        BLACK_ROOK:   'br',
        BLACK_KNIGHT: 'bn',
        BLACK_BISHOP: 'bb',
        BLACK_QUEEN:  'bq',
        BLACK_KING:   'bk',
    }
    for i in range(64):
        ui_table[i // 8].append(index_to_char[INITIAL_PIECE_AT[i]])
        
    return ui_table


print(get_chess_board())