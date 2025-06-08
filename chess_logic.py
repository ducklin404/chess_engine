from compute_helper import *



class ChessLogic:
    def __init__(self):
        self.side = WHITE
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
        piece_bb = [[0]*6 for _ in range(2)]
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
                piece_bb[side][char_to_index[cell.upper()]] |= (1 << count)
                count += 1
            
                
        return piece_bb
    
    
    
    def push(self, encoded_move):
        from_sq, to_sq, flag = decode_move(encoded_move)
        print('from and to', from_sq, to_sq)
        print(self.piece_at[from_sq])
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
        landing = piece_code
        
        if 8 <= flag <= 15:
            landing = (flag & 3) + 1
        elif flag in (2, 3):
            rk_from = (7 if flag == 2 else 0) ^ (our_side * 56)
            rk_to   = (5 if flag == 2 else 3) ^ (our_side * 56)

            rk_bb = SQ_MASK[rk_from] | SQ_MASK[rk_to]
            
            self.bb[our_side][ROOK] ^= rk_bb
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
        self.side ^= 1  

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
        self.side ^= 1
        
    def get_chess_board(self):
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
        count = 0
        for i in range(64):
            ui_table[7-(i // 8)].append(index_to_char[self.piece_at[i]])
            
        return ui_table
            
    
    def get_flag(self, from_sq, to_sq, promo = None):
        flag = 0
        moving_piece = self.piece_at[from_sq]
        our_side = moving_piece // 6
        piece_code = moving_piece % 6
        
        if piece_code == PAWN:
            if promo:
                captured = 4 if self.piece_at[to_sq] != NO_PIECE else 0
                flag = promo + captured
            elif abs(to_sq - from_sq) == 16:
                flag == DOUBLE_PUSH
            elif abs(to_sq - from_sq) != 8 and self.piece_at[to_sq] == NO_PIECE:
                flag = EN_PASSANT
            elif self.piece_at[to_sq] != NO_PIECE:
                flag = CAPTURE
        elif piece_code == KING:
            if abs(to_sq - from_sq) == 2:
                if to_sq == 2 or to_sq == 58:
                    flag = CASTLE_QUEEN
                else:
                    flag = CASTLE_KING
                    
            else:
                if self.piece_at[to_sq] != NO_PIECE:
                    flag = CAPTURE
        else:
            if self.piece_at[to_sq] != NO_PIECE:
                flag = CAPTURE
            
        
        
        
        return flag
        
        
    def add_flag(self, piece_type, from_sq, to_sq) -> list:
        encoded_moves = []
        if piece_type == KING:
            if abs(to_sq - from_sq) == 2:
                if to_sq == 2 or to_sq == 58:
                    encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = CASTLE_QUEEN))
                else:
                    encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = CASTLE_KING))
                    
            else:
                if self.piece_at[to_sq] == NO_PIECE:
                    encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = 0))
                else:
                    encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = CAPTURE))
        elif piece_type == PAWN:
            if 56 <= to_sq <= 63 or 0 <= to_sq <= 7:
                captured = 4 if self.piece_at[to_sq] != NO_PIECE else 0
                for i in range(8, 12):
                    encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = i + captured))
            
            elif abs(to_sq - from_sq) == 16:
                encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = DOUBLE_PUSH))
            elif abs(to_sq - from_sq) != 8 and self.piece_at[to_sq] == NO_PIECE:
                encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = EN_PASSANT))
            elif self.piece_at[to_sq] != NO_PIECE:
                encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = CAPTURE))
            else:
                encoded_moves.append(encode_move(from_sq=from_sq, to_sq=to_sq, flag = 0))
            
        return encoded_moves
        
    
    def build_occ(self):
        WP, WN, WB, WR, WQ, WK = self.bb[0]
        BP, BN, BB, BR, BQ, BK = self.bb[1]
        self.occ = [0] * 2
        self.occ[0] = WP | WN | WB | WR | WQ | WK
        self.occ[1] = BP | BN | BB | BR | BQ | BK
        self.all_occ = self.occ[0] | self.occ[1]
    
    def calculate_king_moves(self, sq, same_side_occ, all_occ, attacked_sqs, side = WHITE):
        moves = KING_TABLE[sq] & ~same_side_occ & ~attacked_sqs
        if not attacked_sqs & (1<< sq):
            if side == WHITE:
                if self.white_king_castle:
                    if not (WHITE_KING_EMPTY & all_occ):
                        if not attacked_sqs & 0b1110000:
                            moves |= 0b1000000
                if self.white_queen_castle:
                    if not (WHITE_QUEEN_EMPTY & all_occ):
                        if not attacked_sqs & 0b11100:
                            moves |= 0b100
            else:
                if self.black_king_castle:
                    if not (BLACK_KING_EMPTY & all_occ):
                        if not attacked_sqs & (0b1110000 << 56):
                            moves |= 0b1000000 << 56    
                if self.black_queen_castle:
                    if not (BLACK_QUEEN_EMPTY & all_occ):
                        if not attacked_sqs & (0b11100 << 56):
                            moves |= 0b100 << 56
                
        return moves
    
    
    def calculate_pawn_moves(self, sq, all_occ, white_occ, black_occ, side = WHITE):
        moves = 0
        row, col = divmod(sq, 8)
        if side == WHITE:
            # calculate the attack squares
            moves |= black_occ & WHITE_PAWN_ATTACK_TABLE[sq]
            
            # double pawn push
            if row == 1 and not (0b100000001 << (row + 1) * 8 + col) & all_occ:
                moves |= 1 << (24 + col)
                
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
            if self.en_passant is not None:
                if row == 3:
                    if col + 1 <= 7:
                        if (row - 1)*8 + (col + 1) == self.en_passant:
                            moves |= 1 << self.en_passant
                    if col -1 >= 0:
                        if (row - 1)*8 + (col - 1) == self.en_passant:
                            moves |= 1 << self.en_passant

        return moves
    
    
    
    def find_available_moves(self):
        our_side = self.side
        other_side = our_side ^ 1
        attacked_mask = 0
        pinned = [0] * 64
        moves: list[int] = []
        checked = 0
        checked_mask = 0
        
        
        
        # start here
        king_sq = self.bb[our_side][KING].bit_length() -1
        # calculate if king is in check or any pin exist and get attacked mask so king can't move there
        # black knight
        bits = self.bb[other_side][KNIGHT]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _knight_mask = KNIGHT_TABLE[sq] & self.bb[our_side][KING]
            if _knight_mask:
                checked += 1
                checked_mask = 1 << sq
            knight_movable = KNIGHT_TABLE[sq]
            attacked_mask |= knight_movable
            bits &= bits - 1

        # Black Bishops
        bits = self.bb[other_side][BISHOP]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _bishop_mask = BISHOP_BETWEEN_MASK[sq][king_sq] & self.all_occ
            if _bishop_mask.bit_count() == 1:
                checked += 1
                checked_mask = BISHOP_BETWEEN_MASK[sq][king_sq]
            elif _bishop_mask.bit_count() == 2:
                blocker_bb   = _bishop_mask & self.occ[our_side]    
                if blocker_bb:     
                    blocker_sq   = blocker_bb.bit_length() - 1      
                    pinned[blocker_sq ] = BISHOP_BETWEEN_MASK[sq][king_sq]
                    
            relevant_occ = BISHOP_RELEVANT_MASK[sq] & self.all_occ
            magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[sq], BISHOP_RELEVEANT_BITS[sq])
            bishop_movable = BISHOP_TABLE[sq][magic_index]
            
            attacked_mask |= bishop_movable        
            
            bits &= bits - 1
            

        # Black Pawns
        bits = self.bb[other_side][PAWN]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _pawn_mask = BLACK_PAWN_ATTACK_TABLE[sq] & self.bb[our_side][KING]
            if _pawn_mask:
                checked += 1
                checked_mask = 1 << sq
            pawn_movable = self.calculate_pawn_moves(sq, self.all_occ, self.all_occ, self.occ[other_side], other_side)
            attacked_mask |= pawn_movable
            bits &= bits - 1
            

        # Black Rooks
        bits = self.bb[other_side][ROOK]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _rook_mask = ROOK_BETWEEN_MASK[sq][king_sq] & self.all_occ
            if _rook_mask.bit_count() == 1:
                checked += 1
                checked_mask = ROOK_BETWEEN_MASK[sq][king_sq]
            elif _rook_mask.bit_count() == 2:
                blocker_bb = _rook_mask & self.occ[our_side]
                if blocker_bb:          
                    pinned[blocker_bb.bit_length() - 1] = ROOK_BETWEEN_MASK[sq][king_sq]
                    
            relevant_occ = ROOK_RELEVANT_MASK[sq] & self.all_occ
            magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[sq], ROOK_RELEVEANT_BITS[sq])
            rook_movable = ROOK_TABLE[sq][magic_index]
            attacked_mask |= rook_movable
            bits &= bits - 1
            
         
        # Black Queens
        bits = self.bb[other_side][QUEEN]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _bishop_mask = BISHOP_BETWEEN_MASK[sq][king_sq] & self.all_occ
            if _bishop_mask.bit_count() == 1:
                checked += 1
                checked_mask = BISHOP_BETWEEN_MASK[sq][king_sq]
            elif _bishop_mask.bit_count() == 2:
                blocker_bb   = _bishop_mask & self.occ[our_side]    
                if blocker_bb:     
                    blocker_sq   = blocker_bb.bit_length() - 1      
                    pinned[blocker_sq ] = BISHOP_BETWEEN_MASK[sq][king_sq]
            _rook_mask = ROOK_BETWEEN_MASK[sq][king_sq] & self.all_occ
            if _rook_mask.bit_count() == 1:
                checked += 1
                checked_mask = ROOK_BETWEEN_MASK[sq][king_sq]
            elif _rook_mask.bit_count() == 2:
                blocker_bb = _rook_mask & self.occ[our_side]
                if blocker_bb:          
                    pinned[blocker_bb.bit_length() - 1] = ROOK_BETWEEN_MASK[sq][king_sq]
            
            
 
            relevant_rook_occ = ROOK_RELEVANT_MASK[sq] & self.all_occ
            rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[sq], ROOK_RELEVEANT_BITS[sq])
            rook_moves = ROOK_TABLE[sq][rook_magic_index]

            relevant_bishop_occ = BISHOP_RELEVANT_MASK[sq] & self.all_occ
            bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[sq], BISHOP_RELEVEANT_BITS[sq])
            bishop_moves = BISHOP_TABLE[sq][bishop_magic_index]

            queen_movable = rook_moves | bishop_moves
            attacked_mask |= queen_movable
            
            bits &= bits - 1
            
            
        print(checked)
        
        # Black King
        bits = self.bb[other_side][KING]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            king_movable = self.calculate_king_moves(sq, 0b0, self.all_occ, 0b0, other_side)
            attacked_mask |= king_movable
            bits &= bits - 1
        
        # start to find legal moves for our side
        # King
        bits = self.bb[our_side][KING]
        while bits:
            lsb = bits & -bits
            i = lsb.bit_length() - 1
            king_movable = self.calculate_king_moves(i, self.occ[our_side], self.all_occ, attacked_mask, self.side)
            while king_movable:
                lsb = king_movable & -king_movable
                to_sq = lsb.bit_length() -1
                moves += self.add_flag(KING, i, to_sq = to_sq)
                king_movable &= king_movable -1
            bits &= bits - 1
            
        if checked <= 1:
            # Pawns
            bits = self.bb[our_side][PAWN]
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                pawn_movable = self.calculate_pawn_moves(i, self.all_occ, self.occ[our_side], self.occ[other_side], self.side)
                if pinned[i]:
                    pawn_movable &= pinned[i]
                if checked:
                    pawn_movable &= checked_mask
                while pawn_movable:
                    lsb = pawn_movable & -pawn_movable
                    to_sq = lsb.bit_length() - 1
                    moves+= self.add_flag(PAWN, from_sq= i, to_sq=to_sq)
                    pawn_movable &= pawn_movable -1
                bits &= bits - 1

            # Knights
            bits = self.bb[our_side][KNIGHT]
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                knight_movable = KNIGHT_TABLE[i] & ~self.occ[our_side]
                if pinned[i]:
                    knight_movable &= pinned[i]
                if checked:
                    knight_movable &= checked_mask
                while knight_movable:
                    lsb = knight_movable & -knight_movable
                    to_sq = lsb.bit_length() - 1                
                    if self.piece_at[to_sq] == NO_PIECE:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = 0))
                    else:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = CAPTURE))
                    knight_movable &= knight_movable-1
                bits &= bits - 1

            

            # Rooks
            bits = self.bb[our_side][ROOK]
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = ROOK_RELEVANT_MASK[i] & self.all_occ
                magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_movable = ROOK_TABLE[i][magic_index] & ~self.occ[our_side]
                if pinned[i]:
                    rook_movable &= pinned[i]
                if checked:
                    rook_movable &= checked_mask
                while rook_movable:
                    lsb = rook_movable & -rook_movable
                    to_sq = lsb.bit_length() - 1                
                    if self.piece_at[to_sq] == NO_PIECE:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = 0))
                    else:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = CAPTURE))
                    rook_movable &= rook_movable-1
                bits &= bits - 1

            # Bishops
            bits = self.bb[our_side][BISHOP]
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_occ = BISHOP_RELEVANT_MASK[i] & self.all_occ
                magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_movable = BISHOP_TABLE[i][magic_index] & ~self.occ[our_side]
                if pinned[i]:
                    bishop_movable &= pinned[i]
                if checked:
                    bishop_movable &= checked_mask
                while bishop_movable:
                    lsb = bishop_movable & -bishop_movable
                    to_sq = lsb.bit_length() - 1                
                    if self.piece_at[to_sq] == NO_PIECE:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = 0))
                    else:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = CAPTURE))
                    bishop_movable &= bishop_movable -1
                bits &= bits - 1

            # Queens
            bits = self.bb[our_side][QUEEN]
            while bits:
                lsb = bits & -bits
                i = lsb.bit_length() - 1
                relevant_rook_occ = ROOK_RELEVANT_MASK[i] & self.all_occ
                rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[i], ROOK_RELEVEANT_BITS[i])
                rook_moves = ROOK_TABLE[i][rook_magic_index] & ~self.occ[our_side]
                

                relevant_bishop_occ = BISHOP_RELEVANT_MASK[i] & self.all_occ
                bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[i], BISHOP_RELEVEANT_BITS[i])
                bishop_moves = BISHOP_TABLE[i][bishop_magic_index] & ~self.occ[our_side]
                

                queen_movable = rook_moves | bishop_moves
                if pinned[i]:
                    queen_movable &= pinned[i]
                if checked:
                    queen_movable &= checked_mask
                while queen_movable:
                    lsb = queen_movable & -queen_movable
                    to_sq = lsb.bit_length() - 1                
                    if self.piece_at[to_sq] == NO_PIECE:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = 0))
                    else:
                        moves.append(encode_move(from_sq=i, to_sq = to_sq, flag = CAPTURE))
                    queen_movable &= queen_movable -1
                bits &= bits - 1

        return moves
        
    
    def moves_to_data(self, moves: list[int]):
        result = [0] * 64
        for move in moves:
            from_sq, to_sq, flag = decode_move(move)
            result[from_sq] |= 1 << to_sq
            
        return result
        
            
            
if __name__ == "__main__":
    logic = ChessLogic()
    # fen = 'rnbqk2r/pppp1ppp/5n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1'
    # bb = logic.fen_to_bitboard(fen)
    result = logic.find_available_moves()
    for move in result:
        print(bin(move))
        

