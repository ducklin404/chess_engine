# Chess Engine

This repository contains a Python chess engine with a simple Pygame interface. The engine uses bitboards and magic move generation for fast search. An opening book built from `eco.pgn` is included.

## Features

- **Bitboard representation** with precomputed attack tables using magic bitboards.
- **Negamax search** with alpha--beta pruning and a transposition table.
- **Piece-square tables** and material evaluation.
- **Pygame GUI** for playing against the engine.
- **Opening book** generation script using `python-chess`.

## Installation

Install the requirements using pip:

```bash
pip install -r requirements.txt
```

`requirements.txt` only lists two packages:

```text
pygame
python-chess
```

## Running the Game

Start the graphical interface with:

```bash
python play.py
```

You can choose your side and tweak UI constants in [`ui/config.py`](ui/config.py):

```python
init_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# CHoose your side here
# side = 'black'
side = 'white'
```

## Opening Book

The script [`engine/opening_builder.py`](engine/opening_builder.py) converts a PGN file into the JSON format used by the engine:

```bash
python engine/opening_builder.py [input.pgn] [output.json]
```

The default PGN is `eco.pgn` and the resulting file is `opening.json`.

## Technical Overview

The core engine lives in the [`engine/`](engine/) directory. Important parts include:

- `chess_logic.py` – board state, move generation and the search loop.
- `attack_tables.py` – precomputes attack masks and loads magic tables.
- `magic.py` – generates or loads magic move tables.
- `move.py` – compact move encoding utilities.

Below is a small excerpt from `get_best_move` to illustrate the search structure:

```python
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
```

Magic tables are loaded or generated automatically:

```python
    with open(MAGIC_FILENAME, 'rb') as f:
        data = pickle.load(f)
    print("Loaded magic tables from file.")
    ...
    data = generate_and_save_tables()
    print("Saved magic tables to file.")
```

## Assets

The `pieces/` directory contains PNG images for the GUI. Board dimensions and colours are defined in `ui/config.py`.