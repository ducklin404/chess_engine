init_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class ChessLogic:
        
        
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
    
    
    
    def find_available_moves(self, piece_bb: list):
        _WP, _WN, _WB, _WR, _WQ, _WK, _BP, _BN, _BB, _BR, _BQ, _BK = piece_bb
        
        
        
                
            
            
if __name__ == "__main__":
    logic = ChessLogic()
    logic.fen_to_bitboard(init_fen)