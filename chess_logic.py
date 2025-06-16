from compute_helper import *



class ChessLogic:
    BOOK: dict[int, list[int]] = {}      
    
    
    def __init__(self):
        self.side = WHITE
        self.en_passant = None
        self.white_king_castle = True
        self.black_king_castle = True
        self.black_queen_castle = True
        self.white_queen_castle = True
        self.attacked_mask = 0
        self.pawn_attack_mask = 0
        self.hash = 0
        self.tt: dict[int, TTEntry] = {} 
        self.history = []
        self.bb = self.fen_to_bitboard(init_fen)
        self.bitboard_to_board()
        self.build_occ()
        self.hash = self.compute_hash()  

    def restart(self):
        self.side = WHITE
        self.en_passant = None
        self.white_king_castle = True
        self.black_king_castle = True
        self.black_queen_castle = True
        self.white_queen_castle = True
        self.attacked_mask = 0
        self.pawn_attack_mask = 0
        self.hash = 0
        self.tt: dict[int, TTEntry] = {} 
        self.history = []
        self.bb = self.fen_to_bitboard(init_fen)
        self.bitboard_to_board()
        self.build_occ()
        self.hash = self.compute_hash()  
    
    def compute_hash(self):
        key = 0
        for sq in range(64):
            p = self.piece_at[sq]
            if p != NO_PIECE:
                side = p // 6
                piece_code = p%6
                key ^= H_PIECE[side][piece_code][sq]
                
        # castling -> 4-bit mask KQkq 0000-1111
        if self.white_king_castle:  key ^= H_CASTLE[0]
        if self.white_queen_castle: key ^= H_CASTLE[1]
        if self.black_king_castle:  key ^= H_CASTLE[2]
        if self.black_queen_castle: key ^= H_CASTLE[3]
        
        # en-passant: store file only if a pawn can capture it 
        if self.en_passant is not None:
            key ^= H_EN_PASSANT[self.en_passant & 7]
            
        if self.side == BLACK:
            key ^= H_BLACK_TO_MOVE
        return key    
    
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
    
        castle_field = fen.split(' ', 1)[1]
        self.white_king_castle  = 'K' in castle_field
        self.white_queen_castle = 'Q' in castle_field
        self.black_king_castle  = 'k' in castle_field
        self.black_queen_castle = 'q' in castle_field
            
                
        return piece_bb
    
    def bitboard_to_board(self):
        self.piece_at = [NO_PIECE ] * 64
        for sq in range(64):
            sq_bb = SQ_MASK[sq]
            for side in (0, 1):
                for piece_type in range (6):
                    if sq_bb & self.bb[side][piece_type]:
                        self.piece_at[sq] = piece_type + side*6
    
    
    
    def push(self, encoded_move):
        from_sq, to_sq, flag = decode_move(encoded_move)
        moving_piece = self.piece_at[from_sq]          
        our_side = moving_piece // 6 
        other_side = our_side ^ 1              
        piece_code = moving_piece % 6               

        from_bb = SQ_MASK[from_sq]
        to_bb   = SQ_MASK[to_sq]
        prev_hash = self.hash
        

        # 1. pull the piece off its origin square
        self.bb[our_side][piece_code] ^= from_bb              
        self.occ[our_side] ^= from_bb
        self.all_occ ^= from_bb
        self.piece_at[from_sq] = NO_PIECE
        self.hash ^= H_PIECE[our_side][piece_code][from_sq]
        
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
            self.hash ^= H_PIECE[other_side][cap_piece][cap_sq]
            
            
        # 3. adjust which piece land on to_sq and move the rook if castle
        landing = piece_code
        
        if flag & 8:
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
            self.hash ^= H_PIECE[our_side][ROOK][rk_from]
            self.hash ^= H_PIECE[our_side][ROOK][rk_to]
            
        # 4. move the piece to landing
        self.bb[our_side][landing] ^= to_bb
        self.occ[our_side] ^= to_bb
        self.all_occ ^= to_bb
        self.piece_at[to_sq] = landing + our_side*6
        self.hash ^= H_PIECE[our_side][landing][to_sq]
        
        
        # 5. save history to revesve later
        castle_mask_before = pack_castle(
            self.white_king_castle, self.white_queen_castle,
            self.black_king_castle, self.black_queen_castle
        )
        
        last_move = HistoryEntry(
                encoded_move     = encoded_move,
                captured         = cap_piece,
                prev_ep          = self.en_passant,
                castle_mask      = castle_mask_before,
                prev_hash             = prev_hash
            )
        
        self.history.append(
            last_move
        )
        
        # 6. mark en passant and castling right
        if piece_code == PAWN and abs(to_sq - from_sq) == 16:
            self.en_passant = (from_sq + to_sq) // 2
        else:
            self.en_passant = None
            
        if last_move.prev_ep is not None:
            self.hash ^= H_EN_PASSANT[last_move.prev_ep & 7]
        if self.en_passant is not None:
            self.hash ^= H_EN_PASSANT[self.en_passant & 7]
            
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
                
        new_castle_mask = pack_castle(
            self.white_king_castle, self.white_queen_castle,
            self.black_king_castle, self.black_queen_castle
        )            
        change = castle_mask_before ^ new_castle_mask
        if change:
            if change & 1: self.hash ^= H_CASTLE[0]   # WK
            if change & 2: self.hash ^= H_CASTLE[1]   # WQ
            if change & 4: self.hash ^= H_CASTLE[2]   # BK
            if change & 8: self.hash ^= H_CASTLE[3]   # BQ
            
        # 7. flip the side
        self.side ^= 1  
        self.hash ^= H_BLACK_TO_MOVE

    def unpush(self):
        
        # 1. decode everything
        last_move: HistoryEntry = self.history.pop()
        from_sq, to_sq, flag = decode_move(last_move.encoded_move)
        moving_piece = self.piece_at[to_sq]           
        our_side    = moving_piece // 6
        other_side  = our_side ^ 1
        piece_code  = moving_piece % 6   
        
        self.hash = last_move.prev_hash
        
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
                flag = DOUBLE_PUSH
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
    
    
    def calculate_pawn_moves(self, sq, side = WHITE):
        moves = 0
        row, col = divmod(sq, 8)
        
        other_side_occ = self.occ[side^1]
        attack_mask = WHITE_PAWN_ATTACK_TABLE if side == WHITE else BLACK_PAWN_ATTACK_TABLE
        en_passant_rank = RANK_5 if side == WHITE else RANK_4
        start_rank = RANK_2 if side == WHITE else RANK_7
        
        # calculate the attack squares
        moves |= other_side_occ & attack_mask[sq]
        
        # double pawn push
        if (SQ_MASK[sq] & start_rank) and not (PAWN_DOUBLE_PUSH_TABLE[sq] & self.all_occ):
            moves |= SQ_MASK[sq + 16 - 32*side]
            
        # single pawn push
        if  0 < row < 7:
            if (1 << (row + 1 - 2*side)*8 + col) & ~self.all_occ:
                moves |= SQ_MASK[sq + 8 -16*side]
        
        # en passen
        if self.en_passant is not None:
            if en_passant_rank & SQ_MASK[sq]:
                if attack_mask[sq] & SQ_MASK[self.en_passant]:
                    if en_passant_rank & self.bb[side][KING]:
                        king_pos = self.bb[side][KING].bit_length() - 1 
                        rook_and_queen = self.bb[side^1][ROOK] | self.bb[side^1][QUEEN]
                        rook_same_rank = en_passant_rank & rook_and_queen
                        while rook_same_rank:
                            lsb = rook_same_rank & -rook_same_rank
                            rook_sq = lsb.bit_length() - 1
                            ray = ROOK_BETWEEN_MASK[rook_sq][king_pos] & self.all_occ
                            if ray & SQ_MASK[sq] and ray.bit_count() == 3:                            
                                return moves
                            rook_same_rank &= rook_same_rank - 1        
                    moves |= SQ_MASK[self.en_passant]
        return moves
    
    def get_check_score(self, move: int) -> bool:
        from_sq, to_sq, flag = decode_move(move)
        mover = self.piece_at[from_sq] % 6

        king_sq = (self.bb[self.side ^ 1][KING].bit_length() - 1)
        check_score = 0
        if mover == KNIGHT:
            if (KNIGHT_TABLE[to_sq] & (1 << king_sq)):
                check_score += CHECK_BONUS
        elif mover == BISHOP:
            if ((BISHOP_BETWEEN_MASK[to_sq][king_sq] & ~self.all_occ) == 0):
                check_score += CHECK_BONUS
        elif mover == ROOK:
            if ((ROOK_BETWEEN_MASK[to_sq][king_sq] & ~self.all_occ) == 0):
                check_score += CHECK_BONUS
        elif mover == QUEEN:
            diag = ((BISHOP_BETWEEN_MASK[to_sq][king_sq] & ~self.all_occ) == 0)
            ortho = ((ROOK_BETWEEN_MASK[to_sq][king_sq] & ~self.all_occ) == 0)
            if diag or ortho:
                check_score += CHECK_BONUS
        elif mover == PAWN:
            table = (WHITE_PAWN_ATTACK_TABLE if self.side == WHITE
                    else BLACK_PAWN_ATTACK_TABLE)
            if (table[to_sq] & (1 << king_sq)):
                check_score += CHECK_BONUS
        
        
        # check discover checks
        bits = self.bb[self.side][QUEEN] | self.bb[self.side][ROOK]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            if (ROOK_BETWEEN_MASK[sq][king_sq] & SQ_MASK[from_sq]) and not (ROOK_BETWEEN_MASK[sq][king_sq] & SQ_MASK[to_sq]):
                if ROOK_BETWEEN_MASK[sq][king_sq].bit_count() == 2:
                    check_score += CHECK_BONUS
                    
            bits &= bits - 1
            
        bits = self.bb[self.side][BISHOP] | self.bb[self.side][ROOK]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            if (BISHOP_BETWEEN_MASK[sq][king_sq] & SQ_MASK[from_sq]) and not (BISHOP_BETWEEN_MASK[sq][king_sq] & SQ_MASK[to_sq]):
                if BISHOP_BETWEEN_MASK[sq][king_sq].bit_count() == 2:
                    check_score += CHECK_BONUS
                    
            bits &= bits - 1
        
        return check_score
    
    

    
    def order_moves(self, moves):
        """
        prioritize making high potential piece first
        """
        scored = []
        for move in moves:
            score = 0
            from_sq, to_sq, flag = decode_move(move)
            
            moved_piece = self.piece_at[from_sq]
            captured_piece = self.piece_at[to_sq]

            # 1) prioritize capture with lower value piece
            if captured_piece != NO_PIECE:
                score = 10 * PIECE_VALUES[captured_piece] - PIECE_VALUES[moved_piece]

            # 2) prioritize promotion
            if flag & 8:
                score += PIECE_VALUES[(flag & 3) + 1]
                
            # 3) bonus for check
            score += self.get_check_score(move)

            # 4) penalize moving into an opponent‐pawn attack
            if SQ_MASK[to_sq] & self.pawn_attack_mask:
                score -= PIECE_VALUES[moved_piece]

            scored.append((score, move))

        # now sort descending by score and unpack
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mv for _, mv in scored]
    
    
    def tt_probe(self, depth: int, alpha: int, beta: int):
        ent = self.tt.get(self.hash)
        if ent and ent.depth >= depth:
            if ent.flag == EXACT:
                return ent.score, ent.move, True
            if ent.flag == LOWER and ent.score > alpha:
                alpha = ent.score
            elif ent.flag == UPPER and ent.score < beta:
                beta  = ent.score
            # cut-off
            if alpha >= beta:                        
                return ent.score, ent.move, True
        return alpha, beta, False
        
    def tt_store(self, depth, score, alpha0, beta, best_move):
        if   score <= alpha0:  flag = UPPER    
        elif score >= beta:    flag = LOWER    
        else:                  flag = EXACT     

        old = self.tt.get(self.hash)
        # keep the best information we have
        if old is None or depth >= old.depth or flag == EXACT:
            # deeper entry *or* an EXACT replacement
            self.tt[self.hash] = TTEntry(
                key   = self.hash,
                depth = depth,
                flag  = flag,
                score = score,
                move  = best_move,
            )
            
            
    def calculate_captured(self, alpha= -INF, beta= INF, depth = 5):                    
        alpha, beta, hit = self.tt_probe(depth, alpha, beta)
        if hit: return alpha
        # prune if it's no better
        score = self.evaluate()
        if score >= beta:
            return beta
        alpha = max(alpha, score)
        
        if depth == 0:
            return alpha
        
        
        capture_moves = [move for move in self.find_available_moves() if move & (1 << 14)]
        capture_moves = self.order_moves(capture_moves)
        # always get the maximize value with negamax  
        for move in capture_moves:
            self.push(move)
            score =  -self.calculate_captured(alpha = -beta, beta = -alpha, depth = depth - 1)
            self.unpush()
            alpha = max(score, alpha)
        
            if alpha >= beta:
                break    
            

        return alpha
    
        
    
    def negamax(self, alpha= -INF, beta= INF, depth = 2, ply = 0):
        """note that 1 for white and -1 for black"""
        
        alpha_start = alpha              
        alpha, beta, hit = self.tt_probe(depth, alpha, beta)
        if hit:
            return alpha
        
        
        moves = self.find_available_moves()
        
        # return score at leaf or when checkmated
        if not moves:
            if self.attacked_mask & self.bb[self.side][KING]:
                win = MATE - ply
                return -win
            return 0
        if depth == 0:
            return self.calculate_captured(alpha=alpha, beta=beta)
            # return self.evaluate()
        
        moves = self.order_moves(moves)
        
        # always get the maximize value with negamax 
        best_move = 0 
        for move in moves:
            self.push(move)
            score =  -self.negamax(alpha = -beta, beta = -alpha, depth=depth-1, ply = ply + 1)
            self.unpush()
            if score >= alpha:
                alpha, best_move = score, move
            if alpha >= beta:
                break    
            
        self.tt_store(depth, alpha, alpha_start, beta, best_move)
        return alpha
    
    @classmethod
    def load_opening_book(cls, path: str = "opening.json"):
        import json, pathlib
        # already loaded
        if cls.BOOK:              
            return
        p = pathlib.Path(path)
        if p.exists():
            with p.open() as fh:
                raw = json.load(fh)
            # keys were dumped as strings, convert back to int
            cls.BOOK = {int(k): v for k, v in raw.items()}
            print(f"[book] loaded {len(cls.BOOK):,} positions")
    
    @property
    def current_fen(self) -> str:
        piece_map = []
        for r in range(8):
            empty = 0
            row   = ""
            for c in range(8):
                sq = (7 - r) * 8 + c
                p  = self.piece_at[sq]
                if p == NO_PIECE:
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    sym = "PNBRQKpnbrqk"[p]
                    row += sym
            if empty:
                row += str(empty)
            piece_map.append(row)
        pieces  = "/".join(piece_map)
        side    = "w" if self.side == WHITE else "b"

        castles = "".join([
            "K" if self.white_king_castle  else "",
            "Q" if self.white_queen_castle else "",
            "k" if self.black_king_castle  else "",
            "q" if self.black_queen_castle else "",
        ]) or "-"

        ep = "-" if self.en_passant is None else "abcdefgh"[self.en_passant & 7] + str((self.en_passant >> 3)+1)

        return f"{pieces} {side} {castles} {ep} 0 1"
    
    def get_book_move(self) -> int | None:
        if not ChessLogic.BOOK:
            # lazy-load on first call
            ChessLogic.load_opening_book()   

        entries = ChessLogic.BOOK.get(self.hash)
        if not entries:
            return None                      
        
        return random.choice(entries)
    
    def get_best_move(self, depth= 3):
        move = self.get_book_move()
        if move is not None:
            return move            
        
        self.get_game_phase()
        moves = self.find_available_moves()
        if self.game_phase <= 3:
            depth += 3
        if self.game_phase == 0:
            depth += 3
        if not moves:
            print('what the fuck')
            return None
        alpha= -INF
        beta= INF
        
        ent = self.tt.get(self.hash)
        if ent and ent.depth >= depth and ent.flag == EXACT:
            return ent.move 
        
               
        best_score = -INF
        best_move = None
        moves = self.order_moves(moves)
        for move in moves:
            self.push(move)
            score = - self.negamax(alpha= -beta, beta= -alpha, depth=depth -1)
            self.unpush()
            if score > best_score:
                best_move = move
                best_score = score
                alpha = score
            if alpha >= beta:
                break
            
        self.tt[self.hash] = TTEntry(self.hash, depth, EXACT, alpha, best_move)
        return best_move

    def count_material(self, side = WHITE):
        material = 0
        material += self.bb[side][PAWN].bit_count()*PAWN_VALUE
        material += self.bb[side][KNIGHT].bit_count()*KNIGHT_VALUE
        material += self.bb[side][BISHOP].bit_count()*BISHOP_VALUE
        material += self.bb[side][ROOK].bit_count()*ROOK_VALUE
        material += self.bb[side][QUEEN].bit_count()*QUEEN_VALUE
        return material
    
    def calculate_bonus_point(self, side, game_phase):
        score = 0
        bits = self.occ[side]
        
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            
            # mirror only the rank for Black
            if side == BLACK:
                sq_mirror = sq ^ 56          
            else:
                sq_mirror = sq      
            
            piece = self.piece_at[sq] % 6
            if piece != KING:
                score += PIECE_TO_PST[piece][sq_mirror]
            else:
                score += PIECE_TO_PST[piece + game_phase][sq_mirror]
            
            bits &= bits - 1
                
        
        # calculate isolate/doubled pawn and half open rook
        own_pawns = self.bb[side][PAWN]
        opp_pawns = self.bb[side ^ 1][PAWN]

        own_pawn_files = [ (own_pawns & FILE_MASKS[f]).bit_count() for f in range(8) ]
        opp_pawn_files = [ (opp_pawns & FILE_MASKS[f]).bit_count() for f in range(8) ]

        isolated_cnt = 0
        doubled_cnt  = 0
        
        for f in range(8):
            cnt = own_pawn_files[f]
            if cnt:
                if cnt > 1:
                    doubled_cnt += cnt - 1
                left  = own_pawn_files[f - 1] if f > 0 else 0
                right = own_pawn_files[f + 1] if f < 7 else 0
                if left + right == 0:
                    isolated_cnt += cnt

        score -= doubled_cnt  * DOUBLED_PAWN_PENALTY
        score -= isolated_cnt * ISOLATED_PAWN_PENALTY

        own_rooks = self.bb[side][ROOK]
        bits = own_rooks
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            file_idx = sq & 7

            if own_pawn_files[file_idx] == 0:          
                if opp_pawn_files[file_idx] == 0:
                    score += ROOK_ON_OPEN_FILE_BONUS   
                else:
                    score += ROOK_ON_HALF_OPEN_FILE_BONUS

            bits &= bits - 1
            
        
            
        bits = own_pawns
        while bits:
            lsb = bits & -bits
            sq  = lsb.bit_length() - 1

            # rank from own side (0 = 2nd rank, 6 = 8th rank)
            rank = ((sq ^ 56) >> 3) if side == BLACK else (sq >> 3) - 1
            score += PAWN_ADVANCE[rank]                 # basic “further is better”

            col = sq & 7
            in_front = FILE_MASKS[col] & (
                (MASK64 << sq) if side == WHITE else (MASK64 >> (63 - sq))
            )
            if not (in_front & opp_pawns):              # true passed pawn
                score += PASSED_BONUS + PAWN_ADVANCE[rank]

            bits &= bits - 1

        
        return score
    
    
    
    
    def get_game_phase(self):
        self.game_phase = 0
        our_side = self.side
        other_side = self.side^1
        
        one_value = self.bb[our_side][KNIGHT] | self.bb[other_side][KNIGHT] | self.bb[our_side][BISHOP] | self.bb[other_side][BISHOP]
        two_value = self.bb[our_side][ROOK] | self.bb[other_side][ROOK]
        four_value = self.bb[our_side][QUEEN] | self.bb[other_side][QUEEN]
        
        self.game_phase = (one_value.bit_count() + two_value.bit_count()*2 + four_value.bit_count()*4)
    
    def checkmate_attemp(self):
        if self.game_phase >= 8:
            return 0
        score = 0
        phase_scale = 24 - self.game_phase      
        king_bonus  = 2 * phase_scale           
        # --- Opponent‐king vs centre ---
        our_king_sq = self.bb[self.side][KING].bit_length() - 1
        other_king_sq = self.bb[self.side^1][KING].bit_length() - 1
        our_row, our_col = divmod(our_king_sq, 8)
        other_row, other_col = divmod(other_king_sq, 8)

        # distance from centre file: max distance to either wall of the central two files (3,4)
        opponent_dst_file = max(3 - other_col, other_col - 4)
        # distance from centre rank
        opponent_dst_rank = max(3 - other_row, other_row - 4)

        # total “how far from centre” score
        score = king_bonus * (opponent_dst_file + opponent_dst_rank)


        # file and rank distance between kings
        dst_between_file = abs(our_col - other_col)
        dst_between_rank = abs(our_row - other_row)

        # encourage our king to close in
        approach = (14 - (dst_between_file + dst_between_rank))//2
        score += king_bonus * approach // 4     

        # scale and weight, then return as integer
        return score
    
    def evaluate(self):
        self.get_game_phase()
        our_score = self.count_material(self.side) 
        other_score = self.count_material(self.side^1)  
        
        score = our_score - other_score
        if self.game_phase <= 8:
            game_phase = END_GAME
        else:
            game_phase = MIDDLE_GAME
        bonus = self.calculate_bonus_point(self.side, game_phase) - self.calculate_bonus_point(self.side^1, game_phase)
        score+= bonus
        score += self.checkmate_attemp()
        
        return score 
    
    def find_available_moves(self):
        our_side = self.side
        other_side = our_side ^ 1
        self.attacked_mask = 0
        self.pawn_attack_mask = 0
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
            self.attacked_mask |= knight_movable
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
                    
            relevant_occ = BISHOP_RELEVANT_MASK[sq] & (self.all_occ & ~self.bb[our_side][KING])
            magic_index = get_magic_index(relevant_occ, BISHOP_MAGIC[sq], BISHOP_RELEVEANT_BITS[sq])
            bishop_movable = BISHOP_TABLE[sq][magic_index]
            
            self.attacked_mask |= bishop_movable        
            
            bits &= bits - 1
            

        # Opponent Pawns
        bits = self.bb[other_side][PAWN]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            _pawn_attack_mask = BLACK_PAWN_ATTACK_TABLE[sq] if our_side == WHITE else WHITE_PAWN_ATTACK_TABLE[sq]
            _pawn_mask = _pawn_attack_mask & self.bb[our_side][KING]
            if _pawn_mask:
                checked += 1
                checked_mask = 1 << sq
            self.attacked_mask |= _pawn_attack_mask
            self.pawn_attack_mask |= _pawn_attack_mask
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
                    
            relevant_occ = ROOK_RELEVANT_MASK[sq] & (self.all_occ & ~self.bb[our_side][KING])
            magic_index = get_magic_index(relevant_occ, ROOK_MAGIC[sq], ROOK_RELEVEANT_BITS[sq])
            rook_movable = ROOK_TABLE[sq][magic_index]
            self.attacked_mask |= rook_movable
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
            
            
 
            relevant_rook_occ = ROOK_RELEVANT_MASK[sq] & (self.all_occ & ~self.bb[our_side][KING])
            rook_magic_index = get_magic_index(relevant_rook_occ, ROOK_MAGIC[sq], ROOK_RELEVEANT_BITS[sq])
            rook_moves = ROOK_TABLE[sq][rook_magic_index]

            relevant_bishop_occ = BISHOP_RELEVANT_MASK[sq]  & (self.all_occ & ~self.bb[our_side][KING])
            bishop_magic_index = get_magic_index(relevant_bishop_occ, BISHOP_MAGIC[sq], BISHOP_RELEVEANT_BITS[sq])
            bishop_moves = BISHOP_TABLE[sq][bishop_magic_index]

            queen_movable = rook_moves | bishop_moves
            self.attacked_mask |= queen_movable
            
            bits &= bits - 1
            
        
        # Black King
        bits = self.bb[other_side][KING]
        while bits:
            lsb = bits & -bits
            sq = lsb.bit_length() - 1
            king_movable = self.calculate_king_moves(sq, 0b0, self.all_occ, 0b0, other_side)
            self.attacked_mask |= king_movable
            bits &= bits - 1
        
        # start to find legal moves for our side
        # King
        bits = self.bb[our_side][KING]
        while bits:
            lsb = bits & -bits
            i = lsb.bit_length() - 1
            king_movable = self.calculate_king_moves(i, self.occ[our_side], self.all_occ, self.attacked_mask, self.side)
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
                pawn_movable = self.calculate_pawn_moves(i, self.side)
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
    result = logic.get_best_move(depth=3)
    print(bin(result[0]), result[1])
        

