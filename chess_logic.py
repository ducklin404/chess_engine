init_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
from move_precalculate import *



class ChessLogic:
    def __init__(self):
        self.side = 'white'
        self.en_passant = None
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
    
    def push(self, from_sq, to_sq, piece, captured = None, is_en_passant = False, promote = None):
        if piece == 5:
            self.white_king_castle = False
            self.white_queen_castle = False
        elif piece == 11:
            self.black_king_castle = False
            self.black_queen_castle = False
        if from_sq == 0 or captured == 0:
            self.white_queen_castle = False
        elif from_sq == 7 or to_sq == 7:
            self.white_king_castle = False
        elif from_sq == 56 or captured == 56:
            self.black_queen_castle = False
        elif from_sq == 63 or to_sq == 63:
            self.black_king_castle = False
            
        if piece == 0 and (to_sq - from_sq) == 16:
            self.en_passant = from_sq + 8
        elif piece == 6 and (from_sq - to_sq) == 16:
            self.en_passant = from_sq - 8
        else:
            self.en_passant = None
        from_bb = ~(1 << from_sq) & 0xFFFFFFFFFFFFFFFF
        to_bb = 1 << to_sq
        if promote:
            if 56 <= to_sq <= 63:
                self.bb[0] &= from_bb
                self.bb[promote] |= to_bb
            else:
                self.bb[6] &= from_bb
                self.bb[promote] |= to_bb
        else:
            
            self.bb[piece] &= from_bb
            self.bb[piece] |= to_bb
        if captured is not None:
            self.bb[captured] &= (~to_bb) & 0xFFFFFFFFFFFFFFFF

        if is_en_passant:
            if piece == 0:
                self.bb[6] &= ~ (1 << to_sq - 8)
            else:
                self.bb[0] &= ~(1 << to_sq + 8)
            
        # white 0-0
        if piece == 5 and from_sq == 4 and to_sq == 6:
            self.bb[3] &= ~(1 << 7)      # clear h1
            self.bb[3] |=  (1 << 5)      # set  f1

        # white 0-0-0
        elif piece == 5 and from_sq == 4 and to_sq == 2:
            self.bb[3] &= ~(1 << 0)      # clear a1
            self.bb[3] |=  (1 << 3)      # set  d1

        # black 0-0
        elif piece == 11 and from_sq == 60 and to_sq == 62:
            self.bb[9] &= ~(1 << 63)     # clear h8
            self.bb[9] |=  (1 << 61)     # set  f8

        # black 0-0-0
        elif piece == 11 and from_sq == 60 and to_sq == 58:
            self.bb[9] &= ~(1 << 56)     # clear a8
            self.bb[9] |=  (1 << 59)     # set  d8
            
            
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
    
    def calculate_king_moves(self, sq, white_occ, all_occ, attacked_sqs, side = 'white'):
        moves = KING_TABLE[sq] & ~white_occ & ~attacked_sqs
        print('aaa')
        print(bin(attacked_sqs))
        print(bin(attacked_sqs & 0b1110000))
        print(bin(white_occ))
        print(bin(all_occ))
        print()
        if not attacked_sqs & (1<< sq):
            if side == 'white':
                if self.white_king_castle:
                    if not WHITE_KING_EMPTY & all_occ:
                        if not attacked_sqs & 0b1110000:
                            moves |= 0b1000000
                if self.white_queen_castle:
                    if not WHITE_QUEEN_EMPTY & all_occ:
                        if not attacked_sqs & 0b11100:
                            moves |= 0b10
            else:
                if self.black_king_castle:
                    if not BLACK_KING_EMPTY & all_occ:
                        if not attacked_sqs & (0b1110000 << 56):
                            moves |= 0b1000000 << 56    
                if self.black_queen_castle:
                    if not BLACK_QUEEN_EMPTY & all_occ:
                        if not attacked_sqs & (0b11100 << 56):
                            moves |= 0b10 << 56
                
            return moves
    
    
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
            
            # en passen
            if self.en_passant is not None:
                if row == 4:
                    if col + 1 <= 7:
                        if (row + 1)*8 + (col + 1) == self.en_passant:
                            moves |= 1 << self.en_passant
                    if col -1 >= 0:
                        if (row + 1)*8 + (col - 1) == self.en_passant:
                            moves |= 1 << self.en_passant
                    
                     
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
                    
            # en passen
            if self.en_passant:
                if row == 3:
                    if col + 1 <= 7:
                        if (row - 1)*8 + (col + 1) == self.en_passant:
                            moves |= 1 << self.en_passant
                    if col -1 >= 0:
                        if (row - 1)*8 + (col - 1) == self.en_passant:
                            moves |= 1 << self.en_passant

        return moves
    
    def is_checked(self, black_can_capture, white_can_capture, wk_bb, bk_bb, side = 'white'):
        if side == 'white':
            if black_can_capture & wk_bb:
                return True
        else:
            if white_can_capture & bk_bb:
                return True
        return False
    
    def is_checkmate(self, black_can_move, white_can_move, side = 'white'):
        if side == 'white':
            if white_can_move:
                return False
        else:
            if black_can_move:
                return False
        return True
    
    def restart(self):
        self.side = 'white'
        self.en_passant = None
        self.white_king_castle = True
        self.black_king_castle = True
        self.black_queen_castle = True
        self.white_queen_castle = True
        self.bb = self.fen_to_bitboard(init_fen)
    
    
    def find_available_moves(self, piece_bb: list, side = 'white'):
        _WP, _WN, _WB, _WR, _WQ, _WK, _BP, _BN, _BB, _BR, _BQ, _BK = piece_bb
        white_occ, black_occ, all_occ, empty_occ = self.build_occ(_WP, _WN, _WB, _WR, _WQ, _WK, _BP, _BN, _BB, _BR, _BQ, _BK)
        white_can_capture = 0
        black_can_capture = 0
        pinned = [0] * 64
        moves = [0] * 64
        checked = 0
        checked_mask = 0
        if side == 'white':
            king_sq = _WK.bit_length() -1
            # calculate if king is in check or any pin exist
            # black knight
            bits = _BN
            while bits:
                lsb = bits & -bits
                sq = lsb.bit_length() - 1
                _knight_mask = KNIGHT_TABLE[sq] & _WK
                if _knight_mask:
                    checked += 1
                    checked_mask = 1 << sq
                bits &= bits - 1

            # Black Bishops
            bits = _BB
            while bits:
                lsb = bits & -bits
                sq = lsb.bit_length() - 1
                _bishop_mask = BISHOP_BETWEEN_MASK[sq][king_sq] & all_occ
                if _bishop_mask.bit_count() == 1:
                    checked += 1
                    checked_mask = BISHOP_BETWEEN_MASK[sq][king_sq]
                elif _bishop_mask.bit_count() == 2:
                    blocker_bb   = _bishop_mask & white_occ    
                    if blocker_bb:     
                        blocker_sq   = blocker_bb.bit_length() - 1      
                        pinned[blocker_sq ] = BISHOP_BETWEEN_MASK[sq][king_sq]
                bits &= bits - 1

            # Black Pawns
            bits = _BP
            while bits:
                lsb = bits & -bits
                sq = lsb.bit_length() - 1
                _pawn_mask = BLACK_PAWN_ATTACK_TABLE[sq] & _WK
                if _pawn_mask:
                    checked += 1
                    checked_mask = 1 << sq
                bits &= bits - 1

            # Black Rooks
            bits = _BR
            while bits:
                lsb = bits & -bits
                sq = lsb.bit_length() - 1
                _rook_mask = ROOK_BETWEEN_MASK[sq][king_sq] & all_occ
                if _rook_mask.bit_count() == 1:
                    checked += 1
                    checked_mask = ROOK_BETWEEN_MASK[sq][king_sq]
                elif _rook_mask.bit_count() == 2:
                    blocker_bb = _rook_mask & white_occ
                    if blocker_bb:          
                        pinned[blocker_bb.bit_length() - 1] = ROOK_BETWEEN_MASK[sq][king_sq]
                bits &= bits - 1

            # Black Queens
            bits = _BQ
            while bits:
                lsb = bits & -bits
                sq = lsb.bit_length() - 1
                _bishop_mask = BISHOP_BETWEEN_MASK[sq][king_sq] & all_occ
                if _bishop_mask.bit_count() == 1:
                    checked += 1
                    checked_mask = BISHOP_BETWEEN_MASK[sq][king_sq]
                elif _bishop_mask.bit_count() == 2:
                    blocker_bb   = _bishop_mask & white_occ    
                    if blocker_bb:     
                        blocker_sq   = blocker_bb.bit_length() - 1      
                        pinned[blocker_sq ] = BISHOP_BETWEEN_MASK[sq][king_sq]
                _rook_mask = ROOK_BETWEEN_MASK[sq][king_sq] & all_occ
                if _rook_mask.bit_count() == 1:
                    checked += 1
                    checked_mask = ROOK_BETWEEN_MASK[sq][king_sq]
                elif _rook_mask.bit_count() == 2:
                    blocker_bb = _rook_mask & white_occ
                    if blocker_bb:          
                        pinned[blocker_bb.bit_length() - 1] = ROOK_BETWEEN_MASK[sq][king_sq]
                bits &= bits - 1
            print(checked)
            
            # calculate all place black piece can move
            # Black Pawns
            bits = _BP
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                pawn_movable = self.calculate_pawn_moves(i, all_occ, white_occ, black_occ, side)
                black_can_capture |= pawn_movable
                bits &= bits - 1

            # Black Knights
            bits = _BN
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                knight_movable = KNIGHT_TABLE[i] & ~black_occ
                black_can_capture |= knight_movable
                bits &= bits - 1

            # Black King
            bits = _BK
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                king_movable = self.calculate_king_moves(i, black_occ, all_occ, 0b0, 'black')
                black_can_capture |= king_movable
                bits &= bits - 1

            # Black Rooks
            bits = _BR
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = ROOK_RELEVANT_MASK[i] & all_occ
                magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_movable = ROOK_TABLE[i][magic_index] & ~black_occ
                black_can_capture |= rook_movable
                bits &= bits - 1

            # Black Bishops
            bits = _BB
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_movable = BISHOP_TABLE[i][magic_index] & ~black_occ
                
                black_can_capture |= bishop_movable
                bits &= bits - 1

            # Black Queens
            bits = _BQ
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_rook_occ = ROOK_RELEVANT_MASK[i] & all_occ
                rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_moves = ROOK_TABLE[i][rook_magic_index] & ~black_occ

                relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_moves = BISHOP_TABLE[i][bishop_magic_index] & ~black_occ

                queen_movable = rook_moves | bishop_moves
                black_can_capture |= queen_movable
                bits &= bits - 1
            
            print('original', bin(black_can_capture))
            # start to find legal moves for white
            # King
            bits = _WK
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                king_movable = self.calculate_king_moves(i, white_occ, all_occ, black_can_capture, side)
                
                moves[i] = king_movable
                bits &= bits - 1
            
            if checked <= 1:
                # Pawns
                bits = _WP
                while bits:
                    lsb = bits & -bits
                    i = lsb.bit_length() - 1
                    pawn_movable = self.calculate_pawn_moves(i, all_occ, white_occ, black_occ, side)
                    if pinned[i]:
                        pawn_movable &= pinned[i]
                    if checked:
                        pawn_movable &= checked_mask
                    moves[i] = pawn_movable
                    bits &= bits - 1

                # Knights
                bits = _WN
                while bits:
                    lsb = bits & -bits
                    i = lsb.bit_length() - 1
                    knight_movable = KNIGHT_TABLE[i] & ~white_occ
                    if pinned[i]:
                        knight_movable &= pinned[i]
                    if checked:
                        knight_movable &= checked_mask
                    moves[i] = knight_movable
                    bits &= bits - 1

                

                # Rooks
                bits = _WR
                while bits:
                    lsb = bits & -bits
                    i = lsb.bit_length() - 1
                    relevant_occ = ROOK_RELEVANT_MASK[i] & all_occ
                    magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                    rook_movable = ROOK_TABLE[i][magic_index] & ~white_occ
                    if pinned[i]:
                        rook_movable &= pinned[i]
                    if checked:
                        rook_movable &= checked_mask
                    moves[i] = rook_movable
                    bits &= bits - 1

                # Bishops
                bits = _WB
                while bits:
                    lsb = bits & -bits
                    i = lsb.bit_length() - 1
                    relevant_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                    magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                    bishop_movable = BISHOP_TABLE[i][magic_index] & ~white_occ
                    if pinned[i]:
                        bishop_movable &= pinned[i]
                    if checked:
                        bishop_movable &= checked_mask
                    moves[i] = bishop_movable
                    bits &= bits - 1

                # Queens
                bits = _WQ
                while bits:
                    lsb = bits & -bits
                    i = lsb.bit_length() - 1
                    relevant_rook_occ = ROOK_RELEVANT_MASK[i] & all_occ
                    rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                    rook_moves = ROOK_TABLE[i][rook_magic_index] & ~white_occ
                    

                    relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                    bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                    bishop_moves = BISHOP_TABLE[i][bishop_magic_index] & ~white_occ
                    

                    queen_movable = rook_moves | bishop_moves
                    if pinned[i]:
                        queen_movable &= pinned[i]
                    if checked:
                        queen_movable &= checked_mask
                    white_can_capture |= queen_movable
                    moves[i] = queen_movable
                    bits &= bits - 1
        
        else:  # ------------------------- BLACK TO MOVE ---------------------
            king_sq = _BK.bit_length() - 1
            # -------------------
            # 1. Detect checks / pins coming from WHITE pieces
            # -------------------
            # (a) White Knights
            bits = _WN
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                if KNIGHT_TABLE[sq] & _BK:
                    checked += 1
                    checked_mask |= 1 << sq
                bits &= bits - 1

            # (b) White Bishops / Queens (diagonals)
            bits = _WB | _WQ
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                mask = BISHOP_BETWEEN_MASK[sq][king_sq] & all_occ
                bc   = mask.bit_count()
                if bc == 1:
                    checked += 1
                    checked_mask |= BISHOP_BETWEEN_MASK[sq][king_sq]
                elif bc == 2:
                    blocker_bb = mask & black_occ
                    if blocker_bb:
                        pinned_sq = blocker_bb.bit_length() - 1
                        pinned[pinned_sq] = BISHOP_BETWEEN_MASK[sq][king_sq]
                bits &= bits - 1

            # (c) White Rooks / Queens (orthogonals)
            bits = _WR | _WQ
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                mask = ROOK_BETWEEN_MASK[sq][king_sq] & all_occ
                bc   = mask.bit_count()
                if bc == 1:
                    checked += 1
                    checked_mask |= ROOK_BETWEEN_MASK[sq][king_sq]
                elif bc == 2:
                    blocker_bb = mask & black_occ
                    if blocker_bb:
                        pinned_sq = blocker_bb.bit_length() - 1
                        pinned[pinned_sq] = ROOK_BETWEEN_MASK[sq][king_sq]
                bits &= bits - 1

            # (d) White Pawns
            bits = _WP
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                if WHITE_PAWN_ATTACK_TABLE[sq] & _BK:
                    checked += 1
                    checked_mask |= 1 << sq
                bits &= bits - 1

            # 2. Generate EVERY square white pieces can capture (for king safety)
            bits = _WP
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                white_can_capture |= self.calculate_pawn_moves(
                    sq, all_occ, white_occ, black_occ, "white"
                )
                bits &= bits - 1
            # Knights
            bits = _WN
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                white_can_capture |= KNIGHT_TABLE[sq] & ~white_occ
                bits &= bits - 1
            # King
            sq = _WK.bit_length() - 1 if _WK else -1
            if sq >= 0:
                white_can_capture |= self.calculate_king_moves(
                    sq, white_occ, all_occ, 0, "white"
                )
            # Rooks / Bishops / Queens
            for bb, table, rel_mask, magic, bits_in in (
                (_WR, ROOK_TABLE, ROOK_RELEVANT_MASK, ROOK_MAGIC, ROOK_RELEVEANT_BITS),
                (_WB, BISHOP_TABLE, BISHOP_RELEVANT_MASK, BISHOP_MAGIC, BISHOP_RELEVEANT_BITS),
            ):
                bits = bb
                while bits:
                    lsb = bits & -bits
                    sq  = lsb.bit_length() - 1
                    rel_occ = rel_mask[sq] & all_occ
                    mi       = get_magic_index(rel_occ, magic[sq], bits_in[sq])
                    white_can_capture |= table[sq][mi] & ~white_occ
                    bits &= bits - 1
            # Queens need both rook and bishop moves
            bits = _WQ
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                # rook part
                r_occ = ROOK_RELEVANT_MASK[sq] & all_occ
                r_mi  = get_magic_index(r_occ, ROOK_MAGIC[sq], ROOK_RELEVEANT_BITS[sq])
                r_mv  = ROOK_TABLE[sq][r_mi]
                # bishop part
                b_occ = BISHOP_RELEVANT_MASK[sq] & all_occ
                b_mi  = get_magic_index(b_occ, BISHOP_MAGIC[sq], BISHOP_RELEVEANT_BITS[sq])
                b_mv  = BISHOP_TABLE[sq][b_mi]
                white_can_capture |= (r_mv | b_mv) & ~white_occ
                bits &= bits - 1

            # 3. Generate legal moves for BLACK side
            # ------------------------------------------------------------------
            # (a) King (must avoid white_can_capture)
            if _BK:
                i = king_sq
                king_moves = self.calculate_king_moves(i, black_occ, all_occ, white_can_capture, "black")
                moves[i] = king_moves
                # Allow king moves to be considered in black_can_capture, too
                black_can_capture |= king_moves

            # If we are double‑checked, nothing except the king can move
            if checked <= 1:
                # (b) Pawns
                bits = _BP
                while bits:
                    lsb = bits & -bits
                    i   = lsb.bit_length() - 1
                    pawn_moves = self.calculate_pawn_moves(i, all_occ, white_occ, black_occ, "black")
                    if pinned[i]:
                        pawn_moves &= pinned[i]
                    if checked:
                        pawn_moves &= checked_mask
                    moves[i] = pawn_moves
                    black_can_capture |= pawn_moves
                    bits &= bits - 1

                # (c) Knights
                bits = _BN
                while bits:
                    lsb = bits & -bits
                    i   = lsb.bit_length() - 1
                    knight_moves = KNIGHT_TABLE[i] & ~black_occ
                    if pinned[i]:
                        knight_moves &= pinned[i]
                    if checked:
                        knight_moves &= checked_mask
                    moves[i] = knight_moves
                    black_can_capture |= knight_moves
                    bits &= bits - 1

                # (d) Rooks
                bits = _BR
                while bits:
                    lsb = bits & -bits
                    i   = lsb.bit_length() - 1
                    rel_occ = ROOK_RELEVANT_MASK[i] & all_occ
                    mi      = get_magic_index(rel_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                    rook_moves = ROOK_TABLE[i][mi] & ~black_occ
                    if pinned[i]:
                        rook_moves &= pinned[i]
                    if checked:
                        rook_moves &= checked_mask
                    moves[i] = rook_moves
                    black_can_capture |= rook_moves
                    bits &= bits - 1

                # (e) Bishops
                bits = _BB
                while bits:
                    lsb = bits & -bits
                    i   = lsb.bit_length() - 1
                    rel_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                    mi      = get_magic_index(rel_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                    bishop_moves = BISHOP_TABLE[i][mi] & ~black_occ
                    if pinned[i]:
                        bishop_moves &= pinned[i]
                    if checked:
                        bishop_moves &= checked_mask
                    moves[i] = bishop_moves
                    black_can_capture |= bishop_moves
                    bits &= bits - 1

                # (f) Queens
                bits = _BQ
                while bits:
                    lsb = bits & -bits
                    i   = lsb.bit_length() - 1
                    # rook part
                    r_occ = ROOK_RELEVANT_MASK[i] & all_occ
                    r_mi  = get_magic_index(r_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                    rook_moves = ROOK_TABLE[i][r_mi]
                    # bishop part
                    b_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                    b_mi  = get_magic_index(b_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                    bishop_moves = BISHOP_TABLE[i][b_mi]
                    queen_moves = (rook_moves | bishop_moves) & ~black_occ
                    if pinned[i]:
                        queen_moves &= pinned[i]
                    if checked:
                        queen_moves &= checked_mask
                    moves[i] = queen_moves
                    black_can_capture |= queen_moves
                    bits &= bits - 1

        return moves
        
                
            
            
if __name__ == "__main__":
    logic = ChessLogic()
    fen = 'rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1'
    bb = logic.fen_to_bitboard(fen)
    result = logic.find_available_moves(bb, 'white')
    



0b1111111100010000001111111110110111011010100010010000100000001000
0b1111111100010000001111111110110111011010100010010000100000001000