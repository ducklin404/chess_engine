from compute_helper import *



class ChessLogic:
    def __init__(self):
        self.side = 'white'
        self.en_passant = None
        self.white_king_castle = True
        self.black_king_castle = True
        self.black_queen_castle = True
        self.white_queen_castle = True
        self.history = []
        self.piece_at = INITIAL_PIECE_AT
        self.bb = self.fen_to_bitboard(init_fen)
        self.build_occ()

    
    
        
    def fen_to_bitboard(self, fen: str):
        char_to_index = {
            'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5}
        piece_bb = [[0] * 6] *2
        board = fen.split(' ')[0] 
        count = 56
        # because fen is so stupid and mark from 8th rank so the start will be 56-63
        for cell in board:
            if cell == '/':
                count -= 16
            elif cell.isnumeric():
                count += int(cell)
            else:
                side = 1 if cell.islower() else 0
                piece_bb[side][char_to_index[cell]] |= (1 << count)
                count += 1
            
                
        return piece_bb
    
    
    
    def push(self, encoded_move):
        from_sq, to_sq, flag = decode_move(encoded_move=encoded_move)
        
        moving_piece = self.piece_at[from_sq]          
        our_side = moving_piece // 6 
        other_side = our_side ^ 1              
        piece_code = moving_piece % 6               

        from_bb = SQ_MASK[from_sq]
        to_bb   = SQ_MASK[to_sq]
        
        

        # 1. pull the piece off its origin square
        self.bb[our_side][piece_code] ^= from_bb              
        self.occ[our_side] ^= from_bb
        self.all_occ ^= from_bb
        self.piece_at[from_sq] = NO_PIECE
        
        # 2. capture or en passant processing
        cap_piece = NO_PIECE
        if flag & 4:
            cap_sq = to_sq
            if flag == 5:
                cap_sq += -8 if our_side == WHITE else 8
            cap_piece = self.piece_at[cap_sq] % 6
            
            
            cap_bb = SQ_MASK[cap_sq]
            self.bb[other_side][cap_piece] ^= cap_bb
            self.occ[other_side] ^= cap_bb
            self.all_occ ^= cap_bb
            self.piece_at[cap_sq] = NO_PIECE
            
        # 3. adjust which piece land on to_sq and move the rook if castle
        landing = moving_piece
        
        if 8 <= flag <= 15:
            landing = (flag & 3) + 1
        elif flag in (2, 3):
            rk_from = (7 if flag == 2 else 0) ^ (our_side * 56)
            rk_to   = (5 if flag == 2 else 3) ^ (our_side * 56)

            rk_bb = SQ_MASK[rk_from] | SQ_MASK[rk_to]
            
            self.bb[ROOK + 6*our_side] ^= rk_bb
            self.occ[our_side] ^= rk_bb
            self.all_occ ^= rk_bb
            self.piece_at[rk_from] = NO_PIECE
            self.piece_at[rk_to] = ROOK + 6*our_side
            
        # 4. move the piece to landing
        self.bb[our_side][landing] ^= to_bb
        self.occ[our_side] ^= to_bb
        self.all_occ ^= to_bb
        self.piece_at[to_sq] = landing + our_side*6
        
        
        # 5. save history to revesve later

        castle_mask_before = pack_castle(
            self.white_king_castle, self.white_queen_castle,
            self.black_king_castle, self.black_queen_castle
        )
        
        self.history.append(
            HistoryEntry(
                encoded_move     = encoded_move,
                captured         = cap_piece,
                prev_ep          = self.en_passant,
                castle_mask      = castle_mask_before
            )
        )
        
        # 6. mark en passant and castling right
        if piece_code == PAWN and abs(to_sq - from_sq) == 16:
            self.en_passant = (from_sq + to_sq) // 2
        else:
            self.en_passant = None
        
        if piece_code == KING:
            if our_side == WHITE:
                self.white_queen_castle = False
                self.white_king_castle = False
            else:
                self.black_queen_castle = False
                self.black_king_castle = False
        if piece_code == ROOK:
            if our_side == WHITE:
                if from_sq == 0:
                    self.white_queen_castle = False
                elif from_sq == 7:
                    self.white_king_castle = False
            else:
                if from_sq == 56:
                    self.black_queen_castle = False
                elif from_sq == 63:
                    self.black_king_castle = False
        elif cap_piece == ROOK:
            if   to_sq == 0:   self.white_queen_castle  = False
            elif to_sq == 7:   self.white_king_castle   = False
            elif to_sq == 56:  self.black_queen_castle  = False
            elif to_sq == 63:  self.black_king_castle   = False
                
        
        # 7. flip the side
        self.side_to_move ^= 1  

    def unpush(self):
        
        # 1. decode everything
        last_move: HistoryEntry = self.history.pop()
        from_sq, to_sq, flag = decode_move(last_move.encoded_move)
        moving_piece = self.piece_at[to_sq]           
        our_side    = moving_piece // 6
        other_side  = our_side ^ 1
        piece_code  = moving_piece % 6   
        
        from_bb = SQ_MASK[from_sq]
        to_bb   = SQ_MASK[to_sq]   
        
        # 2. clear the to square
        self.bb[our_side][piece_code] ^= to_bb
        self.occ[our_side] ^= to_bb
        self.all_occ       ^= to_bb
        self.piece_at[to_sq] = NO_PIECE
        
        
        # 3. restore captured piece if any
        if last_move.captured != NO_PIECE:
            capt_piece  = last_move.captured
            cap_sq     = to_sq if flag != 5 else (to_sq + (-8 if our_side == WHITE else 8))
            cap_bb     = SQ_MASK[cap_sq]

            self.bb[other_side][capt_piece] ^= cap_bb
            self.occ[other_side] ^= cap_bb
            self.all_occ ^= cap_bb
            self.piece_at[cap_sq] = last_move.captured + 6*other_side
            
        # 4. undo promotions / castling
        landing_code = piece_code
        if 8 <= flag <= 15:                         # promotion
            landing_code = PAWN
        elif flag in (2, 3):                        # castling
            rk_from = (7 if flag == 2 else 0) ^ (our_side * 56)
            rk_to   = (5 if flag == 2 else 3) ^ (our_side * 56)
            rk_bb   = SQ_MASK[rk_from] | SQ_MASK[rk_to]

            self.bb[our_side][ROOK] ^= rk_bb
            self.occ[our_side]      ^= rk_bb
            self.all_occ            ^= rk_bb
            self.piece_at[rk_to]     = NO_PIECE
            self.piece_at[rk_from]   = ROOK + 6*our_side

        # finally drop the piece back on its origin square
        self.bb[our_side][landing_code] ^= from_bb
        self.occ[our_side] ^= from_bb
        self.all_occ       ^= from_bb
        self.piece_at[from_sq] = landing_code + 6*our_side

        # 5. restore EP and castling rights
        self.en_passant    = last_move.prev_ep
        wk,wq,bk,bq        = unpack_castle(last_move.castle_mask)
        self.white_king_castle, self.white_queen_castle = wk, wq
        self.black_king_castle, self.black_queen_castle = bk, bq

        # 6. flip side
        self.side_to_move ^= 1
                
        
        
        
    
    def build_occ(self):
        WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK = self.bb
        self.occ = [0] * 2
        self.occ[0] = WP | WN | WB | WR | WQ | WK
        self.occ[1] = BP | BN | BB | BR | BQ | BK
        self.all_occ = self.occ[0] | self.occ[1]
    
    def calculate_king_moves(self, sq, same_side_occ, all_occ, attacked_sqs, side = 'white'):
        moves = KING_TABLE[sq] & ~same_side_occ & ~attacked_sqs
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
                pawn_movable = self.calculate_pawn_moves(i, all_occ, all_occ, black_occ, 'black')
                black_can_capture |= pawn_movable
                bits &= bits - 1

            # Black Knights
            bits = _BN
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                knight_movable = KNIGHT_TABLE[i]
                black_can_capture |= knight_movable
                bits &= bits - 1

            # Black King
            bits = _BK
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                king_movable = self.calculate_king_moves(i, 0b0, all_occ, 0b0, 'black')
                black_can_capture |= king_movable
                bits &= bits - 1

            # Black Rooks
            bits = _BR
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = ROOK_RELEVANT_MASK[i] & all_occ
                magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_movable = ROOK_TABLE[i][magic_index]
                black_can_capture |= rook_movable
                bits &= bits - 1

            # Black Bishops
            bits = _BB
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_movable = BISHOP_TABLE[i][magic_index]
                
                black_can_capture |= bishop_movable
                bits &= bits - 1

            # Black Queens
            bits = _BQ
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_rook_occ = ROOK_RELEVANT_MASK[i] & all_occ
                rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_moves = ROOK_TABLE[i][rook_magic_index]

                relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & all_occ
                bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_moves = BISHOP_TABLE[i][bishop_magic_index]

                queen_movable = rook_moves | bishop_moves
                black_can_capture |= queen_movable
                bits &= bits - 1
            
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
                    sq, all_occ, all_occ, black_occ, "white"
                )
                bits &= bits - 1
            # Knights
            bits = _WN
            while bits:
                lsb = bits & -bits
                sq  = lsb.bit_length() - 1
                white_can_capture |= KNIGHT_TABLE[sq]
                bits &= bits - 1
            # King
            sq = _WK.bit_length() - 1 if _WK else -1
            if sq >= 0:
                white_can_capture |= self.calculate_king_moves(
                    sq, 0b0, all_occ, 0, "white"
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
                    white_can_capture |= table[sq][mi]
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
                white_can_capture |= (r_mv | b_mv)
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