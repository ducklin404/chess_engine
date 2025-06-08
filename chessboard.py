import pygame
from pygame import Surface
from chess_logic import *


chess = ChessLogic()

# --- Config and Constants ---
CELL_SIZE = 100
LABEL_OFFSET = 0.85
BOARD_SIZE = CELL_SIZE * 8
DARK = (118, 150,  86)
LIGHT = (238, 238, 210)
hovered_color = (144, 238, 144, 128)
start_square_color = (120, 200, 100, 128)
movable_color = (120, 200, 144, 100)
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

PIECE_TO_INDEX = {
            'wp': 0, 'wn': 1, 'wb': 2, 'wr': 3, 'wq': 4, 'wk': 5,
            'bp': 6, 'bn': 7, 'bb': 8, 'br': 9, 'bq': 10, 'bk': 11
        }


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
            
def draw_hovered(surface, cell_size, x, y):
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(hovered_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    
def draw_start_square(surface, cell_size, x, y):
    hovered_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    hovered_surface.fill(start_square_color)
    surface.blit(hovered_surface, (x * cell_size , y * cell_size))
    


def draw_can_move_square(surface, cell_size, x, y):
    RADIUS = int(cell_size*0.15)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def draw_can_capture_square(surface, cell_size, x, y):
    RADIUS = int(cell_size*0.5)
    centre = (cell_size // 2, cell_size // 2)
    circle_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
    pygame.draw.circle(circle_surf, movable_color, centre, RADIUS)
    pygame.draw.circle(circle_surf, (0, 0, 0, 0), centre, RADIUS*0.8)
    surface.blit(circle_surf, (x * cell_size , y * cell_size))

def show_promotion_options(surface, cell_size, col, side ='white'):
    images = load_piece_images(CELL_SIZE * 0.8)
    image_offset = cell_size * 0.1
    mask = pygame.Surface((cell_size * 8, cell_size*8), pygame.SRCALPHA)
    mask.fill((0,0,0,200))
    promotion_list = pygame.Surface((cell_size, cell_size*4), pygame.SRCALPHA)
    RADIUS = int(cell_size*0.5)
    if side =='white':
        queen = 'wq'
        rook ='wr'
        knight = 'wn'
        bishop = 'wb'
    else:
        queen = 'bq'
        rook = 'br'
        knight = 'bn'
        bishop = 'bb'
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size // 2), RADIUS)
    promotion_list.blit(images[queen], (0 * cell_size + image_offset, image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size + cell_size // 2), RADIUS)
    promotion_list.blit(images[rook], (0 * cell_size + image_offset, cell_size + image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size*2 + cell_size // 2), RADIUS)
    promotion_list.blit(images[knight], (0 * cell_size + image_offset, 2 * cell_size + image_offset))
    pygame.draw.circle(promotion_list, (120, 200, 144, 200), (cell_size // 2, cell_size*3 + cell_size // 2), RADIUS)
    promotion_list.blit(images[bishop], (0 * cell_size + image_offset, 3 * cell_size + image_offset))
    surface.blit(mask, (0,0))
    surface.blit(promotion_list, (cell_size * col , 0))

def bit_indices(n: int):
    """Yield positions of set bits, least-significant bit = position 0."""
    idx = 0
    while n:
        if n & 1:          # check LSB
            yield idx
        n >>= 1            # drop LSB
        idx += 1

def draw_movable_squares(surface, board, cell_size, moves):
    for i in bit_indices(moves):
        row, col = divmod(i, 8)
        if board[7-row][col] == '--':
            draw_can_move_square(surface, cell_size, col, 7-row)
        else:
            draw_can_capture_square(surface, cell_size, col, 7-row)
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
    board_state = INITIAL_POSITION
    promotion = None
    dragging = False
    dragging_piece = None
    moves = chess.find_available_moves()
    print(moves)
    drag_start = (None, None)

    # Prepare the board surface
    board = Surface((BOARD_SIZE, BOARD_SIZE))
    board.fill((255, 255, 255))
    draw_board(board, CELL_SIZE)
    draw_labels(board, font, side, CELL_SIZE, LABEL_OFFSET)
    draw_pieces(board, INITIAL_POSITION, piece_images, side, CELL_SIZE)

    # Main loop
    while running:
        board.fill((255, 255, 255))
        draw_board(board, CELL_SIZE)
        draw_labels(board, font, 'white', CELL_SIZE, LABEL_OFFSET)
        draw_pieces(board, board_state, piece_images, 'white', CELL_SIZE)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if promotion is not None:
                    pass
                else:
                    mx, my = pygame.mouse.get_pos()
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    if row < 0 or row > 7 or col < 0 or col > 7:
                        continue
                    if board_state[row][col] == '--':
                        continue
                    if not moves[(7-row)*8 + col]:
                        continue
                    
                    dragging_piece = board_state[row][col]
                    # board_state[row][col] = '--'
                    dragging = True
                    drag_start = (row, col)
                
            elif event.type == pygame.MOUSEBUTTONUP:
                if promotion is not None:
                    mx, my = pygame.mouse.get_pos()
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    row_promo, col_prommo = divmod(promotion, 8)
                    promote_piece = None
                    
                    if col == col_prommo:
                        if row == 0:
                            promote_piece = 'wq' if side == 'white' else 'bq'
                        elif row == 1:
                            promote_piece = 'wr' if side == 'white' else 'br'
                        elif row == 2:
                            promote_piece = 'wn' if side == 'white' else 'bn'
                        elif row == 3:
                            promote_piece = 'wb'if side == 'white' else 'bb'
                        
                        if promote_piece is not None:
                           
                            board_state[7-row_promo][col_prommo] = promote_piece
                            
                            board_state[drag_start[0]][drag_start[1]] = '--'
                            
                            chess.push((7-drag_start[0])*8 + drag_start[1], (row_promo)*8 + col_prommo, PIECE_TO_INDEX[dragging_piece], captured, is_en_passant=is_en_passant, promote=PIECE_TO_INDEX[promote_piece])
                            captured = None
                            promotion = None
                            drag_start = (None, None)
                            dragging_piece = None
                            side = 'white' if side == 'black' else 'black'
                            moves = chess.find_available_moves()

                elif dragging:
                    is_en_passant = False
                    mx, my = pygame.mouse.get_pos()
                    dragging = False
                    row = (my // CELL_SIZE)
                    col = (mx // CELL_SIZE)
                    if 0 <= row <= 7 and 0 <= col <= 7:
                        if (1 << (7-row) * 8 + col) & moves[(7-drag_start[0])*8 + drag_start[1]]:
                            if board_state[row][col] != '--':
                                captured = PIECE_TO_INDEX[board_state[row][col]]
                            else:
                                captured = None
                            if row == 0 and dragging_piece in ('wp', 'bp'):
                                promotion = (7-row)*8 + col
                                
                            if not promotion:
                            
                                
                                # check for en passant
                                if dragging_piece == 'wp' and drag_start[0] == 3:
                                    if col != drag_start[1]:
                                        if board_state[row][col] == '--':
                                            is_en_passant = True
                                            board_state[3][col]  = '--'
                                elif dragging_piece == 'bp' and drag_start[0] == 4:
                                    if col != drag_start[1]:
                                        if board_state[row][col] == '--':
                                            is_en_passant = True
                                            board_state[4][col]  = '--'
                                            
                                board_state[row][col] = dragging_piece
                                board_state[drag_start[0]][drag_start[1]] = '--'
                                chess.push((7-drag_start[0])*8 + drag_start[1], (7-row)*8 + col, PIECE_TO_INDEX[dragging_piece], captured, is_en_passant=is_en_passant)
                                if dragging_piece == 'wk' and drag_start[1] == 4 and col == 6:
                                    board_state[7][7] = '--'
                                    board_state[7][5] = 'wr'
                                elif dragging_piece == 'wk' and drag_start[1] == 4 and col == 2:
                                    board_state[7][0] = '--'
                                    board_state[7][3] = 'wr'
                                elif dragging_piece == 'bk' and drag_start[1] == 4 and col == 6:
                                    board_state[0][7] = '--'
                                    board_state[0][5] = 'br'
                                elif dragging_piece == 'bk' and drag_start[1] == 4 and col == 2:
                                    board_state[0][0] = '--'
                                    board_state[0][3] = 'br'
                                if side == 'white':
                                    side = 'black'
                                else:
                                    side = 'white'
                        
                            
                                
                                moves = chess.find_available_moves()
                            
                        else:
                            board_state[drag_start[0]][drag_start[1]] = dragging_piece
                    else:
                        board_state[drag_start[0]][drag_start[1]] = dragging_piece
                    if not promotion:
                        drag_start = (None, None)
                        dragging_piece = None

        if promotion is not None:
            row, col = divmod(promotion, 8)
            show_promotion_options(board, CELL_SIZE, col)

        
        if dragging:
            mx, my = pygame.mouse.get_pos()
            row = (my // CELL_SIZE)
            col = (mx // CELL_SIZE)
            draw_movable_squares(board, board_state,CELL_SIZE, moves[(7-drag_start[0])*8 + drag_start[1]])
            draw_start_square(board, CELL_SIZE, drag_start[1], drag_start[0])
            if 0 <= row <= 7 and 0 <= col <= 7:
                if (1 << (7-row)*8 + col) & (moves[(7-drag_start[0])*8 + drag_start[1]]):
                    draw_hovered(board, CELL_SIZE, col, row)
            board.blit(piece_images[dragging_piece], (mx - piece_images[dragging_piece].get_width() // 2, my - piece_images[dragging_piece].get_height() // 2))
                
        screen.blit(board, board.get_rect())
                    
        pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main()
