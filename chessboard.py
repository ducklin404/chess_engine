import pygame
from pygame import Surface

# --- Config and Constants ---
CELL_SIZE = 100
LABEL_OFFSET = 0.85
BOARD_SIZE = CELL_SIZE * 8
DARK = (118, 150,  86)
LIGHT = (238, 238, 210)
LETTERS = 'abcdefgh'
PIECES = ['wp', 'bp', 'wn', 'bn', 'wb', 'bb', 'wr', 'br', 'wq', 'bq', 'wk', 'bk']
INITIAL_POSITION = [
    ["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"],
    ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["--", "--", "--", "--", "--", "--", "--", "--"],
    ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
    ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]
]


def load_piece_images(cell_size):
    piece_images = {}
    for piece in PIECES:
        img = pygame.image.load(f'pieces/{piece}.png')
        piece_images[piece] = pygame.transform.scale(img, (cell_size, cell_size))
    return piece_images

def draw_board(surface, cell_size):
    for x in range(8):
        for y in range(8):
            color = LIGHT if (x + y) % 2 == 0 else DARK
            pygame.draw.rect(surface, color, (x * cell_size, y * cell_size, cell_size, cell_size))

def draw_labels(surface, font, side, cell_size, label_offset):
    for i in range(8):
        file_color = DARK if i % 2 == 0 else LIGHT
        rank_color = LIGHT if file_color == DARK else DARK

        # File labels (a-h)
        text = font.render(LETTERS[i] if side == 'white' else LETTERS[7-i], True, rank_color)
        x = i * cell_size + int(cell_size * label_offset) - text.get_width() // 2
        y = BOARD_SIZE - text.get_height()
        surface.blit(text, (x, y))

        # Rank labels (1-8)
        rank = str(8 - i) if side == 'white' else str(i + 1)
        text = font.render(rank, True, file_color)
        x = text.get_width() // 2
        y = i * cell_size + int(cell_size * (1-label_offset)) - text.get_height() // 2
        surface.blit(text, (x, y))

def draw_pieces(surface, board_pos, images, side, cell_size):
    for i in range(8):
        for j in range(8):
            if side == 'white':
                piece = board_pos[i][j]
                y, x = i, j
            else:
                piece = board_pos[7-i][j]
                y, x = i, j
            if piece != '--':
                surface.blit(images[piece], (x * cell_size, y * cell_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("chess engine hehehe")
    font = pygame.font.SysFont(None, 24, bold=True)
    piece_images = load_piece_images(CELL_SIZE)
    side = 'white'  # or 'black'
    running = True

    # Prepare the board surface
    board = Surface((BOARD_SIZE, BOARD_SIZE))
    board.fill((255, 255, 255))
    draw_board(board, CELL_SIZE)
    draw_labels(board, font, side, CELL_SIZE, LABEL_OFFSET)
    draw_pieces(board, INITIAL_POSITION, piece_images, side, CELL_SIZE)

    # Main loop
    while running:
        screen.blit(board, board.get_rect())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
