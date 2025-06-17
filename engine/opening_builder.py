#
import json, random, sys, pathlib
import chess.pgn           
from engine.chess_logic import ChessLogic   
from engine.move import encode_move

def san_to_engine_move(position: ChessLogic, san: str) -> int | None:
    """
    Convert SAN coming from python-chess into engine's encoded move.
    """
    board = chess.Board()                  
    # Use the current FEN to sync python-chess with our position
    board.set_fen(position.current_fen)
    try:
        ch_move = board.parse_san(san)
    except ValueError:
        return None

    from_sq  = ch_move.from_square
    to_sq    = ch_move.to_square
    promo    = None
    if ch_move.promotion is not None:      
        promo = { chess.KNIGHT: 1, chess.BISHOP: 2,
                  chess.ROOK: 3,  chess.QUEEN: 4 }[ch_move.promotion]

    flag = position.get_flag(from_sq, to_sq, promo)
    return encode_move(from_sq=from_sq, to_sq=to_sq, flag=flag)



def build_book(in_pgn: str, out_json: str):
    logic   = ChessLogic()
    book: dict[str, list[int]] = {}   

    with open(in_pgn, "r", encoding="latin-1") as fh:
        while (game := chess.pgn.read_game(fh)) is not None:
            logic.restart()
            for node in game.mainline():
                san  = node.san()
                move = san_to_engine_move(logic, san)
                if move is None:         
                    break

                key = str(logic.hash)
                book.setdefault(key, []).append(move)
                logic.push(move)

    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(book, fh)

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "eco.pgn"
    dst = sys.argv[2] if len(sys.argv) > 2 else "opening.json"
    build_book(src, dst)
    with open(dst) as fh:
        data = json.load(fh)

    num_positions = len(data)                      
    num_moves     = sum(len(m) for m in data.values())  

    print(f"Built {dst} with "
          f"{num_positions:,} positions and {num_moves:,} moves.")