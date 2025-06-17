"""Configuration values for the UI and default board setup."""

init_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# CHoose your side here
# side = 'black'
side = 'white'

# --- Config and Constants ---
CELL_SIZE = 100
LABEL_OFFSET = 0.88
BOARD_SIZE = CELL_SIZE * 8
DARK = (118, 150,  86)
LIGHT = (238, 238, 210)
hovered_color = (144, 238, 144, 128)
start_square_color = (120, 200, 100, 128)
movable_color = (120, 200, 144, 100)
LETTERS = 'abcdefgh'
PIECES = ['wp', 'bp', 'wn', 'bn', 'wb', 'bb', 'wr', 'br', 'wq', 'bq', 'wk', 'bk']
END_SCENE_COLOR = (40,40,40) 
TEXT_COLOR = (152, 255, 152)