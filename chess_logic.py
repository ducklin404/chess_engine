init_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
from move_precalculate import *



class ChessLogic:
    def __init__(self):
        self.side = 'white'
        self.en_passen = None
        self.white_king_castle = True
        self.black_king_castle = True
        self.black_queen_castle = True
        self.white_queen_castle = True
        self.bb = self.fen_to_bitboard(init_fen)


        
    def fen_to_bitboard(self, fen: str):
        char_to_index = {
            'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
            'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
        }
        piece_bb = [0] * 12
        board = fen.split(' ')[0] 
        count = 56
        # because fen is so stupid and mark from 8th rank so the start will be 56-63
        for cell in board:
            if cell == '/':
                count -= 16
            elif cell.isnumeric():
                count += int(cell)
            else:
                piece_bb[char_to_index[cell]] = piece_bb[char_to_index[cell]] | (1 << count)
                count += 1
            
                
        return piece_bb
    
    def push(self, from_sq, to_sq, piece, captured = None):
        from_bb = ~(1 << from_sq) & 0xFFFFFFFFFFFFFFFF
        to_bb = 1 << to_sq
        print(bin(to_bb))
        print(bin(self.bb[piece]))
        self.bb[piece] &= from_bb
        self.bb[piece] |= to_bb
        print(bin(self.bb[piece]))
        if captured:
            self.bb[captured] &= (~to_bb) & 0xFFFFFFFFFFFFFFFF
            
        if self.side == 'white':
            self.side = 'black'
        else:
            self.side = 'white'

    
    def build_occ(self, WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK):
        white_occ = WP | WN | WB | WR | WQ | WK
        black_occ = BP | BN | BB | BR | BQ | BK
        all_occ = white_occ | black_occ
        empty_occ = 0xFFFFFFFFFFFFFFFF & (~all_occ)
        return white_occ, black_occ, all_occ, empty_occ
    
    def calculate_pawn_moves(self, sq, all_occ, white_occ, black_occ, side = 'white'):
        moves = 0
        row, col = divmod(sq, 8)
        if side == 'white':
            # calculate the attack squares
            moves |= black_occ & WHITE_PAWN_ATTACK_TABLE[sq]
            
            # double pawn push
            if row == 1 and not (0b100000001 << (row + 1) * 8 + col) & all_occ:
                moves |= 1 << 24 + col
                
            # single pawn push
            if row < 7:
                if (1 << (row + 1)*8 + col) & ~all_occ:
                    moves |= 1 << (row + 1)*8 +col
        else:
            # calculate the attack squares
            moves |= white_occ & BLACK_PAWN_ATTACK_TABLE[sq]
            
            # double pawn push
            if row == 6 and not (0b100000001 << (row - 2) * 8 + col) & all_occ:
                moves |= 1 << 32 + col
            
            # single pawn push
            if row > 0:
                if (1 << (row - 1)*8 + col) & ~all_occ:
                    moves |= 1 << (row - 1)*8 +col

        return moves
    
    
    def find_available_moves(self, piece_bb: list, side = 'white'):
        _WP, _WN, _WB, _WR, _WQ, _WK, _BP, _BN, _BB, _BR, _BQ, _BK = piece_bb
        white_occ, black_occ, all_occ, empty_occ = self.build_occ(_WP, _WN, _WB, _WR, _WQ, _WK, _BP, _BN, _BB, _BR, _BQ, _BK)
        moves = [0] * 64
        
        if side == 'white':
            for i in range(0, 64):
                if white_occ & (1 << i):
                    if _WP & (1 << i):
                        moves[i] = self.calculate_pawn_moves(i, all_occ, white_occ, black_occ, side)
                    elif _WN & (1 << i):
                        moves[i] = KNIGHT_TABLE[i] & ~white_occ
                    elif _WK & (1 << i):
                        moves[i] = KING_TABLE[i] & ~white_occ
                    elif _WR & (1 << i):
                        relevant_occ = ROOK_RELEVANT_MASK[i] & all_occ
                        magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                        moves[i] = ROOK_TABLE[i][magic_index] & ~white_occ
                    elif _WB & (1 << i):
                        relevant_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                        magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                        moves[i] = BISHOP_TABLE[i][magic_index] & ~white_occ
                    elif _WQ & (1 << i):
                        relevant_rook_occ = ROOK_RELEVANT_MASK[i] & all_occ
                        rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                        rook_moves = ROOK_TABLE[i][rook_magic_index] & ~white_occ
                        
                        relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                        bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                        bishop_moves = BISHOP_TABLE[i][bishop_magic_index] & ~white_occ
                        
                        moves[i] = rook_moves | bishop_moves
        
        else:
            for i in range(0, 64):
                if black_occ & (1 << i):
                    if _BP & (1 << i):
                        moves[i] = self.calculate_pawn_moves(i, all_occ, white_occ, black_occ, side)
                    elif _BN & (1 << i):
                        moves[i] = KNIGHT_TABLE[i] & ~black_occ
                    elif _BK & (1 << i):
                        moves[i] = KING_TABLE[i] & ~black_occ
                    elif _BR & (1 << i):
                        relevant_occ = ROOK_RELEVANT_MASK[i] & all_occ
                        magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                        moves[i] = ROOK_TABLE[i][magic_index] & ~black_occ
                    elif _BB & (1 << i):
                        relevant_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                        magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                        moves[i] = BISHOP_TABLE[i][magic_index] & ~black_occ
                    elif _BQ & (1 << i):
                        relevant_rook_occ = ROOK_RELEVANT_MASK[i] & all_occ
                        rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                        rook_moves = ROOK_TABLE[i][rook_magic_index] & ~black_occ
                        
                        relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                        bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                        bishop_moves = BISHOP_TABLE[i][bishop_magic_index] & ~black_occ
                        
                        moves[i] = rook_moves | bishop_moves
        return moves
        
                
            
            
if __name__ == "__main__":
    logic = ChessLogic()
    fen = 'rnbqk1nr/pppp1ppp/8/4p3/1bB1P3/2P5/PP1P1PPP/RNBQK1NR b KQkq - 0 1'
    bb = logic.fen_to_bitboard(fen)
    result = logic.find_available_moves(bb, 'white')
    print(bin(result[18]))
    
